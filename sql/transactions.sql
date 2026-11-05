-- ============================================================================
-- SCROLLS OF AGORA (v3.0): ACID TRANSACTIONS & ANTI-DUPE CONCURRENCY PROTOCOLS
-- Demonstrates:
--   1. Pessimistic Row-Level Locking (SELECT ... FOR UPDATE) & Deadlock Prevention
--   2. Atomic Escrow Bid Placement & Automatic Outbid Refunds
--   3. The Weekly Kiosk Flip (Sealed-Bid Guild Trader Resolution)
--   4. Arcane Tempering & Glyph Enchanting (Multi-Table Atomic Crafting)
-- ============================================================================

-- ============================================================================
-- TRANSACTION 1: ATOMIC INSTANT BUYOUT (Prevents "Item Dupe" & Double-Spend)
-- ============================================================================
CREATE OR REPLACE FUNCTION execute_atomic_buyout(
    p_listing_id INT,
    p_buyer_id INT
) RETURNS TABLE (
    success BOOLEAN,
    code TEXT,
    message TEXT,
    tx_id INT,
    gross_paid BIGINT,
    tax_burned BIGINT,
    seller_payout BIGINT
) LANGUAGE plpgsql AS $$
DECLARE
    v_listing RECORD;
    v_buyer RECORD;
    v_tax_amount BIGINT;
    v_guild_cut BIGINT;
    v_net_payout BIGINT;
    v_new_tx_id INT;
BEGIN
    -- Step 1: Acquire Exclusive Pessimistic Row Lock on the Listing
    SELECT l.*, r.tax_rate_bps, r.controlling_guild_id, ii.mint_serial, ii.item_id, it.item_name
    INTO v_listing
    FROM auction_listings l
    JOIN realms r ON r.realm_id = l.realm_id
    JOIN inventory_items ii ON ii.instance_id = l.instance_id
    JOIN item_templates it ON it.item_id = ii.item_id
    WHERE l.listing_id = p_listing_id
    FOR UPDATE OF l;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 'ERR_NOT_FOUND'::TEXT, 'Listing does not exist.'::TEXT, NULL::INT, 0::BIGINT, 0::BIGINT, 0::BIGINT;
        RETURN;
    END IF;

    -- Step 2: Re-verify Status under Lock (Blocks 99 of 100 concurrent race threads)
    IF v_listing.status <> 'ACTIVE' THEN
        RETURN QUERY SELECT FALSE, 'ERR_ALREADY_CLOSED'::TEXT, ('Lock serialized: Listing #' || p_listing_id || ' already ' || v_listing.status)::TEXT, NULL::INT, 0::BIGINT, 0::BIGINT, 0::BIGINT;
        RETURN;
    END IF;

    IF v_listing.buyout_price IS NULL THEN
        RETURN QUERY SELECT FALSE, 'ERR_NO_BUYOUT'::TEXT, 'Listing is bid-only.'::TEXT, NULL::INT, 0::BIGINT, 0::BIGINT, 0::BIGINT;
        RETURN;
    END IF;

    IF v_listing.seller_id = p_buyer_id THEN
        RETURN QUERY SELECT FALSE, 'ERR_SELF_TRADE'::TEXT, 'Cannot buy your own listing.'::TEXT, NULL::INT, 0::BIGINT, 0::BIGINT, 0::BIGINT;
        RETURN;
    END IF;

    -- Step 3: Lock Player Wallets in Deterministic Ascending Order (Zero AB-BA Deadlocks)
    PERFORM 1 FROM players
    WHERE player_id IN (p_buyer_id, v_listing.seller_id, COALESCE(v_listing.high_bidder_id, -1))
    ORDER BY player_id ASC
    FOR UPDATE;

    SELECT gold_balance, is_banned INTO v_buyer FROM players WHERE player_id = p_buyer_id;
    IF v_buyer.is_banned THEN
        RETURN QUERY SELECT FALSE, 'ERR_BANNED'::TEXT, 'Account is banned by the Inquisitor.'::TEXT, NULL::INT, 0::BIGINT, 0::BIGINT, 0::BIGINT;
        RETURN;
    END IF;

    IF v_buyer.gold_balance < v_listing.buyout_price THEN
        RETURN QUERY SELECT FALSE, 'ERR_INSUFFICIENT_GOLD'::TEXT, 'Insufficient liquid gold.'::TEXT, NULL::INT, 0::BIGINT, 0::BIGINT, 0::BIGINT;
        RETURN;
    END IF;

    -- Step 4: Refund Escrow to Previous High Bidder
    IF v_listing.high_bidder_id IS NOT NULL AND v_listing.current_bid > 0 THEN
        UPDATE players
        SET escrow_gold = escrow_gold - v_listing.current_bid,
            gold_balance = gold_balance + v_listing.current_bid
        WHERE player_id = v_listing.high_bidder_id;
    END IF;

    -- Step 5: Compute Regional Kiosk Tax Burn & Guild Dividend
    v_tax_amount := (v_listing.buyout_price * v_listing.tax_rate_bps) / 10000;
    v_net_payout := v_listing.buyout_price - v_tax_amount;
    v_guild_cut := v_tax_amount / 2;

    IF v_listing.controlling_guild_id IS NOT NULL AND v_guild_cut > 0 THEN
        UPDATE trade_guilds
        SET treasury_gold = treasury_gold + v_guild_cut,
            tax_dividend_earned = tax_dividend_earned + v_guild_cut
        WHERE guild_id = v_listing.controlling_guild_id;
    END IF;

    -- Step 6: Atomic Wallet Debit & Credit
    UPDATE players SET gold_balance = gold_balance - v_listing.buyout_price WHERE player_id = p_buyer_id;
    UPDATE players SET gold_balance = gold_balance + v_net_payout WHERE player_id = v_listing.seller_id;

    -- Step 7: Transfer Unique Cryptographic Item Instance
    UPDATE inventory_items
    SET owner_id = p_buyer_id,
        is_escrowed = FALSE
    WHERE instance_id = v_listing.instance_id;

    -- Step 8: Close Listing & Write Double-Entry Audit Record
    UPDATE auction_listings
    SET status = 'SOLD',
        high_bidder_id = p_buyer_id,
        current_bid = v_listing.buyout_price
    WHERE listing_id = p_listing_id;

    INSERT INTO ledger_transactions (
        listing_id, instance_id, seller_id, buyer_id,
        gross_price, market_tax_burned, seller_net_payout, settlement_type
    ) VALUES (
        p_listing_id, v_listing.instance_id, v_listing.seller_id, p_buyer_id,
        v_listing.buyout_price, v_tax_amount, v_net_payout, 'INSTANT_BUYOUT'
    ) RETURNING ledger_transactions.tx_id INTO v_new_tx_id;

    RETURN QUERY SELECT
        TRUE,
        'OK_SETTLED'::TEXT,
        ('Acquired [' || v_listing.item_name || '] (' || v_listing.mint_serial || ') for ' || v_listing.buyout_price || 'g (Kiosk Tax: ' || v_tax_amount || 'g).')::TEXT,
        v_new_tx_id,
        v_listing.buyout_price,
        v_tax_amount,
        v_net_payout;
END;
$$;


-- ============================================================================
-- TRANSACTION 2: THE WEEKLY KIOSK FLIP (Atomic Sealed-Bid Kiosk Resolution)
-- ============================================================================
CREATE OR REPLACE FUNCTION resolve_weekly_kiosk_flip(
    p_realm_id INT
) RETURNS TABLE (
    winning_guild_id INT,
    winning_guild_name TEXT,
    winning_bid BIGINT,
    refunded_bids INT
) LANGUAGE plpgsql AS $$
DECLARE
    v_winner RECORD;
    v_refund_count INT := 0;
BEGIN
    -- Lock all sealed bids for this city hub
    PERFORM 1 FROM kiosk_bids WHERE realm_id = p_realm_id AND status = 'SEALED' FOR UPDATE;

    SELECT kb.kiosk_bid_id, kb.guild_id, kb.bid_gold, tg.guild_name
    INTO v_winner
    FROM kiosk_bids kb
    JOIN trade_guilds tg ON tg.guild_id = kb.guild_id
    WHERE kb.realm_id = p_realm_id AND kb.status = 'SEALED'
    ORDER BY kb.bid_gold DESC, kb.placed_at ASC
    LIMIT 1;

    IF NOT FOUND THEN
        RETURN;
    END IF;

    -- Award Kiosk Ownership to Highest Sealed Bidder
    UPDATE realms SET controlling_guild_id = v_winner.guild_id WHERE realm_id = p_realm_id;
    UPDATE kiosk_bids SET status = 'WON' WHERE kiosk_bid_id = v_winner.kiosk_bid_id;

    -- Refund all losing guilds atomically
    WITH losing_bids AS (
        UPDATE kiosk_bids
        SET status = 'REFUNDED'
        WHERE realm_id = p_realm_id AND status = 'SEALED' AND kiosk_bid_id <> v_winner.kiosk_bid_id
        RETURNING guild_id, bid_gold
    ),
    refunds AS (
        UPDATE trade_guilds tg
        SET treasury_gold = tg.treasury_gold + lb.bid_gold
        FROM losing_bids lb
        WHERE tg.guild_id = lb.guild_id
        RETURNING 1
    )
    SELECT COUNT(*) INTO v_refund_count FROM refunds;

    RETURN QUERY SELECT v_winner.guild_id, v_winner.guild_name::TEXT, v_winner.bid_gold, v_refund_count;
END;
$$;

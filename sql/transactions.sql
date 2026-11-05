-- ============================================================================
-- SCROLLS OF AGORA: ACID TRANSACTIONS & ANTI-DUPE CONCURRENCY PROTOCOLS
-- Demonstrates Pessimistic Row-Level Locking (SELECT ... FOR UPDATE),
-- Deadlock-Free Deterministic Lock Ordering, and Escrow Settlement
-- ============================================================================

-- ============================================================================
-- TRANSACTION 1: ATOMIC INSTANT BUYOUT (Prevents "Item Dupe" & Double-Spend)
-- ============================================================================
-- Why naive SQL fails under concurrency:
--   If 100 threads simultaneously execute `SELECT status FROM auction_listings WHERE listing_id = 101`
--   without row-level locking under READ COMMITTED, all 100 see status = 'ACTIVE' before any thread
--   commits, resulting in 100 item transfers or negative gold balances.
--
-- How Scrolls of Agora solves it:
--   1. `SELECT ... FOR UPDATE` on `auction_listings` serializes concurrent buyers at the row lock.
--   2. The first transaction to acquire the lock transitions `status` -> 'SOLD'.
--   3. All 99 waiting transactions wake up after commit, re-read the updated row, see `status = 'SOLD'`,
--      and cleanly abort without duplicating the item or corrupting player wallets.
--   4. Player rows (buyer, seller, previous high bidder) are locked in ascending `player_id` order
--      to guarantee freedom from AB-BA deadlocks.

CREATE OR REPLACE FUNCTION execute_atomic_buyout(
    p_listing_id INT,
    p_buyer_id INT
) RETURNS TABLE (
    success BOOLEAN,
    message TEXT,
    tx_id INT,
    gross_paid BIGINT,
    tax_burned BIGINT,
    seller_payout BIGINT
) LANGUAGE plpgsql AS $$
DECLARE
    v_listing RECORD;
    v_tax_bps INT;
    v_buyer_gold BIGINT;
    v_tax_amount BIGINT;
    v_net_payout BIGINT;
    v_new_tx_id INT;
BEGIN
    -- Step 1: Acquire Pessimistic Row Lock on the Auction Listing
    SELECT l.*, r.tax_rate_bps
    INTO v_listing
    FROM auction_listings l
    JOIN realms r ON r.realm_id = l.realm_id
    WHERE l.listing_id = p_listing_id
    FOR UPDATE OF l;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 'ERR_NOT_FOUND: Listing does not exist.', NULL::INT, 0::BIGINT, 0::BIGINT, 0::BIGINT;
        RETURN;
    END IF;

    -- Step 2: Verify Listing State (Blocks 99.9% of concurrent race-condition threads after lock release)
    IF v_listing.status <> 'ACTIVE' THEN
        RETURN QUERY SELECT FALSE, 'ERR_ALREADY_CLOSED: Listing is already ' || v_listing.status, NULL::INT, 0::BIGINT, 0::BIGINT, 0::BIGINT;
        RETURN;
    END IF;

    IF v_listing.buyout_price IS NULL THEN
        RETURN QUERY SELECT FALSE, 'ERR_NO_BUYOUT: Listing is bid-only.', NULL::INT, 0::BIGINT, 0::BIGINT, 0::BIGINT;
        RETURN;
    END IF;

    IF v_listing.seller_id = p_buyer_id THEN
        RETURN QUERY SELECT FALSE, 'ERR_SELF_TRADE: Seller cannot buyout own listing.', NULL::INT, 0::BIGINT, 0::BIGINT, 0::BIGINT;
        RETURN;
    END IF;

    -- Step 3: Lock Player Wallets in Deterministic Order (Ascending player_id prevents AB-BA Deadlocks)
    PERFORM 1 FROM players
    WHERE player_id IN (p_buyer_id, v_listing.seller_id, COALESCE(v_listing.high_bidder_id, -1))
    ORDER BY player_id ASC
    FOR UPDATE;

    -- Step 4: Verify Buyer Solvency
    SELECT gold_balance INTO v_buyer_gold FROM players WHERE player_id = p_buyer_id;
    IF v_buyer_gold < v_listing.buyout_price THEN
        RETURN QUERY SELECT FALSE, 'ERR_INSUFFICIENT_GOLD: Buyer lacks sufficient gold.', NULL::INT, 0::BIGINT, 0::BIGINT, 0::BIGINT;
        RETURN;
    END IF;

    -- Step 5: Refund Escrow to Previous High Bidder (if an active bid existed before buyout)
    IF v_listing.high_bidder_id IS NOT NULL AND v_listing.current_bid > 0 THEN
        UPDATE players
        SET escrow_gold = escrow_gold - v_listing.current_bid,
            gold_balance = gold_balance + v_listing.current_bid
        WHERE player_id = v_listing.high_bidder_id;
    END IF;

    -- Step 6: Calculate Realm Gold-Sink Tax & Net Payout
    v_tax_amount := (v_listing.buyout_price * v_listing.tax_rate_bps) / 10000;
    v_net_payout := v_listing.buyout_price - v_tax_amount;

    -- Step 7: Debit Buyer & Credit Seller Atomically
    UPDATE players
    SET gold_balance = gold_balance - v_listing.buyout_price
    WHERE player_id = p_buyer_id;

    UPDATE players
    SET gold_balance = gold_balance + v_net_payout
    WHERE player_id = v_listing.seller_id;

    -- Step 8: Transfer Unique Item Instance Ownership & Release Escrow Lock
    UPDATE inventory_items
    SET owner_id = p_buyer_id,
        is_escrowed = FALSE
    WHERE instance_id = v_listing.instance_id;

    -- Step 9: Close Auction Listing
    UPDATE auction_listings
    SET status = 'SOLD',
        high_bidder_id = p_buyer_id,
        current_bid = v_listing.buyout_price
    WHERE listing_id = p_listing_id;

    -- Step 10: Append Immutable Double-Entry Audit Record
    INSERT INTO ledger_transactions (
        listing_id, instance_id, seller_id, buyer_id,
        gross_price, market_tax_burned, seller_net_payout, settlement_type
    ) VALUES (
        p_listing_id, v_listing.instance_id, v_listing.seller_id, p_buyer_id,
        v_listing.buyout_price, v_tax_amount, v_net_payout, 'INSTANT_BUYOUT'
    ) RETURNING ledger_transactions.tx_id INTO v_new_tx_id;

    RETURN QUERY SELECT TRUE, 'OK: Atomic buyout settled.', v_new_tx_id, v_listing.buyout_price, v_tax_amount, v_net_payout;
END;
$$;


-- ============================================================================
-- TRANSACTION 2: ATOMIC ESCROW BID PLACEMENT (With Automatic Outbid Refund)
-- ============================================================================
CREATE OR REPLACE FUNCTION place_atomic_bid(
    p_listing_id INT,
    p_bidder_id INT,
    p_bid_amount BIGINT
) RETURNS TABLE (
    success BOOLEAN,
    message TEXT,
    new_high_bid BIGINT
) LANGUAGE plpgsql AS $$
DECLARE
    v_listing RECORD;
    v_bidder_gold BIGINT;
    v_min_required BIGINT;
BEGIN
    SELECT * INTO v_listing
    FROM auction_listings
    WHERE listing_id = p_listing_id
    FOR UPDATE;

    IF NOT FOUND OR v_listing.status <> 'ACTIVE' THEN
        RETURN QUERY SELECT FALSE, 'ERR_INACTIVE: Listing is no longer active.', 0::BIGINT;
        RETURN;
    END IF;

    IF v_listing.seller_id = p_bidder_id THEN
        RETURN QUERY SELECT FALSE, 'ERR_SELF_BID: Seller cannot bid on own item.', 0::BIGINT;
        RETURN;
    END IF;

    v_min_required := CASE
        WHEN v_listing.current_bid = 0 THEN v_listing.start_price
        ELSE v_listing.current_bid + GREATEST(1, (v_listing.current_bid * 5) / 100)
    END;

    IF p_bid_amount < v_min_required THEN
        RETURN QUERY SELECT FALSE, 'ERR_BID_TOO_LOW: Minimum required bid is ' || v_min_required || 'g.', v_listing.current_bid;
        RETURN;
    END IF;

    -- Lock Bidder & Previous High Bidder in Deterministic Order
    PERFORM 1 FROM players
    WHERE player_id IN (p_bidder_id, COALESCE(v_listing.high_bidder_id, -1))
    ORDER BY player_id ASC
    FOR UPDATE;

    SELECT gold_balance INTO v_bidder_gold FROM players WHERE player_id = p_bidder_id;
    IF v_bidder_gold < p_bid_amount THEN
        RETURN QUERY SELECT FALSE, 'ERR_INSUFFICIENT_GOLD: Insufficient free gold for escrow.', v_listing.current_bid;
        RETURN;
    END IF;

    -- Refund previous high bidder's escrow
    IF v_listing.high_bidder_id IS NOT NULL AND v_listing.current_bid > 0 THEN
        UPDATE players
        SET escrow_gold = escrow_gold - v_listing.current_bid,
            gold_balance = gold_balance + v_listing.current_bid
        WHERE player_id = v_listing.high_bidder_id;
    END IF;

    -- Move new bidder's gold into escrow
    UPDATE players
    SET gold_balance = gold_balance - p_bid_amount,
        escrow_gold = escrow_gold + p_bid_amount
    WHERE player_id = p_bidder_id;

    -- Update listing & log bid
    UPDATE auction_listings
    SET current_bid = p_bid_amount,
        high_bidder_id = p_bidder_id
    WHERE listing_id = p_listing_id;

    INSERT INTO auction_bids (listing_id, bidder_id, bid_amount)
    VALUES (p_listing_id, p_bidder_id, p_bid_amount);

    RETURN QUERY SELECT TRUE, 'OK: Bid locked in escrow.', p_bid_amount;
END;
$$;

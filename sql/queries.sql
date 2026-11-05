-- ============================================================================
-- SCROLLS OF AGORA: ANALYTICAL & OPERATIONAL SQL + RELATIONAL ALGEBRA SUITE
-- Covers Selection, Projection, ISA Subtype Joins, Set Difference,
-- Multi-Table Aggregations, Window Functions, and Anti-Fraud Detection
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Q1 [Basic RA: Selection & Projection (σ, π)]
-- Natural Language: List all Legendary and Mythic item templates requiring
--                   character level 60 or higher, ordered by base vendor value.
-- Relational Algebra:
--   π_{item_id, item_name, category, rarity, required_level, base_vendor_value}(
--       σ_{(rarity = 'Legendary' ∨ rarity = 'Mythic') ∧ required_level ≥ 60}(item_templates)
--   )
-- ----------------------------------------------------------------------------
SELECT item_id, item_name, category, rarity, required_level, base_vendor_value
FROM item_templates
WHERE rarity IN ('Legendary', 'Mythic')
  AND required_level >= 60
ORDER BY base_vendor_value DESC;


-- ----------------------------------------------------------------------------
-- Q2 [ISA Generalization / Specialization Subtype Join (⋈)]
-- Natural Language: Retrieve all active weapon/armor auction listings alongside
--                   their combat equipment specifications (attack power, slot,
--                   sockets), seller name, and buyout price.
-- Relational Algebra:
--   π_{listing_id, item_name, rarity, equip_slot, attack_power, username, buyout_price}(
--       σ_{status = 'ACTIVE'}(auction_listings)
--       ⋈_{auction_listings.instance_id = inventory_items.instance_id} inventory_items
--       ⋈_{inventory_items.item_id = item_templates.item_id} item_templates
--       ⋈_{item_templates.item_id = equipment_specs.item_id} equipment_specs
--       ⋈_{auction_listings.seller_id = players.player_id} players
--   )
-- ----------------------------------------------------------------------------
SELECT
    al.listing_id,
    it.item_name,
    it.rarity,
    es.equip_slot,
    es.attack_power,
    es.armor_rating,
    es.socket_count,
    p.username AS seller,
    al.current_bid,
    al.buyout_price
FROM auction_listings al
JOIN inventory_items ii ON ii.instance_id = al.instance_id
JOIN item_templates it ON it.item_id = ii.item_id
JOIN equipment_specs es ON es.item_id = it.item_id
JOIN players p ON p.player_id = al.seller_id
WHERE al.status = 'ACTIVE'
ORDER BY al.buyout_price ASC;


-- ----------------------------------------------------------------------------
-- Q3 [Set Difference / Universal Exclusion (− / NOT EXISTS)]
-- Natural Language: Find all Epic, Legendary, or Mythic item templates that
--                   currently have ZERO active listings across any realm
--                   (complete market scarcity / supply drought).
-- Relational Algebra:
--   π_{item_id, item_name, rarity}(σ_{rarity ∈ {'Epic','Legendary','Mythic'}}(item_templates))
--   −
--   π_{item_id, item_name, rarity}(
--       item_templates ⋈ inventory_items ⋈ σ_{status = 'ACTIVE'}(auction_listings)
--   )
-- ----------------------------------------------------------------------------
SELECT it.item_id, it.item_name, it.category, it.rarity, it.base_vendor_value
FROM item_templates it
WHERE it.rarity IN ('Epic', 'Legendary', 'Mythic')
  AND NOT EXISTS (
      SELECT 1
      FROM inventory_items ii
      JOIN auction_listings al ON al.instance_id = ii.instance_id
      WHERE ii.item_id = it.item_id
        AND al.status = 'ACTIVE'
  )
ORDER BY it.base_vendor_value DESC;


-- ----------------------------------------------------------------------------
-- Q4 [Multi-Table Aggregation & Grouping (γ, GROUP BY / HAVING)]
-- Natural Language: For each realm trading hub, calculate the total gross
--                   trading volume, total deflationary gold burned via kiosk
--                   taxes, average settlement price, and total settled trades.
-- Relational Algebra:
--   γ_{realm_name, region; COUNT(tx_id)→trades, SUM(gross_price)→gross_vol,
--      SUM(market_tax_burned)→tax_burned, AVG(gross_price)→avg_trade}(
--       realms ⋈ auction_listings ⋈ ledger_transactions
--   )
-- ----------------------------------------------------------------------------
SELECT
    r.realm_name,
    r.region,
    r.tax_rate_bps / 100.0 AS tax_rate_pct,
    COUNT(lt.tx_id) AS settled_trades,
    COALESCE(SUM(lt.gross_price), 0) AS gross_gold_volume,
    COALESCE(SUM(lt.market_tax_burned), 0) AS total_gold_burned,
    ROUND(COALESCE(AVG(lt.gross_price), 0), 2) AS avg_trade_price
FROM realms r
LEFT JOIN auction_listings al ON al.realm_id = r.realm_id
LEFT JOIN ledger_transactions lt ON lt.listing_id = al.listing_id
GROUP BY r.realm_id, r.realm_name, r.region, r.tax_rate_bps
ORDER BY gross_gold_volume DESC;


-- ----------------------------------------------------------------------------
-- Q5 [Cross-Hub Arbitrage Scanner (Self-Join & Price Spread Analysis)]
-- Natural Language: Identify items listed simultaneously on two different
--                   trading hubs where buying the cheapest listing on Hub A and
--                   selling at the lowest price on Hub B yields > 25% profit.
-- ----------------------------------------------------------------------------
WITH realm_floor_prices AS (
    SELECT
        ii.item_id,
        it.item_name,
        it.rarity,
        r.realm_name,
        MIN(al.buyout_price) AS floor_buyout
    FROM auction_listings al
    JOIN inventory_items ii ON ii.instance_id = al.instance_id
    JOIN item_templates it ON it.item_id = ii.item_id
    JOIN realms r ON r.realm_id = al.realm_id
    WHERE al.status = 'ACTIVE'
      AND al.buyout_price IS NOT NULL
    GROUP BY ii.item_id, it.item_name, it.rarity, r.realm_name
)
SELECT
    src.item_name,
    src.rarity,
    src.realm_name AS buy_on_realm,
    src.floor_buyout AS buy_price,
    dst.realm_name AS sell_on_realm,
    dst.floor_buyout AS sell_price,
    (dst.floor_buyout - src.floor_buyout) AS gross_spread,
    ROUND(((dst.floor_buyout - src.floor_buyout)::NUMERIC / src.floor_buyout) * 100, 1) AS roi_pct
FROM realm_floor_prices src
JOIN realm_floor_prices dst
  ON src.item_id = dst.item_id
 AND src.realm_name <> dst.realm_name
WHERE dst.floor_buyout > src.floor_buyout * 1.25
ORDER BY roi_pct DESC;


-- ----------------------------------------------------------------------------
-- Q6 [Anti-Cheat / RMT Wash-Trading & Gold-Laundering Anomaly Detection]
-- Natural Language: Flag suspicious settled trades where a buyer paid more
--                   than 300% of the item's historical average trade price OR
--                   more than 10x the item's base vendor value (classic
--                   Real-Money-Trading gold transfer signature via junk items).
-- ----------------------------------------------------------------------------
WITH item_market_Stats AS (
    SELECT
        ii.item_id,
        AVG(lt.gross_price) AS avg_market_price,
        STDDEV_POP(lt.gross_price) AS stddev_price
    FROM ledger_transactions lt
    JOIN inventory_items ii ON ii.instance_id = lt.instance_id
    GROUP BY ii.item_id
)
SELECT
    lt.tx_id,
    it.item_name,
    it.rarity,
    seller.username AS seller_account,
    buyer.username AS buyer_account,
    lt.gross_price AS suspicious_price,
    ROUND(ims.avg_market_price, 0) AS normal_market_avg,
    ROUND(lt.gross_price / NULLIF(ims.avg_market_price, 0), 2) AS price_multiplier_x,
    lt.executed_at
FROM ledger_transactions lt
JOIN inventory_items ii ON ii.instance_id = lt.instance_id
JOIN item_templates it ON it.item_id = ii.item_id
JOIN players seller ON seller.player_id = lt.seller_id
JOIN players buyer ON buyer.player_id = lt.buyer_id
LEFT JOIN item_market_Stats ims ON ims.item_id = it.item_id
WHERE lt.gross_price > GREATEST(it.base_vendor_value * 10, COALESCE(ims.avg_market_price * 2.5, 0))
ORDER BY price_multiplier_x DESC NULLS LAST;


-- ----------------------------------------------------------------------------
-- Q7 [Window Functions: Whale Merchant Leaderboard & Net Worth Ranking]
-- Natural Language: Rank all players by their total liquid + escrow gold plus
--                   total net sales revenue, computing their wealth percentile
--                   within their faction.
-- ----------------------------------------------------------------------------
WITH seller_revenue AS (
    SELECT seller_id, SUM(seller_net_payout) AS total_earned, COUNT(*) AS sales_count
    FROM ledger_transactions
    GROUP BY seller_id
)
SELECT
    p.username,
    p.faction,
    p.character_class,
    p.gold_balance AS liquid_gold,
    p.escrow_gold,
    COALESCE(sr.total_earned, 0) AS lifetime_sales_gold,
    (p.gold_balance + p.escrow_gold) AS total_wallet_wealth,
    RANK() OVER (ORDER BY (p.gold_balance + p.escrow_gold) DESC) AS global_wealth_rank,
    RANK() OVER (PARTITION BY p.faction ORDER BY (p.gold_balance + p.escrow_gold) DESC) AS faction_rank
FROM players p
LEFT JOIN seller_revenue sr ON sr.seller_id = p.player_id
ORDER BY global_wealth_rank ASC;

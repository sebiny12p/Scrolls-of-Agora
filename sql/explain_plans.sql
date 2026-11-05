-- ============================================================================
-- SCROLLS OF AGORA: QUERY EXECUTION PLANS & PERFORMANCE PROFILES
-- Contains EXPLAIN (ANALYZE, BUFFERS) for PostgreSQL 18 & EXPLAIN QUERY PLAN for SQLite
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Q1: Selection & Projection (σ, π)
-- ----------------------------------------------------------------------------
EXPLAIN (ANALYZE, BUFFERS)
SELECT item_id, item_name, category, rarity, required_level, base_vendor_value
FROM item_templates
WHERE rarity IN ('Legendary', 'Mythic')
  AND required_level >= 60
ORDER BY base_vendor_value DESC;


-- ----------------------------------------------------------------------------
-- Q2: ISA Specialization Subtype Join (⋈)
-- ----------------------------------------------------------------------------
EXPLAIN (ANALYZE, BUFFERS)
SELECT al.listing_id, it.item_name, it.rarity, es.equip_slot,
       (es.attack_power + ii.bonus_power) AS attack_power, es.armor_rating,
       p.username AS seller, r.realm_name AS kiosk_hub, al.buyout_price
FROM auction_listings al
JOIN inventory_items ii ON ii.instance_id = al.instance_id
JOIN item_templates it ON it.item_id = ii.item_id
JOIN equipment_specs es ON es.item_id = it.item_id
JOIN players p ON p.player_id = al.seller_id
JOIN realms r ON r.realm_id = al.realm_id
WHERE al.status = 'ACTIVE'
ORDER BY al.buyout_price ASC;


-- ----------------------------------------------------------------------------
-- Q3: Universal Supply Drought (Set Difference − / NOT EXISTS)
-- ----------------------------------------------------------------------------
EXPLAIN (ANALYZE, BUFFERS)
SELECT it.item_id, it.item_name, it.category, it.rarity, it.base_vendor_value
FROM item_templates it
WHERE it.rarity IN ('Rare', 'Epic', 'Legendary', 'Mythic')
  AND NOT EXISTS (
      SELECT 1 FROM inventory_items ii
      JOIN auction_listings al ON al.instance_id = ii.instance_id
      WHERE ii.item_id = it.item_id AND al.status = 'ACTIVE'
  )
ORDER BY it.base_vendor_value DESC;


-- ----------------------------------------------------------------------------
-- Q4: Multi-Table Grouping & Tax Burn Aggregations (γ)
-- ----------------------------------------------------------------------------
EXPLAIN (ANALYZE, BUFFERS)
SELECT r.realm_name, r.province, tg.guild_name AS controlling_guild,
       ROUND(r.tax_rate_bps / 100.0, 2) AS kiosk_cut_pct,
       COUNT(lt.tx_id) AS settled_trades,
       COALESCE(SUM(lt.gross_price), 0) AS gross_gold_volume,
       COALESCE(SUM(lt.market_tax_burned), 0) AS total_gold_burned
FROM realms r
LEFT JOIN trade_guilds tg ON tg.guild_id = r.controlling_guild_id
LEFT JOIN auction_listings al ON al.realm_id = r.realm_id
LEFT JOIN ledger_transactions lt ON lt.listing_id = al.listing_id
GROUP BY r.realm_id, r.realm_name, r.province, tg.guild_name, r.tax_rate_bps
ORDER BY gross_gold_volume DESC;


-- ----------------------------------------------------------------------------
-- Q5: Cross-City Arbitrage Scanner (CTE Self-Join)
-- ----------------------------------------------------------------------------
EXPLAIN (ANALYZE, BUFFERS)
WITH realm_floor_prices AS (
    SELECT ii.item_id, it.item_name, it.rarity, r.realm_name,
           MIN(al.buyout_price) AS floor_buyout
    FROM auction_listings al
    JOIN inventory_items ii ON ii.instance_id = al.instance_id
    JOIN item_templates it ON it.item_id = ii.item_id
    JOIN realms r ON r.realm_id = al.realm_id
    WHERE al.status = 'ACTIVE' AND al.buyout_price IS NOT NULL
    GROUP BY ii.item_id, it.item_name, it.rarity, r.realm_name
)
SELECT src.item_name, src.rarity,
       src.realm_name AS buy_kiosk, src.floor_buyout AS buy_price,
       dst.realm_name AS flip_kiosk, dst.floor_buyout AS sell_price,
       (dst.floor_buyout - src.floor_buyout) AS profit_spread,
       ROUND(((dst.floor_buyout - src.floor_buyout) * 100.0) / src.floor_buyout, 1) AS roi_pct
FROM realm_floor_prices src
JOIN realm_floor_prices dst
  ON src.item_id = dst.item_id AND src.realm_name <> dst.realm_name
WHERE dst.floor_buyout > src.floor_buyout * 1.15
ORDER BY roi_pct DESC;


-- ----------------------------------------------------------------------------
-- Q6: Anti-Cheat RMT Anomaly Detector (Non-Equi Theta Join)
-- ----------------------------------------------------------------------------
EXPLAIN (ANALYZE, BUFFERS)
SELECT lt.tx_id, it.item_name,
       seller.username AS mule_recipient,
       buyer.username AS launder_sender,
       it.base_vendor_value AS real_val,
       lt.gross_price AS laundered_gold,
       ROUND(lt.gross_price * 1.0 / MAX(1, it.base_vendor_value), 0) AS inflation_x
FROM ledger_transactions lt
JOIN inventory_items ii ON ii.instance_id = lt.instance_id
JOIN item_templates it ON it.item_id = ii.item_id
JOIN players seller ON seller.player_id = lt.seller_id
JOIN players buyer ON buyer.player_id = lt.buyer_id
WHERE lt.gross_price > it.base_vendor_value * 15
ORDER BY inflation_x DESC;


-- ----------------------------------------------------------------------------
-- Q7: Window Functions & Wealth Partition Ranking
-- ----------------------------------------------------------------------------
EXPLAIN (ANALYZE, BUFFERS)
WITH seller_revenue AS (
    SELECT seller_id, SUM(seller_net_payout) AS total_earned, COUNT(*) AS sales_count
    FROM ledger_transactions
    GROUP BY seller_id
)
SELECT p.username, p.faction, p.character_class,
       p.gold_balance AS liquid_gold,
       p.escrow_gold,
       (p.gold_balance + p.escrow_gold) AS net_worth,
       RANK() OVER (ORDER BY (p.gold_balance + p.escrow_gold) DESC) AS global_rank,
       RANK() OVER (PARTITION BY p.faction ORDER BY (p.gold_balance + p.escrow_gold) DESC) AS faction_rank
FROM players p
LEFT JOIN seller_revenue sr ON sr.seller_id = p.player_id
WHERE p.is_banned = 0
ORDER BY global_rank ASC;

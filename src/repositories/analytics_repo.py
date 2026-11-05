"""
Analytics Repository for Scrolls of Agora.
Houses the 7 Relational Algebra analytical queries, query plan explanations,
the Recursive CTE (WITH RECURSIVE) RMT money-laundering graph tracer with cycle detection,
and double-entry ledger audits.
"""

import time
import uuid
from typing import Dict, Any, List

from src.database import (
    get_db_cursor,
    execute_sql,
    adapt_sql,
    row_to_dict,
    rows_to_dicts,
    is_postgres,
    record_journal_entries,
    audit_ledger_integrity,
)


ANALYTICAL_CATALOG = {
    "q1_mythic_projection": {
        "title": "Q1: High-Tier Mythic & Legendary Catalog (Selection & Projection)",
        "ra": "π_{item_id, item_name, category, rarity, required_level, base_vendor_value}(σ_{(rarity='Legendary' ∨ rarity='Mythic') ∧ required_level ≥ 60}(item_templates))",
        "sql": """SELECT item_id, item_name, category, rarity, required_level, base_vendor_value
FROM item_templates
WHERE rarity IN ('Legendary', 'Mythic')
  AND required_level >= 60
ORDER BY base_vendor_value DESC;""",
    },
    "q2_isa_equipment_join": {
        "title": "Q2: Active Equipment Orderbook (ISA Subtype Specialization Join)",
        "ra": "π_{listing_id, item_name, rarity, equip_slot, attack_power, armor_rating, username, buyout_price}(σ_{status='ACTIVE'}(auction_listings) ⋈ inventory_items ⋈ item_templates ⋈ equipment_specs ⋈ players)",
        "sql": """SELECT al.listing_id, it.item_name, it.rarity, es.equip_slot,
       (es.attack_power + ii.bonus_power) AS attack_power, es.armor_rating,
       p.username AS seller, r.realm_name AS kiosk_hub, al.buyout_price
FROM auction_listings al
JOIN inventory_items ii ON ii.instance_id = al.instance_id
JOIN item_templates it ON it.item_id = ii.item_id
JOIN equipment_specs es ON es.item_id = it.item_id
JOIN players p ON p.player_id = al.seller_id
JOIN realms r ON r.realm_id = al.realm_id
WHERE al.status = 'ACTIVE'
ORDER BY al.buyout_price ASC;""",
    },
    "q3_market_scarcity_diff": {
        "title": "Q3: Complete Market Scarcity / Unlisted High-Tier Items (Set Difference −)",
        "ra": "π_{item_id, item_name, rarity}(σ_{rarity ∈ {'Rare','Epic','Legendary','Mythic'}}(item_templates)) − π_{item_id, item_name, rarity}(item_templates ⋈ inventory_items ⋈ σ_{status='ACTIVE'}(auction_listings))",
        "sql": """SELECT it.item_id, it.item_name, it.category, it.rarity, it.base_vendor_value
FROM item_templates it
WHERE it.rarity IN ('Rare', 'Epic', 'Legendary', 'Mythic')
  AND NOT EXISTS (
      SELECT 1 FROM inventory_items ii
      JOIN auction_listings al ON al.instance_id = ii.instance_id
      WHERE ii.item_id = it.item_id AND al.status = 'ACTIVE'
  )
ORDER BY it.base_vendor_value DESC;""",
    },
    "q4_realm_tax_burn": {
        "title": "Q4: Regional Hub Macro-Economy & Guild Tax Burn (Grouping γ)",
        "ra": "γ_{realm_name, province; COUNT(tx_id)→trades, SUM(gross_price)→gross_vol, SUM(market_tax_burned)→tax_burned}(realms ⟕ auction_listings ⟕ ledger_transactions)",
        "sql": """SELECT r.realm_name, r.province, tg.guild_name AS controlling_guild,
       ROUND(r.tax_rate_bps / 100.0, 2) AS kiosk_cut_pct,
       COUNT(lt.tx_id) AS settled_trades,
       COALESCE(SUM(lt.gross_price), 0) AS gross_gold_volume,
       COALESCE(SUM(lt.market_tax_burned), 0) AS total_gold_burned
FROM realms r
LEFT JOIN trade_guilds tg ON tg.guild_id = r.controlling_guild_id
LEFT JOIN auction_listings al ON al.realm_id = r.realm_id
LEFT JOIN ledger_transactions lt ON lt.listing_id = al.listing_id
GROUP BY r.realm_id, r.realm_name, r.province, tg.guild_name, r.tax_rate_bps
ORDER BY gross_gold_volume DESC;""",
    },
    "q5_cross_realm_arbitrage": {
        "title": "Q5: Cross-City Arbitrage Scanner (CTE Self-Join)",
        "ra": "σ_{dst.floor_buyout > src.floor_buyout × 1.15}(ρ_{src}(HubFloor) ⋈_{src.item_id = dst.item_id ∧ src.realm ≠ dst.realm} ρ_{dst}(HubFloor))",
        "sql": """WITH realm_floor_prices AS (
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
ORDER BY roi_pct DESC;""",
    },
    "q6_rmt_anomaly_detection": {
        "title": "Q6: Inquisitor RMT Gold-Laundering Wash-Trade Detector",
        "ra": "σ_{gross_price > 15 × base_vendor_value}(ledger_transactions ⋈ inventory_items ⋈ item_templates ⋈ ρ_{seller}(players) ⋈ ρ_{buyer}(players))",
        "sql": """SELECT lt.tx_id, it.item_name,
       seller.username AS mule_recipient,
       buyer.username AS launder_sender,
       it.base_vendor_value AS real_val,
       lt.gross_price AS laundered_gold,
       ROUND(lt.gross_price * 1.0 / (CASE WHEN it.base_vendor_value = 0 THEN 1 ELSE it.base_vendor_value END), 0) AS inflation_x
FROM ledger_transactions lt
JOIN inventory_items ii ON ii.instance_id = lt.instance_id
JOIN item_templates it ON it.item_id = ii.item_id
JOIN players seller ON seller.player_id = lt.seller_id
JOIN players buyer ON buyer.player_id = lt.buyer_id
WHERE lt.gross_price > it.base_vendor_value * 15
ORDER BY inflation_x DESC;""",
    },
    "q7_whale_leaderboard": {
        "title": "Q7: Merchant Whale Net-Worth & Alliance Rank (Window Functions)",
        "ra": "π_{username, faction, liquid_gold, escrow_gold, sales_gold, RANK() OVER (PARTITION BY faction)}(players ⟕ γ_{seller_id; SUM(seller_net_payout)}(ledger_transactions))",
        "sql": """WITH seller_revenue AS (
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
ORDER BY global_rank ASC;""",
    },
}


def run_analytical_query(query_key: str) -> Dict[str, Any]:
    if query_key not in ANALYTICAL_CATALOG:
        return {"error": f"Unknown query key: {query_key}"}

    entry = ANALYTICAL_CATALOG[query_key]
    with get_db_cursor() as cur:
        t0 = time.perf_counter()
        execute_sql(cur, entry["sql"])
        rows = rows_to_dicts(cur.fetchall())
        elapsed_us = int((time.perf_counter() - t0) * 1_000_000)

        # Plan explanation based on active engine
        try:
            if is_postgres():
                cur.execute("EXPLAIN " + entry["sql"])
                plan_rows = [r[0] if isinstance(r, (list, tuple)) else str(r) for r in cur.fetchall()]
            else:
                cur.execute("EXPLAIN QUERY PLAN " + entry["sql"])
                plan_rows = [r["detail"] if hasattr(r, "keys") and "detail" in r.keys() else str(r) for r in cur.fetchall()]
        except Exception as e:
            plan_rows = [f"Plan inspection unavailable: {e}"]

        return {
            "title": entry["title"],
            "ra": entry["ra"],
            "sql": entry["sql"],
            "latency_us": elapsed_us,
            "query_plan": plan_rows,
            "rows": rows,
        }


def get_rmt_laundering_graph() -> Dict[str, Any]:
    """
    Executes a true Recursive Common Table Expression (WITH RECURSIVE)
    with SQL-level cycle detection to trace multi-hop gold laundering trails
    through wash-trade items.
    """
    t0 = time.perf_counter()
    with get_db_cursor() as cur:
        # Recursive CTE with visited node path tracking to prevent cyclic infinite loops
        recursive_sql = """
        WITH RECURSIVE
        rmt_wash_edges AS (
            SELECT
                lt.tx_id,
                lt.seller_id AS recipient_id,
                seller.username AS recipient_name,
                seller.is_banned AS recipient_banned,
                lt.buyer_id AS sender_id,
                buyer.username AS sender_name,
                it.item_name,
                it.base_vendor_value,
                lt.gross_price,
                r.realm_name,
                lt.executed_at
            FROM ledger_transactions lt
            JOIN inventory_items ii ON ii.instance_id = lt.instance_id
            JOIN item_templates it ON it.item_id = ii.item_id
            JOIN players seller ON seller.player_id = lt.seller_id
            JOIN players buyer ON buyer.player_id = lt.buyer_id
            JOIN auction_listings al ON al.listing_id = lt.listing_id
            JOIN realms r ON r.realm_id = al.realm_id
            WHERE lt.gross_price >= it.base_vendor_value * 15
        ),
        laundering_chain AS (
            -- Anchor: Initial laundering transactions
            SELECT
                tx_id, sender_id, sender_name, recipient_id, recipient_name, recipient_banned,
                item_name, base_vendor_value, gross_price, realm_name,
                1 AS hop_depth,
                sender_name || ' -> ' || recipient_name AS trail_path,
                ',' || sender_id || ',' || recipient_id || ',' AS visited_nodes
            FROM rmt_wash_edges

            UNION ALL

            -- Recursive Step: Trace recipient moving illicit gold to another player (with cycle detection)
            SELECT
                e.tx_id, e.sender_id, e.sender_name, e.recipient_id, e.recipient_name, e.recipient_banned,
                e.item_name, e.base_vendor_value, e.gross_price, e.realm_name,
                c.hop_depth + 1,
                c.trail_path || ' -> ' || e.recipient_name,
                c.visited_nodes || e.recipient_id || ','
            FROM rmt_wash_edges e
            JOIN laundering_chain c ON e.sender_id = c.recipient_id
            WHERE c.hop_depth < 5
              AND instr(c.visited_nodes, ',' || e.recipient_id || ',') = 0
        )
        SELECT 
            tx_id, sender_id, sender_name, recipient_id, recipient_name, recipient_banned,
            item_name, base_vendor_value, gross_price, realm_name, hop_depth, trail_path
        FROM laundering_chain
        ORDER BY hop_depth ASC, tx_id ASC;
        """
        execute_sql(cur, recursive_sql)
        edges = rows_to_dicts(cur.fetchall())
        elapsed_us = int((time.perf_counter() - t0) * 1_000_000)

        # Unique transactions involved in the laundering chains
        unique_tx_ids = set()
        deduped_edges = []
        for e in edges:
            if e["tx_id"] not in unique_tx_ids:
                unique_tx_ids.add(e["tx_id"])
                deduped_edges.append(e)

        return {
            "latency_us": elapsed_us,
            "edges": deduped_edges if deduped_edges else edges,
            "total_laundered_gold": sum(e["gross_price"] for e in deduped_edges),
            "max_hop_depth": max((e["hop_depth"] for e in edges), default=1),
        }


def ban_and_seize_rmt_mule_ring() -> Dict[str, Any]:
    """
    Identifies accounts involved in wash trading (junk items sold for >15x vendor value),
    bans them, confiscates their illicit liquid gold, deposits it into the guild treasury,
    and records balanced double-entry journal entries.
    """
    with get_db_cursor(immediate=True) as cur:
        execute_sql(cur, """
            SELECT DISTINCT p.player_id, p.gold_balance
            FROM players p
            JOIN ledger_transactions lt ON lt.seller_id = p.player_id OR lt.buyer_id = p.player_id
            JOIN inventory_items ii ON ii.instance_id = lt.instance_id
            JOIN item_templates it ON it.item_id = ii.item_id
            WHERE lt.gross_price >= it.base_vendor_value * 15
              AND p.is_banned = 0;
        """)
        suspects = rows_to_dicts(cur.fetchall())
        if not suspects:
            return {
                "success": True,
                "banned_accounts": 0,
                "seized_gold": 0,
                "message": "Fraud Audit: No active illicit wash-trade accounts detected."
            }

        suspect_ids = [s["player_id"] for s in suspects]
        total_seized = sum(s["gold_balance"] for s in suspects)

        placeholders = ",".join("?" for _ in suspect_ids)
        execute_sql(
            cur,
            f"UPDATE players SET gold_balance = 0, is_banned = 1, reputation_score = 0 WHERE player_id IN ({placeholders});",
            tuple(suspect_ids),
        )

        # Find target guild for deposit (the guild with lowest treasury)
        execute_sql(cur, "SELECT guild_id FROM trade_guilds ORDER BY treasury_gold ASC LIMIT 1;")
        g_row = cur.fetchone()
        dest_guild_id = g_row["guild_id"] if g_row else 1

        # Deposit confiscated funds
        if total_seized > 0:
            execute_sql(
                cur,
                "UPDATE trade_guilds SET treasury_gold = treasury_gold + ? WHERE guild_id = ?;",
                (total_seized, dest_guild_id),
            )

            # Record balancing double-entry journal entries: Confiscate from suspects, Credit guild treasury
            tx_group_seize = f"TX-SEIZE-{uuid.uuid4().hex[:6]}"
            journal_entries = [
                ("PLAYER_LIQUID", str(s["player_id"]), -s["gold_balance"], f"Illicit gold confiscated from player #{s['player_id']}")
                for s in suspects if s["gold_balance"] > 0
            ]
            journal_entries.append(
                ("GUILD_TREASURY", str(dest_guild_id), total_seized, f"Inquisitor confiscated gold deposit to Guild #{dest_guild_id}")
            )
            record_journal_entries(cur, tx_group_seize, "SEIZURE", journal_entries)

        return {
            "success": True,
            "banned_accounts": len(suspect_ids),
            "seized_gold": total_seized,
            "message": f"Fraud Audit Executed: Banned {len(suspect_ids)} accounts in wash ring & confiscated {total_seized:,}g illicit gold.",
        }

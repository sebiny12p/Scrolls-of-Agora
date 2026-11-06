"""
Market Repository for Scrolls of Agora.
Handles queries for the 5-hub spatial orderbook, character inventory bag,
candlestick OHLC charts, and macro-economic KPIs across PostgreSQL & SQLite.
"""

from typing import Dict, Any, List, Optional
from src.database import get_db_cursor, execute_sql, row_to_dict, rows_to_dicts, ACTIVE_BACKEND, is_postgres


def get_market_state(player_id: int = 1005, realm_id: int = 0) -> Dict[str, Any]:
    with get_db_cursor() as cur:
        # 1. Fetch 5 Regional Kiosk Hubs + Controlling Guilds
        execute_sql(cur, """
            SELECT
                r.*,
                tg.guild_name AS controlling_guild_name,
                tg.alliance AS controlling_alliance,
                tg.treasury_gold AS guild_treasury,
                tg.tax_dividend_earned,
                (SELECT COUNT(*) FROM auction_listings al WHERE al.realm_id = r.realm_id AND al.status = 'ACTIVE') AS active_listings_count,
                (SELECT COALESCE(MAX(kb.bid_gold), 0) FROM kiosk_bids kb WHERE kb.realm_id = r.realm_id AND kb.status = 'SEALED') AS top_sealed_bid,
                (SELECT COUNT(*) FROM kiosk_bids kb WHERE kb.realm_id = r.realm_id AND kb.status = 'SEALED') AS sealed_bids_count
            FROM realms r
            LEFT JOIN trade_guilds tg ON tg.guild_id = r.controlling_guild_id
            ORDER BY r.realm_id ASC;
        """)
        realms = rows_to_dicts(cur.fetchall())

        execute_sql(cur, "SELECT * FROM trade_guilds ORDER BY treasury_gold DESC;")
        guilds = rows_to_dicts(cur.fetchall())

        # 2. Fetch Active Orderbook with Cross-City Arbitrage Spotter
        realm_filter_sql = "AND al.realm_id = ?" if realm_id and realm_id > 0 else ""
        params = (realm_id,) if realm_id and realm_id > 0 else ()

        execute_sql(cur, f"""
            SELECT
                al.listing_id, al.instance_id, al.realm_id, al.listing_type, al.start_price,
                al.buyout_price, al.current_bid, al.status, al.listed_at, al.expires_at,
                ii.mint_serial, ii.temper_tier, ii.bonus_power, ii.stack_size, ii.current_durability,
                it.item_id, it.item_name, it.icon_key, it.lore_text, it.category, it.rarity,
                it.required_level, it.base_vendor_value,
                es.equip_slot, (COALESCE(es.attack_power, 0) + ii.bonus_power) AS attack_power,
                (COALESCE(es.armor_rating, 0) + ii.bonus_power) AS armor_rating,
                es.max_durability, es.socket_count,
                cs.effect_type, cs.effect_potency, cs.duration_seconds,
                seller.player_id AS seller_id, seller.username AS seller_name, seller.faction AS seller_faction,
                bidder.username AS high_bidder_name,
                r.realm_name, r.province, r.tax_rate_bps,
                tg.guild_name AS kiosk_guild_name,
                GROUP_CONCAT(e.enchant_name || ' (+' || e.bonus_value || ' ' || e.stat_type || ')', ' | ') AS enchants,
                (
                    SELECT MAX(al2.buyout_price)
                    FROM auction_listings al2
                    JOIN inventory_items ii2 ON ii2.instance_id = al2.instance_id
                    WHERE ii2.item_id = it.item_id AND al2.status = 'ACTIVE' AND al2.realm_id <> al.realm_id
                ) AS other_hub_max_price,
                (
                    SELECT r2.realm_name
                    FROM auction_listings al2
                    JOIN inventory_items ii2 ON ii2.instance_id = al2.instance_id
                    JOIN realms r2 ON r2.realm_id = al2.realm_id
                    WHERE ii2.item_id = it.item_id AND al2.status = 'ACTIVE' AND al2.realm_id <> al.realm_id
                    ORDER BY al2.buyout_price DESC
                    LIMIT 1
                ) AS arbitrage_target_hub
            FROM auction_listings al
            JOIN inventory_items ii ON ii.instance_id = al.instance_id
            JOIN item_templates it ON it.item_id = ii.item_id
            LEFT JOIN equipment_specs es ON es.item_id = it.item_id
            LEFT JOIN consumable_specs cs ON cs.item_id = it.item_id
            JOIN players seller ON seller.player_id = al.seller_id
            LEFT JOIN players bidder ON bidder.player_id = al.high_bidder_id
            JOIN realms r ON r.realm_id = al.realm_id
            LEFT JOIN trade_guilds tg ON tg.guild_id = r.controlling_guild_id
            LEFT JOIN item_instance_enchantments iie ON iie.instance_id = ii.instance_id
            LEFT JOIN enchantments e ON e.enchant_id = iie.enchant_id
            WHERE al.status = 'ACTIVE' {realm_filter_sql}
            GROUP BY al.listing_id
            ORDER BY al.listing_id DESC;
        """, params)
        listings = rows_to_dicts(cur.fetchall())

        execute_sql(cur, """
            SELECT p.*, r.realm_name, tg.guild_name,
                   (SELECT COUNT(*) FROM inventory_items ii WHERE ii.owner_id = p.player_id) AS items_owned
            FROM players p
            JOIN realms r ON r.realm_id = p.realm_id
            LEFT JOIN trade_guilds tg ON tg.guild_id = p.guild_id
            WHERE p.is_banned = 0
            ORDER BY (p.gold_balance + p.escrow_gold) DESC;
        """)
        players = rows_to_dicts(cur.fetchall())

        execute_sql(cur, """
            SELECT
                ii.instance_id, ii.item_id, ii.mint_serial, ii.temper_tier, ii.bonus_power,
                ii.stack_size, ii.current_durability, ii.is_escrowed,
                it.item_name, it.icon_key, it.lore_text, it.category, it.rarity, it.required_level, it.base_vendor_value,
                es.equip_slot, (COALESCE(es.attack_power, 0) + ii.bonus_power) AS attack_power,
                (COALESCE(es.armor_rating, 0) + ii.bonus_power) AS armor_rating, es.socket_count,
                cs.effect_type, cs.effect_potency,
                GROUP_CONCAT(e.enchant_name || ' (+' || e.bonus_value || ' ' || e.stat_type || ')', ' | ') AS enchants
            FROM inventory_items ii
            JOIN item_templates it ON it.item_id = ii.item_id
            LEFT JOIN equipment_specs es ON es.item_id = it.item_id
            LEFT JOIN consumable_specs cs ON cs.item_id = it.item_id
            LEFT JOIN item_instance_enchantments iie ON iie.instance_id = ii.instance_id
            LEFT JOIN enchantments e ON e.enchant_id = iie.enchant_id
            WHERE ii.owner_id = ?
            GROUP BY ii.instance_id
            ORDER BY ii.is_escrowed ASC, it.base_vendor_value DESC;
        """, (player_id,))
        inventory = rows_to_dicts(cur.fetchall())

        execute_sql(cur, """
            SELECT
                lt.tx_id, lt.listing_id, lt.gross_price, lt.market_tax_burned,
                lt.seller_net_payout, lt.settlement_type, lt.executed_at,
                it.item_id, it.item_name, it.icon_key, it.rarity, ii.mint_serial,
                s.username AS seller_name, b.username AS buyer_name,
                r.realm_name
            FROM ledger_transactions lt
            JOIN inventory_items ii ON ii.instance_id = lt.instance_id
            JOIN item_templates it ON it.item_id = ii.item_id
            JOIN players s ON s.player_id = lt.seller_id
            JOIN players b ON b.player_id = lt.buyer_id
            JOIN auction_listings al ON al.listing_id = lt.listing_id
            JOIN realms r ON r.realm_id = al.realm_id
            ORDER BY lt.tx_id DESC
            LIMIT 16;
        """)
        ledger = rows_to_dicts(cur.fetchall())

        execute_sql(cur, "SELECT * FROM enchantments ORDER BY tier DESC;")
        enchantments = rows_to_dicts(cur.fetchall())

        execute_sql(cur, """
            SELECT
                (SELECT COUNT(*) FROM auction_listings WHERE status = 'ACTIVE') AS active_orders,
                (SELECT COALESCE(SUM(gross_price), 0) FROM ledger_transactions) AS total_volume,
                (SELECT COALESCE(SUM(market_tax_burned), 0) FROM ledger_transactions) AS total_tax_burned,
                (SELECT COALESCE(SUM(escrow_gold), 0) FROM players) AS total_escrow_locked,
                (SELECT COUNT(*) FROM inventory_items) AS total_minted_items,
                (SELECT COUNT(DISTINCT mint_serial) FROM inventory_items) AS unique_serials
        """)
        kpi_row = cur.fetchone()
        kpis = row_to_dict(kpi_row)
        kpis["backend_engine"] = ACTIVE_BACKEND
        execute_sql(cur, "SELECT COUNT(*) AS uncollected_mail FROM player_mail WHERE recipient_id = ? AND is_collected = 0;", (player_id,))
        mail_row = cur.fetchone()
        kpis["uncollected_mail"] = (mail_row["uncollected_mail"] if hasattr(mail_row, "keys") else mail_row[0]) if mail_row else 0

    return {
        "kpis": kpis,
        "realms": realms,
        "guilds": guilds,
        "listings": listings,
        "players": players,
        "inventory": inventory,
        "enchantments": enchantments,
        "ledger": ledger,
    }


def get_item_candles(item_id: int) -> Dict[str, Any]:
    with get_db_cursor() as cur:
        execute_sql(cur, "SELECT item_name, rarity, base_vendor_value FROM item_templates WHERE item_id = ?;", (item_id,))
        item = row_to_dict(cur.fetchone())

        execute_sql(cur, """
            SELECT bucket_timestamp, open_price, high_price, low_price, close_price, volume_traded
            FROM price_history_ohlc
            WHERE item_id = ?
            ORDER BY candle_id DESC
            LIMIT 24;
        """, (item_id,))
        rows = rows_to_dicts(cur.fetchall())
        rows.reverse()

    return {
        "item_id": item_id,
        "item_name": item.get("item_name", "Unknown"),
        "rarity": item.get("rarity", "Common"),
        "candles": rows,
    }

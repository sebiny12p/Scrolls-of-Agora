"""
Large-Scale Relational Dataset Generator & Index Benchmark Script.
Project: Scrolls of Agora
Usage:
  python scripts/seed_scale.py --listings 10000 --players 2000
"""

import argparse
import random
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.database import get_db_cursor, execute_sql, is_postgres, init_database


def generate_scale_data(target_listings: int = 10000, target_players: int = 2000):
    print("=" * 72)
    print(f"  SCROLLS OF AGORA — RELATIONAL DATASET SCALE GENERATOR")
    print(f"  Target Listings: {target_listings:,} | Target Players: {target_players:,}")
    print("=" * 72)

    init_database(force=False)
    t0 = time.perf_counter()

    # 1. Bulk generate players
    print(f"[*] Generating {target_players:,} players across 5 alliances...")
    factions = ["Vanguard", "Syndicate", "Outlanders"]
    classes = ["Templar", "Dragonknight", "Nightblade", "Sorcerer", "Warden", "Necromancer", "Arcanist"]
    
    player_tuples = []
    base_player_id = 2000
    for i in range(target_players):
        pid = base_player_id + i
        username = f"Player_{pid}_{uuid.uuid4().hex[:4]}"
        rid = random.randint(1, 5)
        gid = random.choice([1, 2, 3, 4, 5, None])
        faction = random.choice(factions)
        c_class = random.choice(classes)
        lvl = random.randint(10, 100)
        gold = random.randint(5000, 2500000)
        escrow = 0
        rep = random.randint(50, 1500)
        player_tuples.append((pid, username, rid, gid, faction, c_class, lvl, gold, escrow, rep, 0))

    with get_db_cursor(immediate=True) as cur:
        # Check current player count
        execute_sql(cur, "SELECT COUNT(*) FROM players;")
        curr_p = cur.fetchone()[0]
        if curr_p < target_players:
            cur.executemany(
                """
                INSERT OR IGNORE INTO players (player_id, username, realm_id, guild_id, faction, character_class, level, gold_balance, escrow_gold, reputation_score, is_banned)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """ if not is_postgres() else """
                INSERT INTO players (player_id, username, realm_id, guild_id, faction, character_class, level, gold_balance, escrow_gold, reputation_score, is_banned)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (player_id) DO NOTHING;
                """,
                player_tuples,
            )
            print(f"[+] Inserted {len(player_tuples):,} player records.")

    # 2. Bulk generate inventory instances & listings
    print(f"[*] Generating {target_listings:,} items & market listings...")
    item_templates = [5001, 5002, 5003, 5004, 5005, 5006, 5007, 5008, 5009, 5010, 5011, 5012, 5014]
    
    # 5% active listings, 95% historical (SOLD, EXPIRED, CANCELLED) to simulate real-world skewed orderbook
    active_count = max(50, int(target_listings * 0.05))
    historical_count = target_listings - active_count
    
    sold_count = int(historical_count * 0.75)
    expired_count = int(historical_count * 0.15)
    cancelled_count = historical_count - sold_count - expired_count
    
    statuses = (["ACTIVE"] * active_count) + (["SOLD"] * sold_count) + (["EXPIRED"] * expired_count) + (["CANCELLED"] * cancelled_count)
    while len(statuses) < target_listings:
        statuses.append("SOLD")
    statuses = statuses[:target_listings]
    random.shuffle(statuses)

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    item_rows = []
    listing_rows = []
    base_instance_id = 20000
    base_listing_id = 50000

    for i in range(target_listings):
        inst_id = base_instance_id + i
        list_id = base_listing_id + i
        tid = random.choice(item_templates)
        owner_id = random.randint(base_player_id, base_player_id + target_players - 1)
        serial = f"AGORA-SCALE-{inst_id}-{uuid.uuid4().hex[:4].upper()}"
        tier = random.randint(0, 4)
        power = tier * 80
        status = statuses[i]
        is_escrowed = 1 if status == "ACTIVE" else 0
        
        item_rows.append((inst_id, tid, owner_id, serial, tier, power, 1, 100, is_escrowed))
        
        seller_id = owner_id
        realm_id = random.randint(1, 5)
        start_price = random.randint(1000, 150000)
        buyout_price = int(start_price * random.uniform(1.2, 1.8))
        curr_bid = int(start_price * 1.05) if status == "ACTIVE" and random.random() < 0.3 else 0
        high_bidder = random.randint(base_player_id, base_player_id + target_players - 1) if curr_bid > 0 else None
        
        dt_past = (now - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d %H:%M:%S")
        dt_exp = (now + timedelta(hours=random.randint(6, 48))).strftime("%Y-%m-%d %H:%M:%S")
        
        listing_rows.append((list_id, inst_id, seller_id, realm_id, "AUCTION", start_price, buyout_price, curr_bid, high_bidder, status, dt_past, dt_exp))

    batch_size = 5000
    with get_db_cursor(immediate=True) as cur:
        for i in range(0, len(item_rows), batch_size):
            b_items = item_rows[i:i + batch_size]
            b_lists = listing_rows[i:i + batch_size]
            
            cur.executemany(
                """
                INSERT OR IGNORE INTO inventory_items (instance_id, item_id, owner_id, mint_serial, temper_tier, bonus_power, stack_size, current_durability, is_escrowed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """ if not is_postgres() else """
                INSERT INTO inventory_items (instance_id, item_id, owner_id, mint_serial, temper_tier, bonus_power, stack_size, current_durability, is_escrowed)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (instance_id) DO NOTHING;
                """,
                b_items,
            )
            cur.executemany(
                """
                INSERT OR IGNORE INTO auction_listings (listing_id, instance_id, seller_id, realm_id, listing_type, start_price, buyout_price, current_bid, high_bidder_id, status, listed_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """ if not is_postgres() else """
                INSERT INTO auction_listings (listing_id, instance_id, seller_id, realm_id, listing_type, start_price, buyout_price, current_bid, high_bidder_id, status, listed_at, expires_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (listing_id) DO NOTHING;
                """,
                b_lists,
            )

    elapsed = round(time.perf_counter() - t0, 2)
    print(f"[+] Successfully seeded {target_listings:,} listings ({active_count:,} active, {historical_count:,} historical) in {elapsed}s.")

    # 3. Benchmark partial index scan vs full table scan at scale
    print("\n" + "=" * 72)
    print("  EXPLAIN QUERY PLAN: PARTIAL INDEX EVALUATION AT SCALE")
    print("=" * 72)
    with get_db_cursor() as cur:
        query_sql = """
            SELECT al.listing_id, it.item_name, al.buyout_price, r.realm_name
            FROM auction_listings al
            JOIN inventory_items ii ON ii.instance_id = al.instance_id
            JOIN item_templates it ON it.item_id = ii.item_id
            JOIN realms r ON r.realm_id = al.realm_id
            WHERE al.status = 'ACTIVE'
            ORDER BY al.buyout_price ASC
            LIMIT 50;
        """
        t_bench0 = time.perf_counter()
        cur.execute(query_sql)
        res_rows = cur.fetchall()
        t_active_ms = (time.perf_counter() - t_bench0) * 1000

        cur.execute("EXPLAIN QUERY PLAN " + query_sql if not is_postgres() else "EXPLAIN " + query_sql)
        plan = cur.fetchall()
        print(f"[*] Query on ACTIVE listings ({active_count:,} out of {target_listings:,} rows) took {t_active_ms:.2f} ms:")
        for step in plan:
            print(f"    -> {step['detail'] if hasattr(step, 'keys') and 'detail' in step.keys() else step[0]}")

    print("=" * 72)
    print("  SCALE SEEDING & BENCHMARK COMPLETE!")
    print("=" * 72)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed large-scale relational dataset for Scrolls of Agora")
    parser.add_argument("--listings", type=int, default=10000, help="Number of auction listings to generate")
    parser.add_argument("--players", type=int, default=2000, help="Number of player records to generate")
    args = parser.parse_args()

    generate_scale_data(target_listings=args.listings, target_players=args.players)

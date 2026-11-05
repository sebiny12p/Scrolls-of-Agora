-- ============================================================================
-- SCROLLS OF AGORA: INITIAL MMORPG WORLD & MARKET ECONOMY SEED DATA
-- ============================================================================

BEGIN;

-- 1. REALMS / DECENTRALIZED TRADING HUBS
INSERT INTO realms (realm_id, realm_name, region, population_cap, tax_rate_bps) VALUES
    (1, 'Mournhold-Grand-Kiosk', 'EU-CENTRAL', 15000, 500),   -- 5.00% kiosk cut
    (2, 'Vivec-Canton-Exchange', 'EU-WEST',    12000, 750),   -- 7.50% cut (high-volatility hub)
    (3, 'Wayrest-Royal-Bazaar',  'NA-EAST',    10000, 350);   -- 3.50% cut (merchant haven)

-- 2. PLAYERS & AUTONOMOUS MARKET TRADERS
INSERT INTO players (player_id, username, realm_id, faction, character_class, level, gold_balance, escrow_gold, reputation_score) VALUES
    (1001, 'Kaelen_Sunstrider', 1, 'Vanguard',   'Templar',     100, 485000, 12500, 980),
    (1002, 'Sylvan_Whisper',    1, 'Syndicate',  'Nightblade',  100, 920000,     0, 845),
    (1003, 'Gorim_Ironforge',   1, 'Vanguard',   'Dragonknight', 95, 310000,     0, 995),
    (1004, 'Vexia_Nightbane',   2, 'Syndicate',  'Arcanist',    100, 675000, 45000, 620),
    (1005, 'Aurelius_Goldhand', 1, 'Outlanders', 'Sorcerer',    100, 2150000,    0, 1250),
    (1006, 'Lyra_Starweaver',   3, 'Vanguard',   'Warden',       88, 195000,     0, 910),
    (1007, 'Drax_Bloodfang',    2, 'Syndicate',  'Berserker',    98, 142000,     0, 540),
    (1008, 'Zul_RMT_Mule_99',   2, 'Outlanders', 'Rogue',         5,  15000,     0,  15),
    (1009, 'Thorne_Alchemist',  1, 'Outlanders', 'Apothecary',   92, 540000,     0, 890),
    (1010, 'Nyx_Voidwalker',    1, 'Syndicate',  'Necromancer', 100, 780000,     0, 775);

-- 3. ITEM TEMPLATES (Supertype)
INSERT INTO item_templates (item_id, item_name, category, rarity, base_vendor_value, max_stack, required_level) VALUES
    (5001, 'Ashbringer, Blade of the Sovereign', 'Weapon',     'Mythic',    25000,   1, 100),
    (5002, 'Aegis of the Fallen Tribunal',       'Armor',      'Legendary', 15000,   1,  95),
    (5003, 'Mehrunes'' Razor of Malice',         'Weapon',     'Legendary', 12000,   1,  90),
    (5004, 'Crown of Eternal Frost',             'Armor',      'Epic',       4500,   1,  85),
    (5005, 'Ebonheart Dragonscale Cuirass',      'Armor',      'Epic',       5200,   1,  85),
    (5006, 'Signet Ring of the Psijic Order',    'Armor',      'Epic',       3800,   1,  80),
    (5007, 'Runed Glass Greatsword',             'Weapon',     'Rare',       1200,   1,  60),
    (5008, 'Flask of Supreme Spell Power',       'Consumable', 'Epic',        180,  20,  80),
    (5009, 'Elixir of True Sight',               'Consumable', 'Rare',         65,  50,  50),
    (5010, 'Draught of Aetherial Magicka',       'Consumable', 'Uncommon',     25, 100,  30),
    (5011, 'Dreugh Wax Tempering Resin',         'Reagent',    'Epic',        400, 200,   1),
    (5012, 'Aetherial Chromium Grains',          'Reagent',    'Rare',        110, 500,   1),
    (5013, 'Cracked Goblinshiv (Grey Junk)',     'Weapon',     'Common',        5,   1,   1),
    (5014, 'Elder Scroll of Chim (Relic)',       'Artifact',   'Mythic',    50000,   1, 100);

-- 4A. EQUIPMENT SPECS (Subtype 1)
INSERT INTO equipment_specs (item_id, equip_slot, attack_power, armor_rating, max_durability, socket_count) VALUES
    (5001, 'MainHand', 1480,   0, 150, 3),
    (5002, 'OffHand',     0, 950, 140, 2),
    (5003, 'MainHand',  980,   0, 110, 2),
    (5004, 'Helm',       85, 420, 100, 2),
    (5005, 'Chest',      40, 680, 135, 3),
    (5006, 'Ring',      210,  50,  80, 1),
    (5007, 'MainHand',  460,   0, 100, 1),
    (5013, 'MainHand',    4,   0,  20, 0);

-- 4B. CONSUMABLE SPECS (Subtype 2)
INSERT INTO consumable_specs (item_id, effect_type, effect_potency, duration_seconds, cooldown_seconds) VALUES
    (5008, 'BerserkBuff',  450, 3600, 60),
    (5009, 'StealthElixir',120, 1800, 45),
    (5010, 'ManaRestore', 2500,    0, 30);

-- 5. ENCHANTMENTS
INSERT INTO enchantments (enchant_id, enchant_name, stat_type, bonus_value, tier) VALUES
    (1, 'Glyph of Prismatic Onslaught', 'Lifesteal',  150, 5),
    (2, 'Whispering Void Infusion',     'VoidDamage', 220, 5),
    (3, 'Glyph of Weapon Berserking',   'CritStrike', 140, 4),
    (4, 'Prismatic Quickness',          'Haste',       95, 3),
    (5, 'Tribunal Bulwark Plating',     'Thorns',     110, 4);

-- 6. INVENTORY ITEMS (Physical Minted Instances with Unique Anti-Dupe Serials)
INSERT INTO inventory_items (instance_id, item_id, owner_id, mint_serial, stack_size, current_durability, is_escrowed) VALUES
    (9001, 5001, 1003, 'AGORA-ASH-0001-9F8A7B', 1,   150, TRUE),
    (9002, 5002, 1001, 'AGORA-AEG-0002-3C4D1E', 1,   140, TRUE),
    (9003, 5003, 1002, 'AGORA-VFD-0003-7A2B9C', 1,   110, TRUE),
    (9004, 5004, 1005, 'AGORA-CEF-0004-1D5E8F', 1,   100, TRUE),
    (9005, 5005, 1003, 'AGORA-DSC-0005-6B3F0A', 1,   135, TRUE),
    (9006, 5008, 1009, 'AGORA-FST-0006-4E9C2D', 20,  100, TRUE),
    (9007, 5008, 1004, 'AGORA-FST-0007-8A1F5B', 20,  100, TRUE),
    (9008, 5011, 1009, 'AGORA-ANC-0008-2C7D4E', 50,  100, TRUE),
    (9009, 5011, 1007, 'AGORA-ANC-0009-5F0B3A', 50,  100, TRUE),
    (9010, 5006, 1010, 'AGORA-SRA-0010-9D4A6C', 1,    80, TRUE),
    -- Historical Sold Items (Now owned by buyers)
    (9011, 5001, 1005, 'AGORA-ASH-0011-SOLD01', 1,   150, FALSE),
    (9012, 5003, 1001, 'AGORA-VFD-0012-SOLD02', 1,   110, FALSE),
    (9013, 5005, 1002, 'AGORA-DSC-0013-SOLD03', 1,   135, FALSE),
    (9014, 5013, 1004, 'AGORA-JNK-0014-RMT999', 1,    15, FALSE),
    (9015, 5007, 1006, 'AGORA-RMG-0015-SOLD05', 1,   100, FALSE);

-- 7. ITEM INSTANCE ENCHANTMENTS (M:N Junction)
INSERT INTO item_instance_enchantments (instance_id, enchant_id) VALUES
    (9001, 1), (9001, 2),
    (9002, 5),
    (9003, 2), (9003, 3),
    (9004, 4),
    (9011, 1), (9011, 3);

-- 8. AUCTION LISTINGS (Active Orderbook + Settled Historical Listings)
INSERT INTO auction_listings (
    listing_id, instance_id, seller_id, realm_id, listing_type,
    start_price, buyout_price, current_bid, high_bidder_id, status, listed_at, expires_at
) VALUES
    (101, 9001, 1003, 1, 'AUCTION',     140000, 185000, 145000, 1004, 'ACTIVE', CURRENT_TIMESTAMP - INTERVAL '4 hours', CURRENT_TIMESTAMP + INTERVAL '20 hours'),
    (102, 9002, 1001, 1, 'AUCTION',      72000,  95000,  75000, 1002, 'ACTIVE', CURRENT_TIMESTAMP - INTERVAL '6 hours', CURRENT_TIMESTAMP + INTERVAL '18 hours'),
    (103, 9003, 1002, 1, 'BUYOUT_ONLY',  64000,  64000,      0, NULL, 'ACTIVE', CURRENT_TIMESTAMP - INTERVAL '2 hours', CURRENT_TIMESTAMP + INTERVAL '22 hours'),
    (104, 9004, 1005, 1, 'AUCTION',      18000,  24500,  19500, 1006, 'ACTIVE', CURRENT_TIMESTAMP - INTERVAL '5 hours', CURRENT_TIMESTAMP + INTERVAL '19 hours'),
    (105, 9005, 1003, 1, 'BUYOUT_ONLY',  29000,  29000,      0, NULL, 'ACTIVE', CURRENT_TIMESTAMP - INTERVAL '1 hour',  CURRENT_TIMESTAMP + INTERVAL '23 hours'),
    (106, 9006, 1009, 1, 'BUYOUT_ONLY',   6800,   6800,      0, NULL, 'ACTIVE', CURRENT_TIMESTAMP - INTERVAL '3 hours', CURRENT_TIMESTAMP + INTERVAL '21 hours'),
    (107, 9007, 1004, 2, 'BUYOUT_ONLY',  11200,  11200,      0, NULL, 'ACTIVE', CURRENT_TIMESTAMP - INTERVAL '2 hours', CURRENT_TIMESTAMP + INTERVAL '22 hours'),
    (108, 9008, 1009, 1, 'BUYOUT_ONLY',  22000,  22000,      0, NULL, 'ACTIVE', CURRENT_TIMESTAMP - INTERVAL '3 hours', CURRENT_TIMESTAMP + INTERVAL '21 hours'),
    (109, 9009, 1007, 2, 'BUYOUT_ONLY',  34500,  34500,      0, NULL, 'ACTIVE', CURRENT_TIMESTAMP - INTERVAL '1 hour',  CURRENT_TIMESTAMP + INTERVAL '23 hours'),
    (110, 9010, 1010, 1, 'AUCTION',      14000,  19000,      0, NULL, 'ACTIVE', CURRENT_TIMESTAMP - INTERVAL '30 mins', CURRENT_TIMESTAMP + INTERVAL '23 hours'),
    (201, 9011, 1001, 1, 'BUYOUT_ONLY', 175000, 175000, 175000, 1005, 'SOLD',   CURRENT_TIMESTAMP - INTERVAL '3 days',  CURRENT_TIMESTAMP - INTERVAL '2 days'),
    (202, 9012, 1005, 1, 'AUCTION',      55000,  68000,  68000, 1001, 'SOLD',   CURRENT_TIMESTAMP - INTERVAL '2 days',  CURRENT_TIMESTAMP - INTERVAL '1 day'),
    (203, 9013, 1003, 1, 'BUYOUT_ONLY',  31000,  31000,  31000, 1002, 'SOLD',   CURRENT_TIMESTAMP - INTERVAL '2 days',  CURRENT_TIMESTAMP - INTERVAL '1 day'),
    (204, 9014, 1008, 2, 'BUYOUT_ONLY', 250000, 250000, 250000, 1004, 'SOLD',   CURRENT_TIMESTAMP - INTERVAL '1 day',   CURRENT_TIMESTAMP - INTERVAL '12 hours'),
    (205, 9015, 1002, 3, 'BUYOUT_ONLY',   8500,   8500,   8500, 1006, 'SOLD',   CURRENT_TIMESTAMP - INTERVAL '12 hours',CURRENT_TIMESTAMP - INTERVAL '2 hours');

-- 9. AUCTION BIDS
INSERT INTO auction_bids (listing_id, bidder_id, bid_amount, placed_at) VALUES
    (101, 1002, 140000, CURRENT_TIMESTAMP - INTERVAL '3 hours'),
    (101, 1004, 145000, CURRENT_TIMESTAMP - INTERVAL '1 hour'),
    (102, 1002,  75000, CURRENT_TIMESTAMP - INTERVAL '2 hours'),
    (104, 1006,  19500, CURRENT_TIMESTAMP - INTERVAL '90 mins');

-- 10. LEDGER TRANSACTIONS (Settled Double-Entry Records)
INSERT INTO ledger_transactions (
    tx_id, listing_id, instance_id, seller_id, buyer_id,
    gross_price, market_tax_burned, seller_net_payout, settlement_type, executed_at
) VALUES
    (501, 201, 9011, 1001, 1005, 175000,  8750, 166250, 'INSTANT_BUYOUT', CURRENT_TIMESTAMP - INTERVAL '2 days'),
    (502, 202, 9012, 1005, 1001,  68000,  3400,  64600, 'AUCTION_WON',    CURRENT_TIMESTAMP - INTERVAL '1 day'),
    (503, 203, 9013, 1003, 1002,  31000,  1550,  29450, 'INSTANT_BUYOUT', CURRENT_TIMESTAMP - INTERVAL '1 day'),
    (504, 204, 9014, 1008, 1004, 250000, 18750, 231250, 'INSTANT_BUYOUT', CURRENT_TIMESTAMP - INTERVAL '12 hours'),
    (505, 205, 9015, 1002, 1006,   8500,   297,   8203, 'INSTANT_BUYOUT', CURRENT_TIMESTAMP - INTERVAL '2 hours');

-- 11. OHLCV PRICE HISTORY CANDLES
INSERT INTO price_history_ohlc (item_id, realm_id, bucket_timestamp, open_price, high_price, low_price, close_price, volume_traded) VALUES
    (5001, 1, CURRENT_TIMESTAMP - INTERVAL '6 days', 160000, 172000, 158000, 169000, 3),
    (5001, 1, CURRENT_TIMESTAMP - INTERVAL '5 days', 169000, 178000, 165000, 174000, 4),
    (5001, 1, CURRENT_TIMESTAMP - INTERVAL '4 days', 174000, 181000, 170000, 172000, 2),
    (5001, 1, CURRENT_TIMESTAMP - INTERVAL '3 days', 172000, 185000, 171000, 180000, 5),
    (5001, 1, CURRENT_TIMESTAMP - INTERVAL '2 days', 180000, 189000, 175000, 175000, 3),
    (5001, 1, CURRENT_TIMESTAMP - INTERVAL '1 day',  175000, 192000, 174000, 185000, 6);

-- Synchronize PostgreSQL sequences
SELECT setval('realms_realm_id_seq', 3, true);
SELECT setval('players_player_id_seq', 1010, true);
SELECT setval('item_templates_item_id_seq', 5014, true);
SELECT setval('enchantments_enchant_id_seq', 5, true);
SELECT setval('inventory_items_instance_id_seq', 9015, true);
SELECT setval('auction_listings_listing_id_seq', 205, true);
SELECT setval('ledger_transactions_tx_id_seq', 505, true);

COMMIT;

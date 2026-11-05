-- ============================================================================
-- SCROLLS OF AGORA: INITIAL SEED DATA (SQLite WAL Engine)
-- 5 Decentralized Trading Hubs, Syndicates, Mythic Relics, Bag Items, OHLC & RMT Chain
-- ============================================================================

-- 1. TRADE GUILDS
INSERT INTO trade_guilds (guild_id, guild_name, alliance, banner_crest, treasury_gold, tax_dividend_earned) VALUES
    (1, 'Wayrest Merchant Consortium', 'Daggerfall Covenant',  'lion',   4200000, 185000),
    (2, 'Dominion Golden Bough',       'Aldmeri Dominion',     'eagle',  3850000, 142000),
    (3, 'Mournhold Tribunal Factorum', 'Ebonheart Pact',       'dragon', 5100000, 260000),
    (4, 'Tel Var Obsidian Syndicate',  'Independent Syndicate','telvar', 6400000, 390000),
    (5, 'Baandari Pedlars Caravan',    'Independent Syndicate','moon',   4750000, 215000);

-- 2. THE 5 TAMRIEL TRADING HUBS
INSERT INTO realms (realm_id, realm_name, province, region, map_x, map_y, controlling_guild_id, population_cap, tax_rate_bps) VALUES
    (1, 'Wayrest',       'Stormhaven, High Rock', 'HIGH-ROCK',     18, 22, 1, 14000, 450),
    (2, 'Elden Root',    'Grahtwood, Valenwood',  'VALENWOOD',     44, 82, 2, 14500, 400),
    (3, 'Mournhold',     'Deshaan, Morrowind',    'MORROWIND',     84, 48, 3, 16000, 500),
    (4, 'Imperial City', 'Cyrodiil Heartland',    'CYRODIIL',      56, 44, 4, 10000, 800),
    (5, 'Rawl''kha',     'Reaper''s March',       'REAPERS-MARCH', 24, 56, 5, 15500, 350);

-- 3. SEALED WEEKLY KIOSK BIDS
INSERT INTO kiosk_bids (kiosk_bid_id, realm_id, guild_id, bid_gold, status, placed_at) VALUES
    (1, 3, 3, 850000,  'SEALED', datetime('now', '-2 days')),
    (2, 3, 4, 920000,  'SEALED', datetime('now', '-1 days')),
    (3, 1, 1, 640000,  'SEALED', datetime('now', '-3 days')),
    (4, 5, 5, 780000,  'SEALED', datetime('now', '-12 hours')),
    (5, 4, 4, 1150000, 'SEALED', datetime('now', '-6 hours'));

-- 4. PLAYERS & MULE RING ACCOUNTS
INSERT INTO players (player_id, username, realm_id, guild_id, faction, character_class, level, gold_balance, escrow_gold, reputation_score, is_banned, created_at) VALUES
    (1001, 'Kaelen_Sunstrider', 1, 1, 'Vanguard',   'Templar',      100,  685000,  75000,  980, 0, datetime('now', '-90 days')),
    (1002, 'Sylvan_Whisper',    2, 2, 'Syndicate',  'Nightblade',   100,  920000,      0,  845, 0, datetime('now', '-85 days')),
    (1003, 'Gorim_Ironforge',   3, 3, 'Vanguard',   'Dragonknight',  95,  510000,      0,  995, 0, datetime('now', '-70 days')),
    (1004, 'Vexia_Nightbane',   4, 4, 'Syndicate',  'Arcanist',     100,  875000, 145000,  620, 0, datetime('now', '-60 days')),
    (1005, 'Aurelius_Goldhand', 3, 3, 'Outlanders', 'Sorcerer',     100, 2450000,      0, 1250, 0, datetime('now', '-50 days')),
    (1006, 'Lyra_Starweaver',   2, 2, 'Vanguard',   'Warden',        88,  395000,  19500,  910, 0, datetime('now', '-45 days')),
    (1007, 'Razum_Dar_Trader',  5, 5, 'Outlanders', 'Nightblade',    98,  742000,      0,  940, 0, datetime('now', '-40 days')),
    (1008, 'Zul_Bot_Harvester', 5, NULL, 'Outlanders', 'Rogue',       5,   12000,      0,   15, 0, datetime('now', '-5 days')),
    (1009, 'Thorne_Alchemist',  2, 2, 'Outlanders', 'Apothecary',    92,  640000,      0,  890, 0, datetime('now', '-35 days')),
    (1010, 'Nyx_Voidwalker',    4, 4, 'Syndicate',  'Necromancer',  100,  880000,      0,  775, 0, datetime('now', '-30 days')),
    (1011, 'Skooma_Launder_02', 1, NULL, 'Syndicate',  'Rogue',       8,   45000,      0,   10, 0, datetime('now', '-4 days')),
    (1012, 'RMT_Syndicate_Boss',4, NULL, 'Syndicate',  'Arcanist',   15,  985000,      0,    5, 0, datetime('now', '-3 days'));

-- 5. ITEM TEMPLATES
INSERT INTO item_templates (item_id, item_name, icon_key, lore_text, category, rarity, base_vendor_value, max_stack, required_level) VALUES
    (5001, 'Ashbringer, Blade of the Sovereign', 'runeblade',  'Forged in the heart of a dying star. Sears undead flesh on contact.', 'Weapon',     'Mythic',    25000,   1, 100),
    (5002, 'Aegis of the Fallen Tribunal',       'shield',     'Impenetrable bulwark recovered from the Clockwork Citadel in Mournhold.', 'Armor',  'Legendary', 15000,   1,  95),
    (5003, 'Mehrunes'' Razor of Malice',         'dagger',     'Daedric princes whisper through its serrated obsidian edge.', 'Weapon',              'Legendary', 12000,   1,  90),
    (5004, 'Crown of the White-Gold Tower',      'crown',      'Imperial battlemage circlet looted from the central districts of Cyrodiil.', 'Armor','Epic',       4500,   1,  85),
    (5005, 'Ebonheart Dragonscale Cuirass',      'chestplate', 'Tempered volcanic dragon scales impervious to ballista fire.', 'Armor',              'Epic',       5200,   1,  85),
    (5006, 'Signet Ring of the Psijic Order',    'ring',       'Inscribed with time-bending wards of the Artaeum conclave.', 'Armor',                'Epic',       3800,   1,  80),
    (5007, 'Wayrest Royal Knight Claymore',      'greatsword', 'High-carbon Breton steel greatsword of Stormhaven''s vanguard.', 'Weapon',           'Rare',       1200,   1,  60),
    (5008, 'Flask of Supreme Spell Power',       'flask',      'Distilled Elden Root sap granting +450 Spell Damage for 1 hour.', 'Consumable',      'Epic',        180,  20,  80),
    (5009, 'Rawl''kha Moon-Sugar Elixir',        'potion',     'Khajiiti alchemical brew that reveals stealthed Nightblades in Cyrodiil.', 'Consumable','Rare',      65,  50,  50),
    (5010, 'Draught of Aetherial Magicka',       'vial',       'Restores depleted magicka reserves during veteran trial encounters.', 'Consumable',  'Uncommon',     25, 100,  30),
    (5011, 'Dreugh Wax Tempering Resin',         'crystal',    'Legendary gold-grade upgrade resin used at the Arcane Tempering Forge.', 'Reagent',  'Epic',        400, 200,   1),
    (5012, 'Aetherial Chromium Plating',         'ore',        'Refined iridescent grains required to temper jewelry & weapons.', 'Reagent',         'Rare',        110, 500,   1),
    (5013, 'Cracked Goblinshiv',                  'dagger',     'A notched iron dagger salvaged from a goblin den, frequently traded in illicit black-market circles.', 'Weapon','Common',     5,   1,   1),
    (5014, 'Elder Scroll of Chim',               'artifact',   'Aedric prophecy parchment pulsing with uncontained temporal power.', 'Artifact',     'Mythic',    50000,   1, 100);

-- 6A. EQUIPMENT SPECS
INSERT INTO equipment_specs (item_id, equip_slot, attack_power, armor_rating, max_durability, socket_count) VALUES
    (5001, 'MainHand', 1480,   0, 150, 3),
    (5002, 'OffHand',     0, 950, 140, 2),
    (5003, 'MainHand',  980,   0, 110, 2),
    (5004, 'Helm',       85, 420, 100, 2),
    (5005, 'Chest',      40, 680, 135, 3),
    (5006, 'Ring',      210,  50,  80, 1),
    (5007, 'MainHand',  460,   0, 100, 1),
    (5013, 'MainHand',    4,   0,  20, 0);

-- 6B. CONSUMABLE SPECS
INSERT INTO consumable_specs (item_id, effect_type, effect_potency, duration_seconds, cooldown_seconds) VALUES
    (5008, 'BerserkBuff',   450, 3600, 60),
    (5009, 'StealthElixir', 120, 1800, 45),
    (5010, 'ManaRestore',  2500,    0, 30);

-- 7. ENCHANTMENTS
INSERT INTO enchantments (enchant_id, enchant_name, stat_type, bonus_value, tier) VALUES
    (1, 'Glyph of Prismatic Onslaught', 'Lifesteal',  150, 5),
    (2, 'Glyph of Oblivion Void',       'VoidDamage', 220, 5),
    (3, 'Glyph of Weapon Berserking',   'CritStrike', 140, 4),
    (4, 'Glyph of Arcane Quickness',    'Haste',       95, 3),
    (5, 'Glyph of Tribunal Bulwark',    'Thorns',     110, 4);

-- 8. INVENTORY ITEMS (Physical Instances)
INSERT INTO inventory_items (instance_id, item_id, owner_id, mint_serial, temper_tier, bonus_power, stack_size, current_durability, is_escrowed, minted_at) VALUES
    (9001, 5001, 1003, 'AGORA-ASH-0001-9F8A7B', 3, 240,  1, 150, 1, datetime('now', '-20 days')),
    (9002, 5002, 1001, 'AGORA-AEG-0002-3C4D1E', 2, 120,  1, 140, 1, datetime('now', '-18 days')),
    (9003, 5003, 1007, 'AGORA-RAZ-0003-7A2B9C', 1,  80,  1, 110, 1, datetime('now', '-16 days')),
    (9004, 5004, 1004, 'AGORA-CWN-0004-1D5E8F', 1,  60,  1, 100, 1, datetime('now', '-14 days')),
    (9005, 5005, 1003, 'AGORA-DSC-0005-6B3F0A', 2, 110,  1, 135, 1, datetime('now', '-12 days')),
    (9006, 5008, 1009, 'AGORA-FLK-0006-4E9C2D', 0,   0, 20, 100, 1, datetime('now', '-10 days')),
    (9007, 5008, 1004, 'AGORA-FLK-0007-8A1F5B', 0,   0, 20, 100, 1, datetime('now', '-8 days')),
    (9008, 5011, 1007, 'AGORA-WAX-0008-2C7D4E', 0,   0, 50, 100, 1, datetime('now', '-7 days')),
    (9009, 5011, 1001, 'AGORA-WAX-0009-5F0B3A', 0,   0, 50, 100, 1, datetime('now', '-6 days')),
    (9010, 5006, 1002, 'AGORA-RNG-0010-1B2C3D', 1,  45,  1,  80, 1, datetime('now', '-5 days')),
    (9011, 5007, 1001, 'AGORA-SWD-0011-4E5F6A', 0,   0,  1, 100, 1, datetime('now', '-4 days')),
    (9012, 5009, 1007, 'AGORA-POT-0012-7B8C9D', 0,   0, 30, 100, 1, datetime('now', '-3 days')),
    -- Player Bag items (Aurelius_Goldhand - player 1005)
    (9013, 5003, 1005, 'AGORA-RAZ-0013-0A1B2C', 0,   0,  1, 110, 0, datetime('now', '-2 days')),
    (9014, 5004, 1005, 'AGORA-CWN-0014-3D4E5F', 1,  75,  1, 100, 0, datetime('now', '-2 days')),
    (9015, 5005, 1005, 'AGORA-DSC-0015-6A7B8C', 0,   0,  1, 135, 0, datetime('now', '-2 days')),
    (9016, 5011, 1005, 'AGORA-WAX-0016-9D0E1F', 0,   0, 14, 100, 0, datetime('now', '-2 days')),
    (9017, 5012, 1005, 'AGORA-CHR-0017-2A3B4C', 0,   0,  8, 100, 0, datetime('now', '-2 days')),
    (9018, 5008, 1005, 'AGORA-FLK-0018-5D6E7F', 0,   0,  5, 100, 0, datetime('now', '-2 days')),
    (9019, 5010, 1005, 'AGORA-POT-0019-8A9B0C', 0,   0, 25, 100, 0, datetime('now', '-2 days')),
    -- Mule Ring Instances
    (9020, 5013, 1008, 'AGORA-WSH-0020-0011AA', 0,   0,  1,  20, 0, datetime('now', '-4 days')),
    (9021, 5013, 1011, 'AGORA-WSH-0021-0022BB', 0,   0,  1,  20, 0, datetime('now', '-2 days'));

-- 9. AUCTION LISTINGS (Active Listings 101-112 + Historical Settled Listings 201-206)
INSERT INTO auction_listings (listing_id, instance_id, seller_id, realm_id, listing_type, start_price, buyout_price, current_bid, high_bidder_id, status, listed_at, expires_at) VALUES
    (101, 9001, 1003, 3, 'AUCTION',    165000, 245000, 175000, 1005, 'ACTIVE', datetime('now', '-18 hours'), datetime('now', '+6 hours')),
    (102, 9002, 1001, 1, 'BUYOUT_ONLY', 88000,  88000,      0, NULL, 'ACTIVE', datetime('now', '-12 hours'), datetime('now', '+12 hours')),
    (103, 9003, 1007, 5, 'AUCTION',     54000,  79000,  58000, 1004, 'ACTIVE', datetime('now', '-10 hours'), datetime('now', '+14 hours')),
    (104, 9004, 1004, 4, 'BUYOUT_ONLY', 28000,  28000,      0, NULL, 'ACTIVE', datetime('now', '-8 hours'),  datetime('now', '+16 hours')),
    (105, 9005, 1003, 3, 'AUCTION',     31000,  46000,      0, NULL, 'ACTIVE', datetime('now', '-6 hours'),  datetime('now', '+18 hours')),
    (106, 9006, 1009, 2, 'BUYOUT_ONLY',  7200,   7200,      0, NULL, 'ACTIVE', datetime('now', '-5 hours'),  datetime('now', '+19 hours')),
    (107, 9007, 1004, 4, 'BUYOUT_ONLY', 12800,  12800,      0, NULL, 'ACTIVE', datetime('now', '-4 hours'),  datetime('now', '+20 hours')),
    (108, 9008, 1007, 5, 'BUYOUT_ONLY', 19500,  19500,      0, NULL, 'ACTIVE', datetime('now', '-3 hours'),  datetime('now', '+21 hours')),
    (109, 9009, 1001, 1, 'BUYOUT_ONLY', 34500,  34500,      0, NULL, 'ACTIVE', datetime('now', '-2 hours'),  datetime('now', '+22 hours')),
    (110, 9010, 1002, 2, 'AUCTION',     14000,  22000,      0, NULL, 'ACTIVE', datetime('now', '-90 minutes'),datetime('now', '+23 hours')),
    (111, 9011, 1001, 1, 'BUYOUT_ONLY',  4800,   4800,      0, NULL, 'ACTIVE', datetime('now', '-60 minutes'),datetime('now', '+23 hours')),
    (112, 9012, 1007, 5, 'BUYOUT_ONLY',  1850,   1850,      0, NULL, 'ACTIVE', datetime('now', '-30 minutes'),datetime('now', '+23 hours')),
    -- Historical Closed Listings (Separated from Active Kiosk Orderbook)
    (201, 9020, 1003, 3, 'BUYOUT_ONLY', 210000, 210000, 210000, 1001, 'SOLD', datetime('now', '-7 days'), datetime('now', '-6 days')),
    (202, 9021, 1001, 1, 'BUYOUT_ONLY',  85000,  85000,  85000, 1005, 'SOLD', datetime('now', '-5 days'), datetime('now', '-4 days')),
    (203, 9020, 1004, 4, 'BUYOUT_ONLY',  26500,  26500,  26500, 1002, 'SOLD', datetime('now', '-3 days'), datetime('now', '-2 days')),
    (204, 9020, 1008, 5, 'BUYOUT_ONLY', 320000, 320000, 320000, 1011, 'SOLD', datetime('now', '-3 days'), datetime('now', '-2 days')),
    (205, 9021, 1011, 4, 'BUYOUT_ONLY', 310000, 310000, 310000, 1012, 'SOLD', datetime('now', '-2 days'), datetime('now', '-1 days')),
    (206, 9020, 1012, 1, 'BUYOUT_ONLY', 305000, 305000, 305000, 1004, 'SOLD', datetime('now', '-1 days'), datetime('now', '-12 hours'));

-- 10. IMMUTABLE LEDGER TRANSACTIONS (Settled Sales & RMT Mule Chain)
INSERT INTO ledger_transactions (tx_id, listing_id, instance_id, seller_id, buyer_id, gross_price, market_tax_burned, seller_net_payout, settlement_type, executed_at) VALUES
    (7001, 201, 9020, 1003, 1001, 210000, 10500, 199500, 'INSTANT_BUYOUT', datetime('now', '-7 days')),
    (7002, 202, 9021, 1001, 1005,  85000,  3825,  81175, 'AUCTION_WON',    datetime('now', '-5 days')),
    (7003, 203, 9020, 1004, 1002,  26500,  2120,  24380, 'INSTANT_BUYOUT', datetime('now', '-3 days')),
    -- The 3-Hop RMT Mule Chain
    (7004, 204, 9020, 1008, 1011, 320000, 16000, 304000, 'INSTANT_BUYOUT', datetime('now', '-3 days')),
    (7005, 205, 9021, 1011, 1012, 310000, 15500, 294500, 'INSTANT_BUYOUT', datetime('now', '-2 days')),
    (7006, 206, 9020, 1012, 1004, 305000, 24400, 280600, 'INSTANT_BUYOUT', datetime('now', '-1 days'));

-- 11. OHLC PRICE HISTORY (Sample 24-hour candles)
INSERT INTO price_history_ohlc (item_id, realm_id, bucket_timestamp, open_price, high_price, low_price, close_price, volume_traded) VALUES
    (5001, 3, '18:00', 165000, 172000, 162000, 170000, 5),
    (5001, 3, '19:00', 170000, 175000, 168000, 174000, 6),
    (5001, 3, '20:00', 174000, 180000, 171000, 178000, 8),
    (5002, 1, '18:00',  85000,  89000,  83000,  87000, 4),
    (5002, 1, '19:00',  87000,  91000,  86000,  89000, 3),
    (5002, 1, '20:00',  89000,  93000,  88000,  92000, 7),
    (5011, 5, '18:00',  18000,  19500,  17500,  19000, 14),
    (5011, 5, '19:00',  19000,  20500,  18800,  19800, 18),
    (5011, 5, '20:00',  19800,  21000,  19400,  20500, 22),
    (5014, 4, '18:00', 300000, 320000, 295000, 310000, 2),
    (5014, 4, '19:00', 310000, 325000, 308000, 318000, 3),
    (5014, 4, '20:00', 318000, 335000, 315000, 325000, 4);

-- 12. INITIAL DOUBLE-ENTRY JOURNAL BALANCES (Historical Seed Settlements)
INSERT INTO ledger_journal (tx_group_id, event_type, account_type, account_id, amount, description) VALUES
    ('TX-SEED-7001', 'BUYOUT', 'PLAYER_LIQUID', '1001', -210000, 'Buyout debit: Item #9020'),
    ('TX-SEED-7001', 'BUYOUT', 'PLAYER_LIQUID', '1003',  199500, 'Seller payout: Item #9020'),
    ('TX-SEED-7001', 'BUYOUT', 'GUILD_TREASURY', '3',     5250, 'Kiosk cut dividend: Mournhold'),
    ('TX-SEED-7001', 'BUYOUT', 'SYSTEM_SINK', 'MKT_TAX',   5250, 'Kiosk tax burn: Mournhold'),

    ('TX-SEED-7002', 'BUYOUT', 'PLAYER_LIQUID', '1005',  -85000, 'Buyout debit: Item #9021'),
    ('TX-SEED-7002', 'BUYOUT', 'PLAYER_LIQUID', '1001',   81175, 'Seller payout: Item #9021'),
    ('TX-SEED-7002', 'BUYOUT', 'GUILD_TREASURY', '1',     1912, 'Kiosk cut dividend: Wayrest'),
    ('TX-SEED-7002', 'BUYOUT', 'SYSTEM_SINK', 'MKT_TAX',   1913, 'Kiosk tax burn: Wayrest'),

    ('TX-SEED-7003', 'BUYOUT', 'PLAYER_LIQUID', '1002',  -26500, 'Buyout debit: Item #9020'),
    ('TX-SEED-7003', 'BUYOUT', 'PLAYER_LIQUID', '1004',   24380, 'Seller payout: Item #9020'),
    ('TX-SEED-7003', 'BUYOUT', 'GUILD_TREASURY', '4',     1060, 'Kiosk cut dividend: Imperial City'),
    ('TX-SEED-7003', 'BUYOUT', 'SYSTEM_SINK', 'MKT_TAX',   1060, 'Kiosk tax burn: Imperial City'),

    ('TX-SEED-7004', 'BUYOUT', 'PLAYER_LIQUID', '1011', -320000, 'Buyout debit: Item #9020'),
    ('TX-SEED-7004', 'BUYOUT', 'PLAYER_LIQUID', '1008',  304000, 'Seller payout: Item #9020'),
    ('TX-SEED-7004', 'BUYOUT', 'GUILD_TREASURY', '2',     8000, 'Kiosk cut dividend: Elden Root'),
    ('TX-SEED-7004', 'BUYOUT', 'SYSTEM_SINK', 'MKT_TAX',   8000, 'Kiosk tax burn: Elden Root'),

    ('TX-SEED-7005', 'BUYOUT', 'PLAYER_LIQUID', '1012', -310000, 'Buyout debit: Item #9021'),
    ('TX-SEED-7005', 'BUYOUT', 'PLAYER_LIQUID', '1011',  294500, 'Seller payout: Item #9021'),
    ('TX-SEED-7005', 'BUYOUT', 'GUILD_TREASURY', '4',     7750, 'Kiosk cut dividend: Imperial City'),
    ('TX-SEED-7005', 'BUYOUT', 'SYSTEM_SINK', 'MKT_TAX',   7750, 'Kiosk tax burn: Imperial City'),

    ('TX-SEED-7006', 'BUYOUT', 'PLAYER_LIQUID', '1004', -305000, 'Buyout debit: Item #9020'),
    ('TX-SEED-7006', 'BUYOUT', 'PLAYER_LIQUID', '1012',  280600, 'Seller payout: Item #9020'),
    ('TX-SEED-7006', 'BUYOUT', 'GUILD_TREASURY', '4',    12200, 'Kiosk cut dividend: Imperial City'),
    ('TX-SEED-7006', 'BUYOUT', 'SYSTEM_SINK', 'MKT_TAX',  12200, 'Kiosk tax burn: Imperial City');

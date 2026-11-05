-- ============================================================================
-- SCROLLS OF AGORA (v3.0): INITIAL TAMRIEL WORLD, 5 HUBS & ECONOMY SEED DATA
-- Hubs: Wayrest, Elden Root, Mournhold, Imperial City, Rawl'kha
-- ============================================================================

BEGIN;

-- 1. TRADE GUILDS
INSERT INTO trade_guilds (guild_id, guild_name, alliance, banner_crest, treasury_gold, tax_dividend_earned) VALUES
    (1, 'Wayrest Merchant Consortium', 'Daggerfall Covenant',  'lion',   4200000, 185000),
    (2, 'Dominion Golden Bough',       'Aldmeri Dominion',     'eagle',  3850000, 142000),
    (3, 'Mournhold Tribunal Factorum', 'Ebonheart Pact',       'dragon', 5100000, 260000),
    (4, 'Tel Var Obsidian Syndicate',  'Independent Syndicate','telvar', 6400000, 390000),
    (5, 'Baandari Pedlars Caravan',    'Independent Syndicate','moon',   4750000, 215000);

-- 2. THE 5 TAMRIEL TRADING HUBS (Wayrest, Elden Root, Mournhold, Imperial City, Rawl'kha)
INSERT INTO realms (realm_id, realm_name, province, region, map_x, map_y, controlling_guild_id, population_cap, tax_rate_bps) VALUES
    (1, 'Wayrest',       'Stormhaven, High Rock', 'HIGH-ROCK',     18, 26, 1, 14000, 450), -- 4.5% Tax
    (2, 'Elden Root',    'Grahtwood, Valenwood',  'VALENWOOD',     38, 78, 2, 14500, 400), -- 4.0% Tax
    (3, 'Mournhold',     'Deshaan, Morrowind',    'MORROWIND',     82, 52, 3, 16000, 500), -- 5.0% Tax
    (4, 'Imperial City', 'Cyrodiil Heartland',    'CYRODIIL',      52, 48, 4, 10000, 800), -- 8.0% Warzone Cut
    (5, 'Rawl''kha',     'Reaper''s March',       'REAPERS-MARCH', 30, 64, 5, 15500, 350); -- 3.5% Outlaw Bazaar

-- 3. SEALED WEEKLY KIOSK BIDS
INSERT INTO kiosk_bids (kiosk_bid_id, realm_id, guild_id, bid_gold, status) VALUES
    (1, 3, 3, 850000, 'SEALED'),
    (2, 3, 4, 920000, 'SEALED'),
    (3, 1, 1, 640000, 'SEALED'),
    (4, 5, 5, 780000, 'SEALED'),
    (5, 4, 4, 1150000, 'SEALED');

-- 4. PLAYERS & RMT MULE RING ACCOUNTS
INSERT INTO players (player_id, username, realm_id, guild_id, faction, character_class, level, gold_balance, escrow_gold, reputation_score, is_banned) VALUES
    (1001, 'Kaelen_Sunstrider', 1, 1, 'Vanguard',   'Templar',      100,  685000,  75000,  980, FALSE),
    (1002, 'Sylvan_Whisper',    2, 2, 'Syndicate',  'Nightblade',   100,  920000,      0,  845, FALSE),
    (1003, 'Gorim_Ironforge',   3, 3, 'Vanguard',   'Dragonknight',  95,  510000,      0,  995, FALSE),
    (1004, 'Vexia_Nightbane',   4, 4, 'Syndicate',  'Arcanist',     100,  875000, 145000,  620, FALSE),
    (1005, 'Aurelius_Goldhand', 3, 3, 'Outlanders', 'Sorcerer',     100, 2450000,      0, 1250, FALSE),
    (1006, 'Lyra_Starweaver',   2, 2, 'Vanguard',   'Warden',        88,  395000,  19500,  910, FALSE),
    (1007, 'Razum_Dar_Trader',  5, 5, 'Outlanders', 'Nightblade',    98,  742000,      0,  940, FALSE),
    (1008, 'Zul_Bot_Harvester', 5, NULL, 'Outlanders', 'Rogue',       5,   12000,      0,   15, FALSE),
    (1009, 'Thorne_Alchemist',  2, 2, 'Outlanders', 'Apothecary',    92,  640000,      0,  890, FALSE),
    (1010, 'Nyx_Voidwalker',    4, 4, 'Syndicate',  'Necromancer',  100,  880000,      0,  775, FALSE),
    (1011, 'Skooma_Launder_02', 1, NULL, 'Syndicate',  'Rogue',       8,   45000,      0,   10, FALSE),
    (1012, 'RMT_Syndicate_Boss',4, NULL, 'Syndicate',  'Arcanist',   15,  985000,      0,    5, FALSE);

-- 5. ITEM TEMPLATES (Supertype)
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
    (5013, 'Cracked Goblinshiv (Wash Mule Item)','dagger',     'Worthless scrap blade used by RMT gold-laundering rings to move illicit gold.', 'Weapon','Common',     5,   1,   1),
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

-- 8. INVENTORY ITEMS (Physical Minted Instances across the 5 Cities & Player Bags)
INSERT INTO inventory_items (instance_id, item_id, owner_id, mint_serial, temper_tier, bonus_power, stack_size, current_durability, is_escrowed) VALUES
    -- Escrowed on Kiosks across the 5 Hubs
    (9001, 5001, 1003, 'AGORA-ASH-0001-9F8A7B', 3, 240,  1, 150, TRUE),  -- Mournhold
    (9002, 5002, 1001, 'AGORA-AEG-0002-3C4D1E', 2, 120,  1, 140, TRUE),  -- Wayrest
    (9003, 5003, 1007, 'AGORA-RAZ-0003-7A2B9C', 1,  80,  1, 110, TRUE),  -- Rawl'kha
    (9004, 5004, 1004, 'AGORA-CWN-0004-1D5E8F', 1,  60,  1, 100, TRUE),  -- Imperial City
    (9005, 5005, 1003, 'AGORA-DSC-0005-6B3F0A', 2, 110,  1, 135, TRUE),  -- Mournhold
    (9006, 5008, 1009, 'AGORA-FLK-0006-4E9C2D', 0,   0, 20, 100, TRUE),  -- Elden Root (Cheap!)
    (9007, 5008, 1004, 'AGORA-FLK-0007-8A1F5B', 0,   0, 20, 100, TRUE),  -- Imperial City (Expensive -> Arbitrage!)
    (9008, 5011, 1007, 'AGORA-WAX-0008-2C7D4E', 0,   0, 50, 100, TRUE),  -- Rawl'kha (Cheap Dreugh Wax!)
    (9009, 5011, 1001, 'AGORA-WAX-0009-5F0B3A', 0,   0, 50, 100, TRUE),  -- Wayrest (Expensive Dreugh Wax -> Arbitrage!)
    (9010, 5006, 1002, 'AGORA-RNG-0010-9D4A6C', 1,  45,  1,  80, TRUE),  -- Elden Root
    (9011, 5014, 1010, 'AGORA-CHM-0011-IMPCIT', 4, 400,  1, 100, TRUE),  -- Imperial City
    (9012, 5007, 1001, 'AGORA-CLY-0012-WAYRST', 0,   0,  1, 100, TRUE),  -- Wayrest
    -- Active Player Bag Items (Aurelius_Goldhand 1005 & Kaelen 1001) ready for Arcane Tempering & Listing!
    (9013, 5005, 1005, 'AGORA-DSC-0013-BAG001', 0,   0,  1, 135, FALSE),
    (9014, 5006, 1005, 'AGORA-RNG-0014-BAG002', 0,   0,  1,  80, FALSE),
    (9015, 5007, 1005, 'AGORA-CLY-0015-BAG003', 0,   0,  1, 100, FALSE),
    (9016, 5014, 1005, 'AGORA-ESC-0016-CHIM00', 2, 200,  1, 100, FALSE),
    (9017, 5002, 1005, 'AGORA-AEG-0017-TRIBNL', 1,  90,  1, 140, FALSE),
    (9018, 5011, 1005, 'AGORA-WAX-0018-CRAFT1', 0,   0, 25, 100, FALSE), -- Dreugh Wax in bag for Tempering!
    (9019, 5012, 1005, 'AGORA-CHR-0019-CRAFT2', 0,   0, 40, 100, FALSE), -- Chromium Plating in bag!
    (9020, 5008, 1005, 'AGORA-FLK-0020-ALCHMY', 0,   0, 10, 100, FALSE),
    -- Historical & RMT Mule Chain Items
    (9021, 5001, 1005, 'AGORA-ASH-0021-SOLD01', 2, 180,  1, 150, FALSE),
    (9022, 5013, 1011, 'AGORA-JNK-0022-RMT001', 0,   0,  1,  15, FALSE),
    (9023, 5013, 1004, 'AGORA-JNK-0023-RMT002', 0,   0,  1,  15, FALSE),
    (9024, 5013, 1012, 'AGORA-JNK-0024-RMT003', 0,   0,  1,  15, FALSE);

-- 9. ITEM INSTANCE ENCHANTMENTS
INSERT INTO item_instance_enchantments (instance_id, enchant_id) VALUES
    (9001, 1), (9001, 2),
    (9002, 5),
    (9003, 2), (9003, 3),
    (9004, 4),
    (9011, 2),
    (9016, 2);

-- 10. AUCTION LISTINGS ACROSS THE 5 TAMRIEL CITIES
INSERT INTO auction_listings (
    listing_id, instance_id, seller_id, realm_id, listing_type,
    start_price, buyout_price, current_bid, high_bidder_id, status, listed_at, expires_at
) VALUES
    -- Active Listings across Wayrest (1), Elden Root (2), Mournhold (3), Imperial City (4), Rawl'kha (5)
    (101, 9001, 1003, 3, 'AUCTION',     140000, 185000, 145000, 1004, 'ACTIVE', CURRENT_TIMESTAMP - INTERVAL '4 hours', CURRENT_TIMESTAMP + INTERVAL '20 hours'),
    (102, 9002, 1001, 1, 'AUCTION',      72000,  95000,  75000, 1002, 'ACTIVE', CURRENT_TIMESTAMP - INTERVAL '6 hours', CURRENT_TIMESTAMP + INTERVAL '18 hours'),
    (103, 9003, 1007, 5, 'BUYOUT_ONLY',  64000,  64000,      0, NULL, 'ACTIVE', CURRENT_TIMESTAMP - INTERVAL '2 hours', CURRENT_TIMESTAMP + INTERVAL '22 hours'),
    (104, 9004, 1004, 4, 'AUCTION',      18000,  24500,  19500, 1006, 'ACTIVE', CURRENT_TIMESTAMP - INTERVAL '5 hours', CURRENT_TIMESTAMP + INTERVAL '19 hours'),
    (105, 9005, 1003, 3, 'BUYOUT_ONLY',  29000,  29000,      0, NULL, 'ACTIVE', CURRENT_TIMESTAMP - INTERVAL '1 hour',  CURRENT_TIMESTAMP + INTERVAL '23 hours'),
    (106, 9006, 1009, 2, 'BUYOUT_ONLY',   6200,   6200,      0, NULL, 'ACTIVE', CURRENT_TIMESTAMP - INTERVAL '3 hours', CURRENT_TIMESTAMP + INTERVAL '21 hours'),
    (107, 9007, 1004, 4, 'BUYOUT_ONLY',  11800,  11800,      0, NULL, 'ACTIVE', CURRENT_TIMESTAMP - INTERVAL '2 hours', CURRENT_TIMESTAMP + INTERVAL '22 hours'),
    (108, 9008, 1007, 5, 'BUYOUT_ONLY',  19500,  19500,      0, NULL, 'ACTIVE', CURRENT_TIMESTAMP - INTERVAL '3 hours', CURRENT_TIMESTAMP + INTERVAL '21 hours'),
    (109, 9009, 1001, 1, 'BUYOUT_ONLY',  34500,  34500,      0, NULL, 'ACTIVE', CURRENT_TIMESTAMP - INTERVAL '1 hour',  CURRENT_TIMESTAMP + INTERVAL '23 hours'),
    (110, 9010, 1002, 2, 'AUCTION',      14000,  19000,      0, NULL, 'ACTIVE', CURRENT_TIMESTAMP - INTERVAL '30 mins', CURRENT_TIMESTAMP + INTERVAL '23 hours'),
    (111, 9011, 1010, 4, 'AUCTION',     260000, 320000,      0, NULL, 'ACTIVE', CURRENT_TIMESTAMP - INTERVAL '1 hour',  CURRENT_TIMESTAMP + INTERVAL '23 hours'),
    (112, 9012, 1001, 1, 'BUYOUT_ONLY',   9200,   9200,      0, NULL, 'ACTIVE', CURRENT_TIMESTAMP - INTERVAL '2 hours', CURRENT_TIMESTAMP + INTERVAL '22 hours'),
    -- Settled Historical & RMT Laundering Hop Listings
    (201, 9021, 1001, 3, 'BUYOUT_ONLY', 175000, 175000, 175000, 1005, 'SOLD',   CURRENT_TIMESTAMP - INTERVAL '3 days',  CURRENT_TIMESTAMP - INTERVAL '2 days'),
    (202, 9022, 1008, 5, 'BUYOUT_ONLY', 320000, 320000, 320000, 1011, 'SOLD',   CURRENT_TIMESTAMP - INTERVAL '2 days',  CURRENT_TIMESTAMP - INTERVAL '1 day'),
    (203, 9023, 1011, 1, 'BUYOUT_ONLY', 305000, 305000, 305000, 1004, 'SOLD',   CURRENT_TIMESTAMP - INTERVAL '1 day',   CURRENT_TIMESTAMP - INTERVAL '12 hours'),
    (204, 9024, 1012, 4, 'BUYOUT_ONLY', 290000, 290000, 290000, 1011, 'SOLD',   CURRENT_TIMESTAMP - INTERVAL '6 hours', CURRENT_TIMESTAMP - INTERVAL '1 hour');

-- 11. AUCTION BIDS
INSERT INTO auction_bids (listing_id, bidder_id, bid_amount, placed_at) VALUES
    (101, 1002, 140000, CURRENT_TIMESTAMP - INTERVAL '3 hours'),
    (101, 1004, 145000, CURRENT_TIMESTAMP - INTERVAL '1 hour'),
    (102, 1002,  75000, CURRENT_TIMESTAMP - INTERVAL '2 hours'),
    (104, 1006,  19500, CURRENT_TIMESTAMP - INTERVAL '90 mins');

-- 12. LEDGER TRANSACTIONS (Includes 3-Hop RMT Gold Laundering Chain: 1008 -> 1011 -> 1012)
INSERT INTO ledger_transactions (
    tx_id, listing_id, instance_id, seller_id, buyer_id,
    gross_price, market_tax_burned, seller_net_payout, settlement_type, executed_at
) VALUES
    (501, 201, 9021, 1001, 1005, 175000,  8750, 166250, 'INSTANT_BUYOUT', CURRENT_TIMESTAMP - INTERVAL '2 days'),
    -- Hop 1: Bot Harvester (1008) sells 5g Goblinshiv to Skooma_Launder_02 (1011) or vice versa to move dirty gold
    (502, 202, 9022, 1008, 1011, 320000, 11200, 308800, 'INSTANT_BUYOUT', CURRENT_TIMESTAMP - INTERVAL '36 hours'),
    -- Hop 2: Skooma_Launder_02 (1011) washes 305,000g to Vexia_Nightbane (1004)
    (503, 203, 9023, 1011, 1004, 305000, 13725, 291275, 'INSTANT_BUYOUT', CURRENT_TIMESTAMP - INTERVAL '18 hours'),
    -- Hop 3: RMT_Syndicate_Boss (1012) extracts 290,000g via junk wash trade
    (504, 204, 9024, 1012, 1011, 290000, 23200, 266800, 'INSTANT_BUYOUT', CURRENT_TIMESTAMP - INTERVAL '4 hours');

-- 13. INITIAL DOUBLE-ENTRY JOURNAL BALANCES
INSERT INTO ledger_journal (tx_group_id, event_type, account_type, account_id, amount, description) VALUES
    ('TX-SEED-501', 'BUYOUT', 'PLAYER_LIQUID', '1005', -175000, 'Buyout debit: Item #9021'),
    ('TX-SEED-501', 'BUYOUT', 'PLAYER_LIQUID', '1001',  166250, 'Seller payout: Item #9021'),
    ('TX-SEED-501', 'BUYOUT', 'GUILD_TREASURY', '3',     4375, 'Kiosk cut dividend'),
    ('TX-SEED-501', 'BUYOUT', 'SYSTEM_SINK', 'MKT_TAX',   4375, 'Kiosk tax burn'),

    ('TX-SEED-502', 'BUYOUT', 'PLAYER_LIQUID', '1011', -320000, 'Buyout debit: Item #9022'),
    ('TX-SEED-502', 'BUYOUT', 'PLAYER_LIQUID', '1008',  308800, 'Seller payout: Item #9022'),
    ('TX-SEED-502', 'BUYOUT', 'GUILD_TREASURY', '5',     5600, 'Kiosk cut dividend'),
    ('TX-SEED-502', 'BUYOUT', 'SYSTEM_SINK', 'MKT_TAX',   5600, 'Kiosk tax burn'),

    ('TX-SEED-503', 'BUYOUT', 'PLAYER_LIQUID', '1004', -305000, 'Buyout debit: Item #9023'),
    ('TX-SEED-503', 'BUYOUT', 'PLAYER_LIQUID', '1011',  291275, 'Seller payout: Item #9023'),
    ('TX-SEED-503', 'BUYOUT', 'GUILD_TREASURY', '1',     6862, 'Kiosk cut dividend'),
    ('TX-SEED-503', 'BUYOUT', 'SYSTEM_SINK', 'MKT_TAX',   6863, 'Kiosk tax burn'),

    ('TX-SEED-504', 'BUYOUT', 'PLAYER_LIQUID', '1011', -290000, 'Buyout debit: Item #9024'),
    ('TX-SEED-504', 'BUYOUT', 'PLAYER_LIQUID', '1012',  266800, 'Seller payout: Item #9024'),
    ('TX-SEED-504', 'BUYOUT', 'GUILD_TREASURY', '4',    11600, 'Kiosk cut dividend'),
    ('TX-SEED-504', 'BUYOUT', 'SYSTEM_SINK', 'MKT_TAX',  11600, 'Kiosk tax burn');

-- Synchronize PostgreSQL sequences
SELECT setval('trade_guilds_guild_id_seq', 5, true);
SELECT setval('realms_realm_id_seq', 5, true);
SELECT setval('kiosk_bids_kiosk_bid_id_seq', 5, true);
SELECT setval('players_player_id_seq', 1012, true);
SELECT setval('item_templates_item_id_seq', 5014, true);
SELECT setval('enchantments_enchant_id_seq', 5, true);
SELECT setval('inventory_items_instance_id_seq', 9024, true);
SELECT setval('auction_listings_listing_id_seq', 204, true);
SELECT setval('ledger_transactions_tx_id_seq', 504, true);
SELECT setval('ledger_journal_entry_id_seq', 16, true);

COMMIT;

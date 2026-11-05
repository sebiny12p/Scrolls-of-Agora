-- ============================================================================
-- SCROLLS OF AGORA: RELATIONAL DDL (SQLite WAL Engine)
-- 12 Normalized Relations (BCNF / 3NF), Foreign Keys & Partial Covering Indexes
-- ============================================================================

DROP TABLE IF EXISTS price_history_ohlc;
DROP TABLE IF EXISTS ledger_transactions;
DROP TABLE IF EXISTS auction_bids;
DROP TABLE IF EXISTS auction_listings;
DROP TABLE IF EXISTS item_instance_enchantments;
DROP TABLE IF EXISTS enchantments;
DROP TABLE IF EXISTS inventory_items;
DROP TABLE IF EXISTS consumable_specs;
DROP TABLE IF EXISTS equipment_specs;
DROP TABLE IF EXISTS item_templates;
DROP TABLE IF EXISTS kiosk_bids;
DROP TABLE IF EXISTS players;
DROP TABLE IF EXISTS realms;
DROP TABLE IF EXISTS trade_guilds;

-- 1. TRADE GUILDS (Merchant Syndicates competing for Regional Kiosk Leases)
CREATE TABLE trade_guilds (
    guild_id INTEGER PRIMARY KEY,
    guild_name TEXT NOT NULL UNIQUE,
    alliance TEXT NOT NULL CHECK (alliance IN ('Daggerfall Covenant', 'Aldmeri Dominion', 'Ebonheart Pact', 'Independent Syndicate')),
    banner_crest TEXT NOT NULL DEFAULT 'gold',
    treasury_gold INTEGER NOT NULL DEFAULT 0 CHECK (treasury_gold >= 0),
    tax_dividend_earned INTEGER NOT NULL DEFAULT 0 CHECK (tax_dividend_earned >= 0)
);

-- 2. TRADING HUBS / REALMS (The 5 Decentralized Tamriel Guild Trader Kiosks)
CREATE TABLE realms (
    realm_id INTEGER PRIMARY KEY,
    realm_name TEXT NOT NULL UNIQUE,
    province TEXT NOT NULL,
    region TEXT NOT NULL CHECK (region IN ('HIGH-ROCK', 'VALENWOOD', 'MORROWIND', 'CYRODIIL', 'REAPERS-MARCH')),
    map_x INTEGER NOT NULL CHECK (map_x BETWEEN 0 AND 100),
    map_y INTEGER NOT NULL CHECK (map_y BETWEEN 0 AND 100),
    controlling_guild_id INTEGER REFERENCES trade_guilds(guild_id) ON DELETE SET NULL,
    population_cap INTEGER NOT NULL DEFAULT 10000 CHECK (population_cap > 0),
    tax_rate_bps INTEGER NOT NULL DEFAULT 500 CHECK (tax_rate_bps BETWEEN 0 AND 2500)
);

-- 3. WEEKLY BLIND KIOSK BIDS (Sealed Guild Bids for The Weekly Flip)
CREATE TABLE kiosk_bids (
    kiosk_bid_id INTEGER PRIMARY KEY AUTOINCREMENT,
    realm_id INTEGER NOT NULL REFERENCES realms(realm_id) ON DELETE CASCADE,
    guild_id INTEGER NOT NULL REFERENCES trade_guilds(guild_id) ON DELETE CASCADE,
    bid_gold INTEGER NOT NULL CHECK (bid_gold > 0),
    status TEXT NOT NULL DEFAULT 'SEALED' CHECK (status IN ('SEALED', 'WON', 'REFUNDED')),
    placed_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 4. PLAYERS (With strict non-negative wallet, escrow & anti-cheat ban status)
CREATE TABLE players (
    player_id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    realm_id INTEGER NOT NULL REFERENCES realms(realm_id) ON DELETE RESTRICT,
    guild_id INTEGER REFERENCES trade_guilds(guild_id) ON DELETE SET NULL,
    faction TEXT NOT NULL CHECK (faction IN ('Vanguard', 'Syndicate', 'Outlanders')),
    character_class TEXT NOT NULL,
    level INTEGER NOT NULL DEFAULT 1 CHECK (level BETWEEN 1 AND 100),
    gold_balance INTEGER NOT NULL DEFAULT 0 CHECK (gold_balance >= 0),
    escrow_gold INTEGER NOT NULL DEFAULT 0 CHECK (escrow_gold >= 0),
    reputation_score INTEGER NOT NULL DEFAULT 100 CHECK (reputation_score >= 0),
    is_banned INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 5. ITEM TEMPLATES (Supertype in ISA Generalization Hierarchy)
CREATE TABLE item_templates (
    item_id INTEGER PRIMARY KEY,
    item_name TEXT NOT NULL UNIQUE,
    icon_key TEXT NOT NULL DEFAULT 'runeblade',
    lore_text TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL CHECK (category IN ('Weapon', 'Armor', 'Consumable', 'Reagent', 'Artifact')),
    rarity TEXT NOT NULL CHECK (rarity IN ('Common', 'Uncommon', 'Rare', 'Epic', 'Legendary', 'Mythic')),
    base_vendor_value INTEGER NOT NULL CHECK (base_vendor_value >= 0),
    max_stack INTEGER NOT NULL DEFAULT 1 CHECK (max_stack BETWEEN 1 AND 1000),
    required_level INTEGER NOT NULL DEFAULT 1 CHECK (required_level BETWEEN 1 AND 100)
);

-- 6A. EQUIPMENT SPECS (ISA Subtype 1: Equipment -> Item Templates)
CREATE TABLE equipment_specs (
    item_id INTEGER PRIMARY KEY REFERENCES item_templates(item_id) ON DELETE CASCADE,
    equip_slot TEXT NOT NULL CHECK (equip_slot IN ('MainHand', 'OffHand', 'Helm', 'Chest', 'Boots', 'Ring', 'Amulet')),
    attack_power INTEGER NOT NULL DEFAULT 0 CHECK (attack_power >= 0),
    armor_rating INTEGER NOT NULL DEFAULT 0 CHECK (armor_rating >= 0),
    max_durability INTEGER NOT NULL DEFAULT 100 CHECK (max_durability > 0),
    socket_count INTEGER NOT NULL DEFAULT 0 CHECK (socket_count BETWEEN 0 AND 4)
);

-- 6B. CONSUMABLE SPECS (ISA Subtype 2: Consumable -> Item Templates)
CREATE TABLE consumable_specs (
    item_id INTEGER PRIMARY KEY REFERENCES item_templates(item_id) ON DELETE CASCADE,
    effect_type TEXT NOT NULL CHECK (effect_type IN ('Heal', 'ManaRestore', 'BerserkBuff', 'StealthElixir', 'Resistance')),
    effect_potency INTEGER NOT NULL CHECK (effect_potency > 0),
    duration_seconds INTEGER NOT NULL DEFAULT 0 CHECK (duration_seconds >= 0),
    cooldown_seconds INTEGER NOT NULL DEFAULT 30 CHECK (cooldown_seconds >= 0)
);

-- 7. INVENTORY ITEMS (Physical Instances with Anti-Dupe Cryptographic Serials)
CREATE TABLE inventory_items (
    instance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL REFERENCES item_templates(item_id) ON DELETE RESTRICT,
    owner_id INTEGER NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    mint_serial TEXT NOT NULL UNIQUE,
    temper_tier INTEGER NOT NULL DEFAULT 0 CHECK (temper_tier BETWEEN 0 AND 5),
    bonus_power INTEGER NOT NULL DEFAULT 0 CHECK (bonus_power >= 0),
    stack_size INTEGER NOT NULL DEFAULT 1 CHECK (stack_size > 0),
    current_durability INTEGER NOT NULL DEFAULT 100 CHECK (current_durability >= 0),
    is_escrowed INTEGER NOT NULL DEFAULT 0,
    minted_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 8. ENCHANTMENTS & M:N JUNCTION TABLE
CREATE TABLE enchantments (
    enchant_id INTEGER PRIMARY KEY,
    enchant_name TEXT NOT NULL UNIQUE,
    stat_type TEXT NOT NULL CHECK (stat_type IN ('CritStrike', 'Haste', 'Lifesteal', 'VoidDamage', 'Thorns')),
    bonus_value INTEGER NOT NULL CHECK (bonus_value > 0),
    tier INTEGER NOT NULL CHECK (tier BETWEEN 1 AND 5)
);

CREATE TABLE item_instance_enchantments (
    instance_id INTEGER NOT NULL REFERENCES inventory_items(instance_id) ON DELETE CASCADE,
    enchant_id INTEGER NOT NULL REFERENCES enchantments(enchant_id) ON DELETE RESTRICT,
    applied_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (instance_id, enchant_id)
);

-- 9. AUCTION LISTINGS (Active & Historical Regional Kiosk Orderbook)
CREATE TABLE auction_listings (
    listing_id INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_id INTEGER NOT NULL REFERENCES inventory_items(instance_id) ON DELETE RESTRICT,
    seller_id INTEGER NOT NULL REFERENCES players(player_id) ON DELETE RESTRICT,
    realm_id INTEGER NOT NULL REFERENCES realms(realm_id) ON DELETE RESTRICT,
    listing_type TEXT NOT NULL DEFAULT 'AUCTION' CHECK (listing_type IN ('AUCTION', 'BUYOUT_ONLY')),
    start_price INTEGER NOT NULL CHECK (start_price > 0),
    buyout_price INTEGER CHECK (buyout_price IS NULL OR buyout_price >= start_price),
    current_bid INTEGER NOT NULL DEFAULT 0 CHECK (current_bid >= 0),
    high_bidder_id INTEGER REFERENCES players(player_id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'SOLD', 'CANCELLED', 'EXPIRED')),
    listed_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    CHECK (high_bidder_id IS NULL OR high_bidder_id <> seller_id)
);

-- 10. AUCTION BIDS (Bid Progression History)
CREATE TABLE auction_bids (
    bid_id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL REFERENCES auction_listings(listing_id) ON DELETE CASCADE,
    bidder_id INTEGER NOT NULL REFERENCES players(player_id) ON DELETE RESTRICT,
    bid_amount INTEGER NOT NULL CHECK (bid_amount > 0),
    placed_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 11. IMMUTABLE LEDGER TRANSACTIONS (Double-Entry Financial Settlement)
CREATE TABLE ledger_transactions (
    tx_id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL UNIQUE REFERENCES auction_listings(listing_id) ON DELETE RESTRICT,
    instance_id INTEGER NOT NULL REFERENCES inventory_items(instance_id) ON DELETE RESTRICT,
    seller_id INTEGER NOT NULL REFERENCES players(player_id) ON DELETE RESTRICT,
    buyer_id INTEGER NOT NULL REFERENCES players(player_id) ON DELETE RESTRICT,
    gross_price INTEGER NOT NULL CHECK (gross_price > 0),
    market_tax_burned INTEGER NOT NULL CHECK (market_tax_burned >= 0),
    seller_net_payout INTEGER NOT NULL CHECK (seller_net_payout >= 0),
    settlement_type TEXT NOT NULL CHECK (settlement_type IN ('INSTANT_BUYOUT', 'AUCTION_WON')),
    executed_at TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (gross_price = market_tax_burned + seller_net_payout),
    CHECK (seller_id <> buyer_id)
);

-- 12. PRICE HISTORY OHLC (For Analytical Market Radar & Candlesticks)
CREATE TABLE price_history_ohlc (
    candle_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL REFERENCES item_templates(item_id) ON DELETE CASCADE,
    realm_id INTEGER NOT NULL REFERENCES realms(realm_id) ON DELETE CASCADE,
    bucket_timestamp TEXT NOT NULL,
    open_price INTEGER NOT NULL,
    high_price INTEGER NOT NULL,
    low_price INTEGER NOT NULL,
    close_price INTEGER NOT NULL,
    volume_traded INTEGER NOT NULL
);

-- ============================================================================
-- PERFORMANCE INDEXES (Partial, Covering & Composite)
-- ============================================================================
CREATE INDEX idx_active_listings_realm_price ON auction_listings (realm_id, buyout_price ASC) WHERE status = 'ACTIVE';
CREATE UNIQUE INDEX idx_unique_active_instance ON auction_listings (instance_id) WHERE status = 'ACTIVE';
CREATE INDEX idx_inventory_owner ON inventory_items (owner_id, is_escrowed);
CREATE INDEX idx_ledger_executed_at ON ledger_transactions (executed_at DESC);
CREATE INDEX idx_ohlc_item_realm_time ON price_history_ohlc (item_id, realm_id, candle_id DESC);

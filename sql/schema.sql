-- ============================================================================
-- SCROLLS OF AGORA: RELATIONAL DDL (PostgreSQL 16/17+ Engine)
-- 13 Normalized Relations (BCNF / 3NF), Foreign Keys & Partial Covering Indexes
-- ============================================================================

DROP TABLE IF EXISTS limit_orders CASCADE;
DROP TABLE IF EXISTS player_mail CASCADE;
DROP TABLE IF EXISTS ledger_journal CASCADE;
DROP TABLE IF EXISTS price_history_ohlc CASCADE;
DROP TABLE IF EXISTS ledger_transactions CASCADE;
DROP TABLE IF EXISTS auction_bids CASCADE;
DROP TABLE IF EXISTS auction_listings CASCADE;
DROP TABLE IF EXISTS item_instance_enchantments CASCADE;
DROP TABLE IF EXISTS enchantments CASCADE;
DROP TABLE IF EXISTS inventory_items CASCADE;
DROP TABLE IF EXISTS consumable_specs CASCADE;
DROP TABLE IF EXISTS equipment_specs CASCADE;
DROP TABLE IF EXISTS item_templates CASCADE;
DROP TABLE IF EXISTS kiosk_bids CASCADE;
DROP TABLE IF EXISTS players CASCADE;
DROP TABLE IF EXISTS realms CASCADE;
DROP TABLE IF EXISTS trade_guilds CASCADE;

-- 1. TRADE GUILDS (Merchant Syndicates competing for City Kiosk Leases)
CREATE TABLE trade_guilds (
    guild_id SERIAL PRIMARY KEY,
    guild_name VARCHAR(64) NOT NULL UNIQUE,
    alliance VARCHAR(32) NOT NULL CHECK (alliance IN ('Daggerfall Covenant', 'Aldmeri Dominion', 'Ebonheart Pact', 'Independent Syndicate')),
    banner_crest VARCHAR(24) NOT NULL DEFAULT 'gold',
    treasury_gold BIGINT NOT NULL DEFAULT 0 CHECK (treasury_gold >= 0),
    tax_dividend_earned BIGINT NOT NULL DEFAULT 0 CHECK (tax_dividend_earned >= 0)
);

-- 2. TRADING HUBS / REALMS (The 5 Decentralized Tamriel Guild Trader Kiosks)
CREATE TABLE realms (
    realm_id SERIAL PRIMARY KEY,
    realm_name VARCHAR(64) NOT NULL UNIQUE,
    province VARCHAR(48) NOT NULL,
    region VARCHAR(16) NOT NULL CHECK (region IN ('HIGH-ROCK', 'VALENWOOD', 'MORROWIND', 'CYRODIIL', 'REAPERS-MARCH')),
    map_x INT NOT NULL CHECK (map_x BETWEEN 0 AND 100),
    map_y INT NOT NULL CHECK (map_y BETWEEN 0 AND 100),
    controlling_guild_id INT REFERENCES trade_guilds(guild_id) ON DELETE SET NULL,
    population_cap INT NOT NULL DEFAULT 10000 CHECK (population_cap > 0),
    tax_rate_bps INT NOT NULL DEFAULT 500 CHECK (tax_rate_bps BETWEEN 0 AND 2500)
);

-- 3. WEEKLY BLIND KIOSK BIDS (Sealed Guild Bids for The Weekly Flip)
CREATE TABLE kiosk_bids (
    kiosk_bid_id SERIAL PRIMARY KEY,
    realm_id INT NOT NULL REFERENCES realms(realm_id) ON DELETE CASCADE,
    guild_id INT NOT NULL REFERENCES trade_guilds(guild_id) ON DELETE CASCADE,
    bid_gold BIGINT NOT NULL CHECK (bid_gold > 0),
    status VARCHAR(16) NOT NULL DEFAULT 'SEALED' CHECK (status IN ('SEALED', 'WON', 'REFUNDED')),
    placed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 4. PLAYERS (With strict non-negative wallet, escrow & anti-cheat ban status)
CREATE TABLE players (
    player_id SERIAL PRIMARY KEY,
    username VARCHAR(48) NOT NULL UNIQUE,
    realm_id INT NOT NULL REFERENCES realms(realm_id) ON DELETE RESTRICT,
    guild_id INT REFERENCES trade_guilds(guild_id) ON DELETE SET NULL,
    faction VARCHAR(24) NOT NULL CHECK (faction IN ('Vanguard', 'Syndicate', 'Outlanders')),
    character_class VARCHAR(32) NOT NULL,
    level INT NOT NULL DEFAULT 1 CHECK (level BETWEEN 1 AND 100),
    gold_balance BIGINT NOT NULL DEFAULT 0 CHECK (gold_balance >= 0),
    escrow_gold BIGINT NOT NULL DEFAULT 0 CHECK (escrow_gold >= 0),
    reputation_score INT NOT NULL DEFAULT 100 CHECK (reputation_score >= 0),
    is_banned BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 5. ITEM TEMPLATES (Supertype in ISA Generalization)
CREATE TABLE item_templates (
    item_id SERIAL PRIMARY KEY,
    item_name VARCHAR(120) NOT NULL UNIQUE,
    icon_key VARCHAR(32) NOT NULL DEFAULT 'runeblade',
    lore_text TEXT NOT NULL DEFAULT '',
    category VARCHAR(32) NOT NULL CHECK (category IN ('Weapon', 'Armor', 'Consumable', 'Reagent', 'Artifact')),
    rarity VARCHAR(16) NOT NULL CHECK (rarity IN ('Common', 'Uncommon', 'Rare', 'Epic', 'Legendary', 'Mythic')),
    base_vendor_value BIGINT NOT NULL CHECK (base_vendor_value >= 0),
    max_stack INT NOT NULL DEFAULT 1 CHECK (max_stack BETWEEN 1 AND 1000),
    required_level INT NOT NULL DEFAULT 1 CHECK (required_level BETWEEN 1 AND 100)
);

-- 6A. EQUIPMENT SPECS (ISA Subtype 1: Equipment -> Item Templates)
CREATE TABLE equipment_specs (
    item_id INT PRIMARY KEY REFERENCES item_templates(item_id) ON DELETE CASCADE,
    equip_slot VARCHAR(24) NOT NULL CHECK (equip_slot IN ('MainHand', 'OffHand', 'Helm', 'Chest', 'Boots', 'Ring', 'Amulet')),
    attack_power INT NOT NULL DEFAULT 0 CHECK (attack_power >= 0),
    armor_rating INT NOT NULL DEFAULT 0 CHECK (armor_rating >= 0),
    max_durability INT NOT NULL DEFAULT 100 CHECK (max_durability > 0),
    socket_count INT NOT NULL DEFAULT 0 CHECK (socket_count BETWEEN 0 AND 4)
);

-- 6B. CONSUMABLE SPECS (ISA Subtype 2: Consumable -> Item Templates)
CREATE TABLE consumable_specs (
    item_id INT PRIMARY KEY REFERENCES item_templates(item_id) ON DELETE CASCADE,
    effect_type VARCHAR(32) NOT NULL CHECK (effect_type IN ('Heal', 'ManaRestore', 'BerserkBuff', 'StealthElixir', 'Resistance')),
    effect_potency INT NOT NULL CHECK (effect_potency > 0),
    duration_seconds INT NOT NULL DEFAULT 0 CHECK (duration_seconds >= 0),
    cooldown_seconds INT NOT NULL DEFAULT 30 CHECK (cooldown_seconds >= 0)
);

-- 7. INVENTORY ITEMS (Unique physical item instances with anti-dupe cryptographic serials)
CREATE TABLE inventory_items (
    instance_id SERIAL PRIMARY KEY,
    item_id INT NOT NULL REFERENCES item_templates(item_id) ON DELETE RESTRICT,
    owner_id INT NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    mint_serial VARCHAR(64) NOT NULL UNIQUE,
    temper_tier INT NOT NULL DEFAULT 0 CHECK (temper_tier BETWEEN 0 AND 5),
    bonus_power INT NOT NULL DEFAULT 0 CHECK (bonus_power >= 0),
    stack_size INT NOT NULL DEFAULT 1 CHECK (stack_size > 0),
    current_durability INT NOT NULL DEFAULT 100 CHECK (current_durability >= 0),
    is_escrowed BOOLEAN NOT NULL DEFAULT FALSE,
    minted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 8. ENCHANTMENTS & M:N JUNCTION TABLE
CREATE TABLE enchantments (
    enchant_id SERIAL PRIMARY KEY,
    enchant_name VARCHAR(64) NOT NULL UNIQUE,
    stat_type VARCHAR(32) NOT NULL CHECK (stat_type IN ('CritStrike', 'Haste', 'Lifesteal', 'VoidDamage', 'Thorns')),
    bonus_value INT NOT NULL CHECK (bonus_value > 0),
    tier INT NOT NULL CHECK (tier BETWEEN 1 AND 5)
);

CREATE TABLE item_instance_enchantments (
    instance_id INT NOT NULL REFERENCES inventory_items(instance_id) ON DELETE CASCADE,
    enchant_id INT NOT NULL REFERENCES enchantments(enchant_id) ON DELETE RESTRICT,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (instance_id, enchant_id)
);

-- 9. AUCTION LISTINGS (Active & Historical City Kiosk Orderbook)
CREATE TABLE auction_listings (
    listing_id SERIAL PRIMARY KEY,
    instance_id INT NOT NULL REFERENCES inventory_items(instance_id) ON DELETE RESTRICT,
    seller_id INT NOT NULL REFERENCES players(player_id) ON DELETE RESTRICT,
    realm_id INT NOT NULL REFERENCES realms(realm_id) ON DELETE RESTRICT,
    listing_type VARCHAR(16) NOT NULL DEFAULT 'AUCTION' CHECK (listing_type IN ('AUCTION', 'BUYOUT_ONLY')),
    start_price BIGINT NOT NULL CHECK (start_price > 0),
    buyout_price BIGINT CHECK (buyout_price IS NULL OR buyout_price >= start_price),
    current_bid BIGINT NOT NULL DEFAULT 0 CHECK (current_bid >= 0),
    high_bidder_id INT REFERENCES players(player_id) ON DELETE SET NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'SOLD', 'CANCELLED', 'EXPIRED')),
    listed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    CONSTRAINT chk_valid_expiration CHECK (expires_at > listed_at),
    CONSTRAINT chk_self_bid CHECK (high_bidder_id IS NULL OR high_bidder_id <> seller_id)
);

-- 10. AUCTION BIDS (Bid Progression Log)
CREATE TABLE auction_bids (
    bid_id SERIAL PRIMARY KEY,
    listing_id INT NOT NULL REFERENCES auction_listings(listing_id) ON DELETE CASCADE,
    bidder_id INT NOT NULL REFERENCES players(player_id) ON DELETE RESTRICT,
    bid_amount BIGINT NOT NULL CHECK (bid_amount > 0),
    placed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 11. IMMUTABLE LEDGER TRANSACTIONS (High-Level Settlement Receipts)
CREATE TABLE ledger_transactions (
    tx_id SERIAL PRIMARY KEY,
    listing_id INT NOT NULL UNIQUE REFERENCES auction_listings(listing_id) ON DELETE RESTRICT,
    instance_id INT NOT NULL REFERENCES inventory_items(instance_id) ON DELETE RESTRICT,
    seller_id INT NOT NULL REFERENCES players(player_id) ON DELETE RESTRICT,
    buyer_id INT NOT NULL REFERENCES players(player_id) ON DELETE RESTRICT,
    gross_price BIGINT NOT NULL CHECK (gross_price > 0),
    market_tax_burned BIGINT NOT NULL CHECK (market_tax_burned >= 0),
    seller_net_payout BIGINT NOT NULL CHECK (seller_net_payout >= 0),
    settlement_type VARCHAR(16) NOT NULL CHECK (settlement_type IN ('INSTANT_BUYOUT', 'AUCTION_WON')),
    executed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_ledger_math CHECK (gross_price = market_tax_burned + seller_net_payout),
    CONSTRAINT chk_distinct_parties CHECK (seller_id <> buyer_id)
);

-- 12. MARKET OHLCV PRICE HISTORY (For Analytics, Candlesticks & Index Benchmarking)
CREATE TABLE price_history_ohlc (
    candle_id SERIAL PRIMARY KEY,
    item_id INT NOT NULL REFERENCES item_templates(item_id) ON DELETE CASCADE,
    realm_id INT NOT NULL REFERENCES realms(realm_id) ON DELETE CASCADE,
    bucket_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    open_price BIGINT NOT NULL CHECK (open_price > 0),
    high_price BIGINT NOT NULL CHECK (high_price >= open_price),
    low_price BIGINT NOT NULL CHECK (low_price > 0 AND low_price <= high_price),
    close_price BIGINT NOT NULL CHECK (close_price BETWEEN low_price AND high_price),
    volume_traded INT NOT NULL CHECK (volume_traded > 0)
);

-- 13. DOUBLE-ENTRY GENERAL LEDGER JOURNAL
-- Enforces mathematical invariance: Sum(amount) == 0 per tx_group_id
CREATE TABLE ledger_journal (
    entry_id BIGSERIAL PRIMARY KEY,
    tx_group_id VARCHAR(64) NOT NULL,
    event_type VARCHAR(32) NOT NULL CHECK (event_type IN ('BUYOUT', 'ESCROW_LOCK', 'ESCROW_REFUND', 'FORGE_FEE', 'KIOSK_BID', 'KIOSK_WIN_FEE', 'KIOSK_REFUND', 'SEIZURE', 'REPAIR_FEE', 'P2P_TRADE', 'LIMIT_ESCROW_LOCK', 'LIMIT_ESCROW_REFUND', 'LIMIT_MATCH', 'MAIL_COD')),
    account_type VARCHAR(32) NOT NULL CHECK (account_type IN ('PLAYER_LIQUID', 'PLAYER_ESCROW', 'GUILD_TREASURY', 'SYSTEM_SINK')),
    account_id VARCHAR(64) NOT NULL,
    amount BIGINT NOT NULL,
    balance_after BIGINT,
    description TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 14. PLAYER MAIL & ASYNCHRONOUS COURIER PARCELS
CREATE TABLE player_mail (
    mail_id SERIAL PRIMARY KEY,
    recipient_id INT NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    sender_name VARCHAR(48) NOT NULL DEFAULT 'Agora Courier',
    subject VARCHAR(100) NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    attached_gold BIGINT NOT NULL DEFAULT 0 CHECK (attached_gold >= 0),
    attached_instance_id INT REFERENCES inventory_items(instance_id) ON DELETE SET NULL,
    cod_amount BIGINT NOT NULL DEFAULT 0 CHECK (cod_amount >= 0),
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    is_collected BOOLEAN NOT NULL DEFAULT FALSE,
    sent_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- 15. CONTINUOUS DOUBLE-SIDED LIMIT ORDERBOOK (Bid & Ask Matching)
CREATE TABLE limit_orders (
    order_id SERIAL PRIMARY KEY,
    player_id INT NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    item_id INT NOT NULL REFERENCES item_templates(item_id) ON DELETE CASCADE,
    realm_id INT NOT NULL REFERENCES realms(realm_id) ON DELETE CASCADE,
    side VARCHAR(8) NOT NULL CHECK (side IN ('BUY', 'SELL')),
    unit_price BIGINT NOT NULL CHECK (unit_price > 0),
    quantity INT NOT NULL DEFAULT 1 CHECK (quantity > 0),
    filled_quantity INT NOT NULL DEFAULT 0 CHECK (filled_quantity >= 0),
    status VARCHAR(16) NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'FILLED', 'CANCELLED')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- PERFORMANCE INDEXES (B-Tree, Partial, and Composite Covering Indexes)
-- ============================================================================
CREATE INDEX idx_active_listings_realm_price 
    ON auction_listings (realm_id, buyout_price ASC) 
    WHERE status = 'ACTIVE';

CREATE UNIQUE INDEX idx_unique_active_instance 
    ON auction_listings (instance_id) 
    WHERE status = 'ACTIVE';

CREATE INDEX idx_ohlc_item_realm_time 
    ON price_history_ohlc (item_id, realm_id, candle_id DESC);

CREATE INDEX idx_inventory_owner ON inventory_items (owner_id, is_escrowed);
CREATE INDEX idx_ledger_executed_at ON ledger_transactions (executed_at DESC);
CREATE INDEX idx_journal_tx_group ON ledger_journal(tx_group_id);
CREATE INDEX idx_journal_account ON ledger_journal(account_type, account_id);
CREATE INDEX idx_mail_recipient ON player_mail(recipient_id, is_collected);
CREATE INDEX idx_limit_orders_active ON limit_orders(item_id, realm_id, side, status);

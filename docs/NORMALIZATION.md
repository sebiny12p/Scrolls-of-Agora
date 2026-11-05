# Relational Schema Design & Normalization Analysis
**Project:** Scrolls of Agora — Decentralized MMORPG Guild Exchange  
**Course:** Relational Database Systems (IST DB1 / University Database Curriculum)  
**Author:** Sebastian Paris (@sebiny12p)  

---

## 1. Relational Database Design Principles

The *Scrolls of Agora* relational schema is engineered to satisfy the rigorous data integrity requirements of a multi-hub virtual economy. The system models physical item ownership, double-entry financial accounting, spatial regional orderbooks, and sealed-bid leasing.

To eliminate data redundancy, update anomalies, insertion anomalies, and deletion anomalies, every relation in the schema was designed under formal Functional Dependency ($F$) constraints and evaluated against **Third Normal Form (3NF)** and **Boyce-Codd Normal Form (BCNF)**.

```mermaid
erDiagram
    TRADE_GUILDS |o--o{ REALMS : "controls_kiosk"
    TRADE_GUILDS ||--o{ KIOSK_BIDS : "submits_bid"
    TRADE_GUILDS |o--o{ PLAYERS : "enrolls"
    REALMS ||--o{ KIOSK_BIDS : "auctions_lease"
    REALMS ||--o{ PLAYERS : "hosts"
    REALMS ||--o{ AUCTION_LISTINGS : "operates_kiosk"
    REALMS ||--o{ PRICE_HISTORY_OHLC : "records_candles"

    PLAYERS ||--o{ INVENTORY_ITEMS : "owns"
    PLAYERS ||--o{ AUCTION_LISTINGS : "sells"
    PLAYERS ||--o{ AUCTION_BIDS : "places"

    ITEM_TEMPLATES ||--o| EQUIPMENT_SPECS : "ISA_Equipment"
    ITEM_TEMPLATES ||--o| CONSUMABLE_SPECS : "ISA_Consumable"
    ITEM_TEMPLATES ||--o{ INVENTORY_ITEMS : "instantiates"
    ITEM_TEMPLATES ||--o{ PRICE_HISTORY_OHLC : "tracks"

    INVENTORY_ITEMS ||--o{ ITEM_INSTANCE_ENCHANTMENTS : "binds"
    ENCHANTMENTS ||--o{ ITEM_INSTANCE_ENCHANTMENTS : "applied_to"

    INVENTORY_ITEMS ||--o| AUCTION_LISTINGS : "escrowed_in"
    AUCTION_LISTINGS ||--o{ AUCTION_BIDS : "receives"
    AUCTION_LISTINGS ||--o| LEDGER_TRANSACTIONS : "settles_in"

    LEDGER_JOURNAL {
        bigint entry_id PK
        string tx_group_id
        string event_type
        string account_type
        string account_id
        bigint amount
        bigint balance_after
        string description
    }
```

---

## 2. Table-by-Table Normal Form & Functional Dependency Analysis

### 2.1 Relation: `trade_guilds`
* **Attributes:** `(guild_id, guild_name, alliance, banner_crest, treasury_gold, tax_dividend_earned)`
* **Candidate Keys:** `{guild_id}`, `{guild_name}`
* **Primary Key:** `guild_id`
* **Functional Dependencies ($F$):**
  1. $\text{guild\_id} \to \text{guild\_name, alliance, banner\_crest, treasury\_gold, tax\_dividend\_earned}$
  2. $\text{guild\_name} \to \text{guild\_id, alliance, banner\_crest, treasury\_gold, tax\_dividend\_earned}$
* **Normal Form Evaluation:**
  * **1NF:** All attribute domains are atomic (scalars). Satisfied.
  * **2NF:** No non-prime attribute is partially dependent on any candidate key (candidate keys are single attributes). Satisfied.
  * **3NF:** For all non-trivial dependencies $X \to Y$, $X$ is a superkey. There are no transitive dependencies. Satisfied.
  * **BCNF:** For every functional dependency $X \to Y$, $X$ is a superkey. **Satisfies BCNF.**

---

### 2.2 Relation: `realms`
* **Attributes:** `(realm_id, realm_name, province, region, map_x, map_y, controlling_guild_id, population_cap, tax_rate_bps)`
* **Candidate Keys:** `{realm_id}`, `{realm_name}`
* **Primary Key:** `realm_id`
* **Foreign Keys:** `controlling_guild_id REFERENCES trade_guilds(guild_id)`
* **Functional Dependencies ($F$):**
  1. $\text{realm\_id} \to \text{realm\_name, province, region, map\_x, map\_y, controlling\_guild\_id, population\_cap, tax\_rate\_bps}$
  2. $\text{realm\_name} \to \text{realm\_id, province, region, map\_x, map\_y, controlling\_guild\_id, population\_cap, tax\_rate\_bps}$
* **Normal Form Evaluation:**
  * Every determinant is a candidate key. **Satisfies BCNF.**

---

### 2.3 Relations: `item_templates`, `equipment_specs`, and `consumable_specs` (ISA Specialization)

#### Problem Formulation:
Items share common attributes (name, vendor value, rarity, level requirement), but Equipment possesses combat ratings (attack power, armor rating, sockets, durability), whereas Consumables possess chemical effects (potency, duration, cooldown). 

#### Naive Anti-Pattern (Wide Table with NULLs):
Lumping all attributes into a single table `items(..., attack_power, effect_potency, duration)` violates 2NF/3NF through partial domain applicability and creates sparse storage with hundreds of `NULL` fields.

#### Chosen Design: Class Hierarchy Mapping via Shared Primary Key (BCNF)
* **Supertype:** `item_templates(item_id, item_name, icon_key, lore_text, category, rarity, base_vendor_value, max_stack, required_level)`
  * Key: `{item_id}`, `{item_name}`
  * Dependencies: $\text{item\_id} \to \text{all other attributes}$ (**BCNF**)
* **Subtype 1:** `equipment_specs(item_id, equip_slot, attack_power, armor_rating, max_durability, socket_count)`
  * Key: `{item_id}` (FK references `item_templates.item_id`)
  * Dependencies: $\text{item\_id} \to \text{equip\_slot, attack\_power, armor\_rating, max\_durability, socket\_count}$ (**BCNF**)
* **Subtype 2:** `consumable_specs(item_id, effect_type, effect_potency, duration_seconds, cooldown_seconds)`
  * Key: `{item_id}` (FK references `item_templates.item_id`)
  * Dependencies: $\text{item\_id} \to \text{effect\_type, effect\_potency, duration\_seconds, cooldown\_seconds}$ (**BCNF**)

**Decomposition Properties:**
* **Lossless Join:** `item_templates` $\bowtie$ `equipment_specs` on `item_id` reconstructs complete equipment records without extraneous or lost tuples.
* **Dependency Preservation:** All functional dependencies are preserved within their respective relations.

---

### 2.4 Relation: `inventory_items` (Physical Item Instances)
* **Attributes:** `(instance_id, item_id, owner_id, mint_serial, temper_tier, bonus_power, stack_size, current_durability, is_escrowed, minted_at)`
* **Candidate Keys:** `{instance_id}`, `{mint_serial}`
* **Primary Key:** `instance_id`
* **Foreign Keys:**
  * `item_id REFERENCES item_templates(item_id)`
  * `owner_id REFERENCES players(player_id)`
* **Functional Dependencies ($F$):**
  1. $\text{instance\_id} \to \text{item\_id, owner\_id, mint\_serial, temper\_tier, bonus\_power, stack\_size, current\_durability, is\_escrowed, minted\_at}$
  2. $\text{mint\_serial} \to \text{instance\_id, ...}$
* **Normal Form Evaluation:**
  * Both determinants are candidate keys. **Satisfies BCNF.**

---

### 2.5 Relation: `item_instance_enchantments` (M:N Junction)
* **Attributes:** `(instance_id, enchant_id, applied_at)`
* **Composite Primary Key:** `(instance_id, enchant_id)`
* **Foreign Keys:**
  * `instance_id REFERENCES inventory_items(instance_id)`
  * `enchant_id REFERENCES enchantments(enchant_id)`
* **Functional Dependencies ($F$):**
  * $\text{\{instance\_id, enchant\_id\}} \to \text{applied\_at}$
* **Normal Form Evaluation:**
  * The only determinant is the composite candidate key. **Satisfies BCNF.**

---

### 2.6 Relation: `ledger_transactions` (Immutable Financial Audit)
* **Attributes:** `(tx_id, listing_id, instance_id, seller_id, buyer_id, gross_price, market_tax_burned, seller_net_payout, settlement_type, executed_at)`
* **Candidate Keys:** `{tx_id}`, `{listing_id}` (each listing settles at most once)
* **Primary Key:** `tx_id`
* **Functional Dependencies ($F$):**
  1. $\text{tx\_id} \to \text{listing\_id, instance\_id, seller\_id, buyer\_id, gross\_price, market\_tax\_burned, seller\_net\_payout, settlement\_type, executed\_at}$
  2. $\text{listing\_id} \to \text{tx\_id, ...}$
* **Integrity Constraint (Double-Entry Balance):**
  $$\text{gross\_price} = \text{market\_tax\_burned} + \text{seller\_net\_payout}$$
  Enforced via table-level `CHECK (gross_price = market_tax_burned + seller_net_payout)`.
* **Normal Form:** **Satisfies BCNF.**

---

## 3. Intentional Engineering Denormalizations (Trade-Off Justifications)

In production relational database engineering, selective denormalization is occasionally introduced when mathematical normalization introduces unsustainable latency on critical high-frequency read paths.

| Denormalized Field | Table | Pure Normalized Alternative | Engineering Justification |
| :--- | :--- | :--- | :--- |
| `current_bid` | `auction_listings` | $\text{MAX}(\text{bid\_amount})$ from `auction_bids` | Under pure 3NF, displaying 100 active listings on the market orderbook requires 100 subqueries or an aggregation join against the historical `auction_bids` table. Caching `current_bid` on the parent listing eliminates join overhead on the orderbook read path. Inconsistency is prevented via an atomic transaction that updates `current_bid` and inserts to `auction_bids` in the same commit. |
| `high_bidder_id` | `auction_listings` | Subquery on `auction_bids` | Required for constant-time ($O(1)$) escrow refund lookups when outbidding occurs. Eliminates scanning `auction_bids` during high-concurrency bidding. |
| `price_history_ohlc` | `price_history_ohlc` | Dynamic aggregation across `ledger_transactions` | Computing 24-hour candlestick Open, High, Low, Close, and Volume from raw ledger transactions requires scanning millions of historical transaction tuples per API request. Pre-aggregating into an OLAP rollup table provides sub-millisecond response times for frontend market telemetry. |

---

## 4. Summary Table of Normal Forms

| Table | Primary Key | Candidate Keys | Normal Form | Foreign Keys |
| :--- | :--- | :--- | :--- | :--- |
| `trade_guilds` | `guild_id` | `guild_id`, `guild_name` | **BCNF** | 0 |
| `realms` | `realm_id` | `realm_id`, `realm_name` | **BCNF** | 1 (`controlling_guild_id`) |
| `kiosk_bids` | `kiosk_bid_id` | `kiosk_bid_id` | **BCNF** | 2 (`realm_id`, `guild_id`) |
| `players` | `player_id` | `player_id`, `username` | **BCNF** | 2 (`realm_id`, `guild_id`) |
| `item_templates` | `item_id` | `item_id`, `item_name` | **BCNF** | 0 |
| `equipment_specs` | `item_id` | `item_id` | **BCNF** | 1 (`item_id`) |
| `consumable_specs`| `item_id` | `item_id` | **BCNF** | 1 (`item_id`) |
| `inventory_items` | `instance_id` | `instance_id`, `mint_serial` | **BCNF** | 2 (`item_id`, `owner_id`) |
| `enchantments` | `enchant_id` | `enchant_id`, `enchant_name` | **BCNF** | 0 |
| `item_instance_enchantments` | `(instance_id, enchant_id)` | `(instance_id, enchant_id)` | **BCNF** | 2 (`instance_id`, `enchant_id`) |
| `auction_listings` | `listing_id` | `listing_id` | **3NF** (Denormalized `current_bid`) | 4 (`instance_id`, `seller_id`, `realm_id`, `high_bidder_id`) |
| `auction_bids` | `bid_id` | `bid_id` | **BCNF** | 2 (`listing_id`, `bidder_id`) |
| `ledger_transactions` | `tx_id` | `tx_id`, `listing_id` | **BCNF** | 4 (`listing_id`, `instance_id`, `seller_id`, `buyer_id`) |
| `price_history_ohlc` | `candle_id` | `candle_id` | **3NF** (OLAP Rollup) | 2 (`item_id`, `realm_id`) |
| `ledger_journal` | `entry_id` | `entry_id` | **BCNF** | 0 (Polymorphic chart-of-accounts) |

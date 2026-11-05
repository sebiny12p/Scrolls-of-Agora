// =========================================================================
// CUSTOM VECTOR GAME ARTWORK (ZERO EMOJIS)
// =========================================================================
const ITEM_SVGS = {
  runeblade: `<svg viewBox="0 0 32 32" fill="none">
    <path d="M26 4L10 20L7 17L23 1L26 4Z" fill="#ff2e55" fill-opacity="0.25"/>
    <path d="M27 3L11 19M27 3L23 3M27 3L27 7" stroke="#ff2e55" stroke-width="2.2" stroke-linecap="round"/>
    <path d="M13 15L17 19M7 15L17 25" stroke="#d4a853" stroke-width="2.2" stroke-linecap="round"/>
    <path d="M9 23L5 27L3 25L7 21" stroke="#cbd5e1" stroke-width="2" stroke-linecap="round"/>
    <circle cx="19" cy="11" r="1.5" fill="#fff"/>
  </svg>`,
  shield: `<svg viewBox="0 0 32 32" fill="none">
    <path d="M16 3L5 7.5V15.5C5 22.4 9.7 27.9 16 30C22.3 27.9 27 22.4 27 15.5V7.5L16 3Z" fill="#ff8c1a" fill-opacity="0.18" stroke="#ff8c1a" stroke-width="2"/>
    <path d="M16 7V25M10 14H22" stroke="#f2c96d" stroke-width="1.8"/>
  </svg>`,
  dagger: `<svg viewBox="0 0 32 32" fill="none">
    <path d="M25 5L12 18L9 15L22 2L25 5Z" fill="#a855f7" fill-opacity="0.25"/>
    <path d="M25 5L11 19" stroke="#e9d5ff" stroke-width="2" stroke-linecap="round"/>
    <path d="M8 14L16 22" stroke="#d4a853" stroke-width="2" stroke-linecap="round"/>
    <path d="M9 21L5 25" stroke="#94a3b8" stroke-width="2.4" stroke-linecap="round"/>
  </svg>`,
  crown: `<svg viewBox="0 0 32 32" fill="none">
    <path d="M4 22L7 10L13 16L16 8L19 16L25 10L28 22H4Z" fill="#a855f7" fill-opacity="0.22" stroke="#c084fc" stroke-width="2" stroke-linejoin="round"/>
    <circle cx="16" cy="17" r="2" fill="#38bdf8"/>
  </svg>`,
  chestplate: `<svg viewBox="0 0 32 32" fill="none">
    <path d="M9 5L5 9L7 15H10V27H22V15H25L27 9L23 5L19 8H13L9 5Z" fill="#a855f7" fill-opacity="0.18" stroke="#c084fc" stroke-width="2" stroke-linejoin="round"/>
    <path d="M16 9V25" stroke="#d4a853" stroke-width="1.5"/>
  </svg>`,
  ring: `<svg viewBox="0 0 32 32" fill="none">
    <circle cx="16" cy="18" r="8" stroke="#f2c96d" stroke-width="2.4"/>
    <polygon points="16,5 20,10 16,13 12,10" fill="#a855f7" stroke="#e9d5ff" stroke-width="1.2"/>
  </svg>`,
  greatsword: `<svg viewBox="0 0 32 32" fill="none">
    <path d="M26 4L9 21" stroke="#60a5fa" stroke-width="2.6" stroke-linecap="round"/>
    <path d="M6 16L16 26" stroke="#d4a853" stroke-width="2.2" stroke-linecap="round"/>
    <path d="M8 22L4 26" stroke="#94a3b8" stroke-width="2.4" stroke-linecap="round"/>
  </svg>`,
  flask: `<svg viewBox="0 0 32 32" fill="none">
    <path d="M13 4H19M14 4V11L7 23C6.2 24.5 7.3 27 9.2 27H22.8C24.7 27 25.8 24.5 25 23L18 11V4" stroke="#c084fc" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M8.5 21H23.5L25 24C25.4 25 24.5 26.5 23 26.5H9C7.5 26.5 6.6 25 7 24L8.5 21Z" fill="#a855f7" fill-opacity="0.45"/>
  </svg>`,
  potion: `<svg viewBox="0 0 32 32" fill="none">
    <path d="M13 5H19M14 5V12L9 20V26H23V20L18 12V5" stroke="#38bdf8" stroke-width="2" stroke-linejoin="round"/>
    <rect x="10" y="19" width="12" height="6" fill="#38bdf8" fill-opacity="0.35"/>
  </svg>`,
  vial: `<svg viewBox="0 0 32 32" fill="none">
    <rect x="11" y="7" width="10" height="19" rx="3" stroke="#22c55e" stroke-width="2"/>
    <rect x="12.5" y="15" width="7" height="9.5" rx="1.5" fill="#22c55e" fill-opacity="0.4"/>
  </svg>`,
  crystal: `<svg viewBox="0 0 32 32" fill="none">
    <polygon points="16,3 25,12 21,28 11,28 7,12" fill="#a855f7" fill-opacity="0.28" stroke="#e879f9" stroke-width="2" stroke-linejoin="round"/>
    <path d="M16 3L16 28M7 12L25 12" stroke="#f0abfc" stroke-width="1.2"/>
  </svg>`,
  ore: `<svg viewBox="0 0 32 32" fill="none">
    <polygon points="8,24 5,14 13,7 23,9 27,18 21,26" fill="#3b82f6" fill-opacity="0.25" stroke="#60a5fa" stroke-width="2"/>
    <circle cx="14" cy="15" r="2" fill="#93c5fd"/>
    <circle cx="20" cy="18" r="1.5" fill="#f2c96d"/>
  </svg>`,
  artifact: `<svg viewBox="0 0 32 32" fill="none">
    <circle cx="16" cy="16" r="10" fill="#ff2e55" fill-opacity="0.2" stroke="#ff2e55" stroke-width="2"/>
    <ellipse cx="16" cy="16" rx="4" ry="8" stroke="#f2c96d" stroke-width="1.8"/>
    <circle cx="16" cy="16" r="2.2" fill="#fff"/>
  </svg>`
};

function getItemSvg(key) {
  return ITEM_SVGS[key] || ITEM_SVGS.runeblade;
}

// =========================================================================
// APPLICATION STATE
// =========================================================================
let marketState = null;
let activePlayerId = 1005;
let selectedRealmId = 0; // 0 = All Tamriel Hubs
let selectedListing = null;
let selectedBagItem = null;
let simTimer = null;

function notify(msg, isErr = false) {
  const el = document.getElementById('statusBanner');
  el.style.display = 'block';
  el.style.borderColor = isErr ? '#ef4444' : '#d4a853';
  el.style.color = isErr ? '#fca5a5' : '#e6eaf2';
  el.innerHTML = (isErr ? '<span style="color:#f87171; font-weight:700;">Action Failed:</span> ' : '<span style="color:var(--brass-bright); font-weight:700;">Action Confirmed:</span> ') + msg;
  clearTimeout(window._nTimer);
  window._nTimer = setTimeout(() => { el.style.display = 'none'; }, 4500);
}

// =========================================================================
// RPG HOVER TOOLTIP ENGINE
// =========================================================================
const tooltipEl = document.getElementById('rpgTooltip');

function showRpgTooltip(ev, itemData) {
  const temperStr = itemData.temper_tier > 0 ? ` (+${itemData.temper_tier} Tempered)` : '';
  const statHtml = itemData.equip_slot
    ? `<div class="tt-stat-line">${itemData.equip_slot} Equipment ${temperStr}</div>
       ${itemData.attack_power > 0 ? `<div class="tt-stat-line" style="color:#f2c96d;">+${itemData.attack_power.toLocaleString()} Attack Power ${itemData.bonus_power > 0 ? `(includes +${itemData.bonus_power} Refined)` : ''}</div>` : ''}
       ${itemData.armor_rating > 0 ? `<div class="tt-stat-line" style="color:#93c5fd;">+${itemData.armor_rating.toLocaleString()} Armor Rating</div>` : ''}
       ${itemData.socket_count > 0 ? `<div class="tt-stat-line" style="color:#a3e635;">Enchantment Sockets: ${itemData.socket_count}</div>` : ''}`
    : (itemData.effect_type
        ? `<div class="tt-stat-line">Effect: ${itemData.effect_type} (+${itemData.effect_potency} Potency)</div>`
        : `<div class="tt-stat-line">Refinement Reagent</div>`);

  tooltipEl.innerHTML = `
    <div class="tt-header">
      <div class="item-slot slot-${itemData.rarity}">
        ${getItemSvg(itemData.icon_key)}
      </div>
      <div>
        <div class="tt-title text-${itemData.rarity}">${itemData.item_name}${temperStr}</div>
        <div class="tt-type">${itemData.rarity} ${itemData.category} · Requires Level ${itemData.required_level}</div>
      </div>
    </div>
    ${statHtml}
    ${itemData.enchants ? `<div class="tt-enchant">Active Glyphs: ${itemData.enchants}</div>` : ''}
    ${itemData.lore_text ? `<div class="tt-lore">"${itemData.lore_text}"</div>` : ''}
    <div class="tt-serial">
      <span>Serial: ${itemData.mint_serial}</span>
      <span>Base Value: ${itemData.base_vendor_value.toLocaleString()} gold</span>
    </div>
  `;
  tooltipEl.style.display = 'block';
  moveRpgTooltip(ev);
}

function moveRpgTooltip(ev) {
  const pad = 16;
  let x = ev.clientX + pad;
  let y = ev.clientY + pad;
  if (x + 330 > window.innerWidth) x = ev.clientX - 335;
  if (y + 250 > window.innerHeight) y = ev.clientY - 230;
  tooltipEl.style.left = x + 'px';
  tooltipEl.style.top = y + 'px';
}

function hideRpgTooltip() {
  tooltipEl.style.display = 'none';
}

// =========================================================================
// HTML5 CANVAS 24H CANDLESTICK & VOLUME RENDERER
// =========================================================================
async function renderItemChart(itemId) {
  const res = await fetch('/api/candles/' + itemId);
  const data = await res.json();
  const candles = data.candles || [];

  const canvas = document.getElementById('ohlcCanvas');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);

  const W = rect.width;
  const H = rect.height;
  ctx.clearRect(0, 0, W, H);

  document.getElementById('chartTitleLabel').textContent =
    `${data.item_name} — 24h Price Action`;

  if (candles.length === 0) return;

  const minP = Math.min(...candles.map(c => c.low_price)) * 0.985;
  const maxP = Math.max(...candles.map(c => c.high_price)) * 1.015;
  const maxV = Math.max(...candles.map(c => c.volume_traded), 1);

  const lastC = candles[candles.length - 1];
  const firstC = candles[0];
  const pctChange = (((lastC.close_price - firstC.open_price) / firstC.open_price) * 100).toFixed(1);
  const sign = pctChange >= 0 ? '+' : '';
  document.getElementById('chartSpreadLabel').innerHTML =
    `Latest: ${lastC.close_price.toLocaleString()}g (${sign}${pctChange}%)`;

  const padLeft = 6;
  const padRight = 56;
  const padTop = 8;
  const padBot = 20;
  const plotW = W - padLeft - padRight;
  const plotH = H - padTop - padBot;

  ctx.strokeStyle = 'rgba(42, 51, 71, 0.45)';
  ctx.lineWidth = 1;
  ctx.font = '9.5px Inter, sans-serif';
  ctx.fillStyle = '#556075';
  for (let i = 0; i <= 3; i++) {
    const y = padTop + (plotH / 3) * i;
    ctx.beginPath();
    ctx.moveTo(padLeft, y);
    ctx.lineTo(W - padRight, y);
    ctx.stroke();
    const priceVal = Math.round(maxP - ((maxP - minP) / 3) * i);
    ctx.fillText(priceVal.toLocaleString() + 'g', W - padRight + 5, y + 3);
  }

  const stepX = plotW / candles.length;
  const candleW = Math.max(3.5, stepX * 0.56);

  candles.forEach((c, idx) => {
    const cx = padLeft + idx * stepX + stepX / 2;
    const isBull = c.close_price >= c.open_price;
    const color = isBull ? '#10b981' : '#ef4444';

    const vHeight = (c.volume_traded / maxV) * (plotH * 0.28);
    ctx.fillStyle = isBull ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.12)';
    ctx.fillRect(cx - candleW / 2, padTop + plotH - vHeight, candleW, vHeight);

    const yHigh = padTop + ((maxP - c.high_price) / (maxP - minP)) * plotH;
    const yLow = padTop + ((maxP - c.low_price) / (maxP - minP)) * plotH;
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.moveTo(cx, yHigh);
    ctx.lineTo(cx, yLow);
    ctx.stroke();

    const yOpen = padTop + ((maxP - c.open_price) / (maxP - minP)) * plotH;
    const yClose = padTop + ((maxP - c.close_price) / (maxP - minP)) * plotH;
    const topY = Math.min(yOpen, yClose);
    const bodyH = Math.max(2, Math.abs(yClose - yOpen));
    ctx.fillStyle = color;
    ctx.fillRect(cx - candleW / 2, topY, candleW, bodyH);

    if (idx % 5 === 0) {
      ctx.fillStyle = '#556075';
      ctx.fillText(c.bucket_timestamp.slice(0, 5), cx - 12, H - 4);
    }
  });
}

// =========================================================================
// MAIN DATA REFRESH & RENDERING
// =========================================================================
async function loadState() {
  const res = await fetch(`/api/state?player_id=${activePlayerId}&realm_id=${selectedRealmId}`);
  marketState = await res.json();

  // Topbar Telemetry
  const k = marketState.kpis;
  document.getElementById('mActiveOrders').textContent = k.active_orders;
  document.getElementById('mVolume').textContent = k.total_volume.toLocaleString() + 'g';
  document.getElementById('mTaxBurn').textContent = k.total_tax_burned.toLocaleString() + 'g';
  document.getElementById('mEscrow').textContent = k.total_escrow_locked.toLocaleString() + 'g';
  document.getElementById('mSerials').textContent = k.items_duplicated > 0 ? `${k.items_duplicated} Duplicates` : 'Verified 1:1';
  document.getElementById('engineBadge').textContent = 'SQLite · Row-Level Locks';

  // Render Interactive 5-Hub Tamriel Map
  renderTamrielMap();

  // Render Hub Filter Pills
  const pillsEl = document.getElementById('hubFilterPills');
  pillsEl.innerHTML = `<button class="hub-pill ${selectedRealmId === 0 ? 'active' : ''}" onclick="selectHubFilter(0)">All Posts (${k.active_orders})</button>` +
    marketState.realms.map(r =>
      `<button class="hub-pill ${selectedRealmId === r.realm_id ? 'active' : ''}" onclick="selectHubFilter(${r.realm_id})">
        ${r.realm_name} (${r.active_listings_count})
      </button>`
    ).join('');

  // Populate Selects in Drawer & Kiosk Bid Box
  const hubOpts = marketState.realms.map(r => `<option value="${r.realm_id}">${r.realm_name} (${(r.tax_rate_bps/100).toFixed(1)}% Tax)</option>`).join('');
  document.getElementById('listHubSelect').innerHTML = hubOpts;
  document.getElementById('kioskBidHub').innerHTML = hubOpts;

  const guildOpts = marketState.guilds.map(g => `<option value="${g.guild_id}">${g.guild_name} (${(g.treasury_gold/1000).toFixed(0)}k treasury)</option>`).join('');
  document.getElementById('kioskBidGuild').innerHTML = guildOpts;

  const glyphOpts = marketState.enchantments.map(e => `<option value="${e.enchant_id}">${e.enchant_name} (+${e.bonus_value} ${e.stat_type})</option>`).join('');
  document.getElementById('forgeGlyphSelect').innerHTML = glyphOpts;

  // Character Selector
  const sel = document.getElementById('traderSelect');
  sel.innerHTML = marketState.players.map(p =>
    `<option value="${p.player_id}" ${p.player_id == activePlayerId ? 'selected' : ''}>
      ${p.username.replace(/_/g, ' ')} — Level ${p.level} ${p.character_class} (${p.realm_name})
    </option>`
  ).join('');
  sel.onchange = () => {
    activePlayerId = parseInt(sel.value, 10);
    closeListDrawer();
    loadState();
  };

  const activePlayerObj = marketState.players.find(p => p.player_id == activePlayerId) || marketState.players[0];
  if (activePlayerObj) {
    activePlayerId = activePlayerObj.player_id;
    document.getElementById('activeLiquidGold').textContent = activePlayerObj.gold_balance.toLocaleString() + 'g';
    document.getElementById('activeEscrowGold').textContent = activePlayerObj.escrow_gold.toLocaleString() + 'g';
  }

  // Default Selected Listing
  if (!selectedListing || !marketState.listings.find(l => l.listing_id === selectedListing.listing_id)) {
    selectedListing = marketState.listings[0] || null;
  } else {
    selectedListing = marketState.listings.find(l => l.listing_id === selectedListing.listing_id);
  }
  renderSelectedItemDeck();

  // Render Orderbook Rows
  const tbody = document.getElementById('orderbookTbody');
  tbody.innerHTML = marketState.listings.map((l, idx) => {
    const isSel = selectedListing && selectedListing.listing_id === l.listing_id;
    const temperTag = l.temper_tier > 0 ? ` +${l.temper_tier}` : '';
    const specStr = l.equip_slot
      ? `${l.equip_slot} · ${l.attack_power > 0 ? l.attack_power + ' ATK' : l.armor_rating + ' ARM'}`
      : (l.effect_type ? `${l.effect_type} (+${l.effect_potency})` : l.category);
    const minNextBid = l.current_bid === 0 ? l.start_price : Math.floor(l.current_bid * 1.05) + 1;

    let ttcHtml = `<span style="font-family:var(--font-mono); font-size:10px; color:var(--text-dim);">Regional Floor</span>`;
    if (l.buyout_price && l.other_hub_max_price && l.other_hub_max_price > l.buyout_price * 1.12) {
      const spreadPct = Math.round(((l.other_hub_max_price - l.buyout_price) / l.buyout_price) * 100);
      ttcHtml = `<span class="ttc-arb-badge" title="Flip at ${l.arbitrage_target_hub} for ${l.other_hub_max_price.toLocaleString()}g">+${spreadPct}% in ${l.arbitrage_target_hub}</span>`;
    }

    return `
      <tr class="${isSel ? 'selected-row' : ''}" onclick="selectOrderRow(${idx})">
        <td style="font-family:var(--font-mono); color:var(--text-dim);">#${l.listing_id}</td>
        <td>
          <div class="item-cell">
            <div class="item-slot slot-${l.rarity}"
                 onmouseenter='showRpgTooltip(event, ${JSON.stringify(l).replace(/'/g, "&#39;")})'
                 onmousemove="moveRpgTooltip(event)"
                 onmouseleave="hideRpgTooltip()">
              ${l.temper_tier > 0 ? `<span class="temper-badge">+${l.temper_tier}</span>` : ''}
              ${getItemSvg(l.icon_key)}
              ${l.stack_size > 1 ? `<span class="stack-count">${l.stack_size}</span>` : ''}
            </div>
            <div>
              <div class="item-name-line text-${l.rarity}">${l.item_name}${temperTag}</div>
              <div class="item-sub-line">
                <span class="mint-badge">${l.mint_serial}</span>
                ${l.enchants ? `<span style="color:#34d399;">[Glyph]</span>` : ''}
              </div>
            </div>
          </div>
        </td>
        <td style="font-family:var(--font-mono); font-size:10.5px; color:var(--text-secondary);">
          ${specStr}
        </td>
        <td>
          <div style="font-weight:600; font-size:11.5px; color:var(--text-primary);">${l.realm_name}</div>
          <div style="font-family:var(--font-mono); font-size:9.5px; color:var(--brass);">${l.kiosk_guild_name || 'Independent'} (${(l.tax_rate_bps/100).toFixed(1)}%)</div>
        </td>
        <td>${ttcHtml}</td>
        <td>
          ${l.current_bid > 0
            ? `<div style="font-family:var(--font-mono); font-weight:700; color:var(--cyan);">${l.current_bid.toLocaleString()}g</div>
               <div style="font-family:var(--font-mono); font-size:9.5px; color:var(--text-dim);">High: ${l.high_bidder_name.replace(/_/g, ' ')}</div>`
            : `<span style="font-family:var(--font-mono); font-size:10.5px; color:var(--text-dim);">Start: ${l.start_price.toLocaleString()}g</span>`}
        </td>
        <td>
          ${l.buyout_price
            ? `<span style="font-family:var(--font-mono); font-weight:700; color:var(--brass-bright);">${l.buyout_price.toLocaleString()}g</span>`
            : `<span style="font-family:var(--font-mono); font-size:11px; color:var(--text-dim);">--</span>`}
        </td>
        <td style="text-align:right;" onclick="event.stopPropagation();">
          <div style="display:inline-flex; gap:5px;">
            <button class="btn" style="padding:4px 8px; font-size:9.5px;" onclick="placeEscrowBid(${l.listing_id}, ${minNextBid})">
              Bid ${minNextBid.toLocaleString()}g
            </button>
            ${l.buyout_price ? `
              <button class="btn btn-brass" style="padding:4px 9px; font-size:9.5px;" onclick="executeBuyout(${l.listing_id})">
                Buy Now
              </button>
            ` : ''}
          </div>
        </td>
      </tr>
    `;
  }).join('');

  // Render 20-Slot Inventory Bag
  const bagGrid = document.getElementById('inventoryBagGrid');
  const inv = marketState.inventory || [];
  let slotsHtml = '';
  for (let i = 0; i < 20; i++) {
    if (i < inv.length) {
      const item = inv[i];
      const isBagSel = selectedBagItem && selectedBagItem.instance_id === item.instance_id;
      slotsHtml += `
        <div class="item-slot slot-${item.rarity} ${isBagSel ? 'selected-bag-slot' : ''}"
             onclick='openListDrawer(${JSON.stringify(item).replace(/'/g, "&#39;")})'
             onmouseenter='showRpgTooltip(event, ${JSON.stringify(item).replace(/'/g, "&#39;")})'
             onmousemove="moveRpgTooltip(event)"
             onmouseleave="hideRpgTooltip()">
          ${item.is_escrowed ? `<span class="escrow-tag">LISTED</span>` : ''}
          ${item.temper_tier > 0 ? `<span class="temper-badge">+${item.temper_tier}</span>` : ''}
          ${getItemSvg(item.icon_key)}
          ${item.stack_size > 1 ? `<span class="stack-count">${item.stack_size}</span>` : ''}
        </div>
      `;
    } else {
      slotsHtml += `<div class="empty-slot"></div>`;
    }
  }
  bagGrid.innerHTML = slotsHtml;

  // Render Settlement Tape
  document.getElementById('ledgerTapeList').innerHTML = marketState.ledger.map(tx => `
    <div style="background:var(--bg-panel); border:1px solid var(--border-dim); padding:7px 10px; display:flex; justify-content:space-between; align-items:center; gap:8px;">
      <div style="min-width:0; flex:1;">
        <div style="font-weight:600; font-size:11.5px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" class="text-${tx.rarity}">
          ${tx.item_name}
        </div>
        <div style="font-family:var(--font-mono); font-size:9.5px; color:var(--text-secondary); margin-top:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
          ${tx.buyer_name.replace(/_/g, ' ')} &larr; ${tx.seller_name.replace(/_/g, ' ')} · <span style="color:var(--text-dim);">${tx.realm_name}</span>
        </div>
      </div>
      <div style="text-align:right; font-family:var(--font-mono); flex-shrink:0;">
        <div style="color:var(--brass-bright); font-weight:700; font-size:11.5px;">${tx.gross_price.toLocaleString()}g</div>
        <div style="font-size:9px; color:#f87171;">Fee: -${tx.market_tax_burned.toLocaleString()}g</div>
      </div>
    </div>
  `).join('');
}

function renderTamrielMap() {
  const container = document.getElementById('tamrielMapNodes');
  const svgBg = container.querySelector('svg').outerHTML;
  const nodesHtml = marketState.realms.map(r => {
    const isAct = selectedRealmId === r.realm_id;
    const isWarzone = r.realm_name === 'Imperial City';
    return `
      <div class="hub-node ${isAct ? 'active' : ''} ${isWarzone ? 'warzone' : ''}"
           style="left:${r.map_x}%; top:${r.map_y}%;"
           onclick="selectHubFilter(${r.realm_id === selectedRealmId ? 0 : r.realm_id})">
        <div class="hub-pin"></div>
        <div class="hub-label">${r.realm_name}</div>
        <div class="hub-sub">${(r.tax_rate_bps/100).toFixed(1)}% · ${r.active_listings_count} ord</div>
      </div>
    `;
  }).join('');
  container.innerHTML = svgBg + nodesHtml;

  const footer = document.getElementById('mapFooterBar');
  const header = document.getElementById('activeHubHeader');
  if (selectedRealmId === 0) {
    header.textContent = 'ALL 5 TRADING POSTS';
    footer.innerHTML = `
      <span style="color:var(--text-secondary);">Select any trading hub node above to isolate regional listings.</span>
      <span style="color:var(--brass-bright);">5 Active Guild Charters</span>
    `;
  } else {
    const hub = marketState.realms.find(r => r.realm_id === selectedRealmId);
    if (hub) {
      header.textContent = `${hub.realm_name} (${hub.province})`;
      footer.innerHTML = `
        <span>Charter: <strong style="color:var(--brass-bright);">${hub.controlling_guild_name}</strong></span>
        <span>High Sealed Bid: <strong style="color:var(--cyan);">${hub.top_sealed_bid.toLocaleString()}g</strong></span>
      `;
    }
  }
}

function selectHubFilter(realmId) {
  selectedRealmId = realmId;
  loadState();
}

function selectOrderRow(idx) {
  selectedListing = marketState.listings[idx];
  renderSelectedItemDeck();
  loadState();
}

function renderSelectedItemDeck() {
  const panel = document.getElementById('selectedItemPanel');
  if (!selectedListing) {
    panel.innerHTML = `<div style="color:var(--text-dim); padding:10px;">No active listing in this trading post.</div>`;
    return;
  }
  const l = selectedListing;
  const temperStr = l.temper_tier > 0 ? ` +${l.temper_tier}` : '';
  panel.innerHTML = `
    <div>
      <div class="sel-header">
        <div class="item-slot slot-${l.rarity}" style="width:50px; height:50px;">
          ${l.temper_tier > 0 ? `<span class="temper-badge">+${l.temper_tier}</span>` : ''}
          ${getItemSvg(l.icon_key)}
        </div>
        <div>
          <div style="font-family:var(--font-display); font-weight:700; font-size:13px;" class="text-${l.rarity}">
            ${l.item_name}${temperStr}
          </div>
          <div style="font-family:var(--font-mono); font-size:10px; color:var(--text-secondary); margin-top:2px;">
            ${l.realm_name} Trading Post · ${(l.tax_rate_bps/100).toFixed(1)}% Tax
          </div>
          <div class="mint-badge" style="margin-top:4px; display:inline-block;">${l.mint_serial}</div>
        </div>
      </div>
      <div style="font-style:italic; font-size:10.5px; color:var(--text-secondary); margin-top:8px; line-height:1.35;">
        "${l.lore_text || 'Tamriel Exchange asset.'}"
      </div>
    </div>
    <div style="display:flex; justify-content:space-between; align-items:center; padding-top:8px; border-top:1px solid var(--border-dim); font-family:var(--font-mono); font-size:10.5px;">
      <span style="color:var(--text-dim);">BUYOUT PRICE</span>
      <span style="color:var(--brass-bright); font-weight:700; font-size:13.5px;">
        ${l.buyout_price ? l.buyout_price.toLocaleString() + 'g' : l.start_price.toLocaleString() + 'g'}
      </span>
    </div>
  `;
  renderItemChart(l.item_id);
}

// =========================================================================
// TRADING, ARCANE TEMPERING & KIOSK ACTIONS
// =========================================================================
async function executeBuyout(listingId) {
  const res = await fetch('/api/buyout', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ listing_id: listingId, buyer_id: activePlayerId })
  });
  const data = await res.json();
  if (!res.ok) {
    notify(data.detail || 'Purchase declined', true);
  } else {
    notify(`${data.message} [Lock latency: ${data.latency_us} µs]`);
    loadState();
  }
}

async function placeEscrowBid(listingId, bidAmount) {
  const res = await fetch('/api/bid', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ listing_id: listingId, bidder_id: activePlayerId, bid_amount: bidAmount })
  });
  const data = await res.json();
  if (!res.ok) {
    notify(data.detail || 'Bid declined', true);
  } else {
    notify(data.message);
    loadState();
  }
}

function openListDrawer(item) {
  if (item.is_escrowed) {
    notify(`Item [${item.item_name}] is currently listed on a trading post.`, true);
    return;
  }
  selectedBagItem = item;
  const tStr = item.temper_tier > 0 ? ` (+${item.temper_tier})` : '';
  document.getElementById('listItemTitle').textContent = `${item.item_name}${tStr} [${item.mint_serial}]`;
  const suggested = Math.max(500, item.base_vendor_value * (4 + item.temper_tier * 2));
  document.getElementById('listStartPrice').value = Math.round(suggested * 0.8);
  document.getElementById('listBuyoutPrice').value = suggested;
  if (selectedRealmId > 0) {
    document.getElementById('listHubSelect').value = selectedRealmId;
  }
  document.getElementById('listDrawer').classList.add('open');
  loadState();
}

function closeListDrawer() {
  selectedBagItem = null;
  document.getElementById('listDrawer').classList.remove('open');
}

async function submitListItem() {
  if (!selectedBagItem) return;
  const realmId = parseInt(document.getElementById('listHubSelect').value, 10);
  const startP = parseInt(document.getElementById('listStartPrice').value, 10);
  const buyoutP = parseInt(document.getElementById('listBuyoutPrice').value, 10);
  const res = await fetch('/api/list-item', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      instance_id: selectedBagItem.instance_id,
      seller_id: activePlayerId,
      realm_id: realmId,
      start_price: startP,
      buyout_price: buyoutP
    })
  });
  const data = await res.json();
  if (!res.ok) {
    notify(data.detail || 'Failed to list item', true);
  } else {
    notify(data.message);
    closeListDrawer();
    loadState();
  }
}

async function submitTemperItem() {
  if (!selectedBagItem) return;
  const enchantId = parseInt(document.getElementById('forgeGlyphSelect').value, 10);
  const res = await fetch('/api/temper-item', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      instance_id: selectedBagItem.instance_id,
      player_id: activePlayerId,
      enchant_id: enchantId
    })
  });
  const data = await res.json();
  if (!res.ok) {
    notify(data.detail || 'Refinement failed', true);
  } else {
    notify(data.message);
    closeListDrawer();
    loadState();
  }
}

async function submitKioskSealedBid() {
  const realmId = parseInt(document.getElementById('kioskBidHub').value, 10);
  const guildId = parseInt(document.getElementById('kioskBidGuild').value, 10);
  const bidGold = parseInt(document.getElementById('kioskBidAmount').value, 10);
  const res = await fetch('/api/kiosk-bid', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ realm_id: realmId, guild_id: guildId, bid_gold: bidGold })
  });
  const data = await res.json();
  if (!res.ok) {
    notify(data.detail || 'Sealed bid rejected', true);
  } else {
    notify(data.message);
    loadState();
  }
}

async function triggerWeeklyKioskFlip() {
  const res = await fetch('/api/kiosk-flip', { method: 'POST' });
  const data = await res.json();
  notify(data.message);
  loadState();
}

// =========================================================================
// RIGHT WORKBENCH TABS
// =========================================================================
function switchRightTab(key, btn) {
  document.querySelectorAll('.sub-tab').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('rtab-kiosk').style.display = key === 'kiosk' ? 'block' : 'none';
  document.getElementById('rtab-dupe').style.display = key === 'dupe' ? 'block' : 'none';
  document.getElementById('rtab-rmt').style.display = key === 'rmt' ? 'block' : 'none';
  document.getElementById('rtab-sql').style.display = key === 'sql' ? 'block' : 'none';
  if (key === 'rmt') {
    loadRmtLaunderingGraph();
  } else if (key === 'sql') {
    loadQueryInspector('q5_cross_realm_arbitrage');
  }
}

async function loadRmtLaunderingGraph() {
  const res = await fetch('/api/rmt-graph');
  const data = await res.json();
  const box = document.getElementById('rmtGraphContainer');

  const edgesHtml = data.edges.map((e, i) => `
    <div style="background:var(--bg-panel); border:1px solid rgba(239,68,68,0.35); padding:8px 10px; margin-bottom:6px; font-family:var(--font-ui); font-size:11px;">
      <div style="display:flex; justify-content:space-between; color:#fca5a5; font-weight:600;">
        <span>Transfer #${i+1}: ${e.sender_name.replace(/_/g, ' ')} &rarr; ${e.recipient_name.replace(/_/g, ' ')}</span>
        <span style="font-family:var(--font-mono);">${e.gross_price.toLocaleString()} gold</span>
      </div>
      <div style="color:var(--text-secondary); font-size:10px; margin-top:3px; display:flex; justify-content:space-between;">
        <span>${e.item_name} (Vendor: ${e.base_vendor_value}g · ${Math.round(e.gross_price/e.base_vendor_value)}&times; markup)</span>
        <span style="color:var(--text-dim);">${e.realm_name}</span>
      </div>
      ${e.recipient_banned ? '<div style="color:var(--emerald); font-size:9.5px; font-weight:600; margin-top:4px;">Account Frozen &amp; Gold Confiscated</div>' : ''}
    </div>
  `).join('');

  box.innerHTML = `
    <div style="background:rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.3); padding:8px 10px; margin-bottom:8px; font-size:10.5px; display:flex; justify-content:space-between;">
      <span>Total Illicit Gold Traced: <strong style="color:#fca5a5;">${data.total_laundered_gold.toLocaleString()}g</strong></span>
      <span style="color:var(--text-dim); font-family:var(--font-mono);">Query Latency: ${data.latency_us} µs</span>
    </div>
    ${edgesHtml}
  `;
}

async function executeInquisitorBan() {
  const res = await fetch('/api/ban-rmt-ring', { method: 'POST' });
  const data = await res.json();
  notify(data.message);
  loadRmtLaunderingGraph();
  loadState();
}

async function executeStressTest(mode) {
  const box = document.getElementById('stressOutputArea');
  box.innerHTML = `<div style="font-family:var(--font-mono); font-size:11px; color:var(--brass-bright); padding:10px; text-align:center;">Simulating 100 simultaneous transactions across execution barrier...</div>`;

  const res = await fetch('/api/stress-test-dupe', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ concurrent_threads: 100, locking_mode: mode })
  });
  const data = await res.json();
  loadState();

  const isSafe = data.items_duplicated === 0;
  let matrixNodes = '';
  for (let i = 0; i < data.threads_fired; i++) {
    let cls = 'blocked';
    if (i === 0) cls = 'win';
    else if (!isSafe && i < data.succeeded) cls = 'duped';
    matrixNodes += `<div class="thread-node ${cls}" title="Transaction #${i+1}"></div>`;
  }

  box.innerHTML = `
    <div style="background:var(--bg-panel); border:1px solid ${isSafe ? 'var(--emerald)' : 'var(--crimson)'}; padding:10px 12px;">
      <div style="display:flex; justify-content:space-between; font-family:var(--font-mono); font-size:10.5px; font-weight:700; color:${isSafe ? 'var(--emerald)' : '#fca5a5'};">
        <span>${isSafe ? 'Transaction Isolation Verified' : 'Race Condition Collision Detected'}</span>
        <span>${data.total_duration_ms} ms</span>
      </div>
      <div style="font-family:var(--font-mono); font-size:9.5px; color:var(--text-secondary); margin-top:4px;">
        Item: ${data.mint_serial} · Settled: ${data.succeeded} · Blocked by Lock: ${data.rejected_by_lock} · Conflicts: ${data.items_duplicated}
      </div>

      <div class="thread-matrix">${matrixNodes}</div>

      <div style="font-family:var(--font-mono); font-size:9.5px; color:var(--text-dim); max-height:115px; overflow-y:auto; background:var(--bg-void); padding:7px; border:1px solid var(--border-dim);">
        ${data.sample_logs.map(l =>
          `<div style="color:${l.success ? (isSafe ? '#6ee7b7' : '#fca5a5') : '#8c96ab'}; margin-bottom:2px;">
            [Worker #${String(l.thread_id).padStart(3,'0')} | ${l.latency_ms}ms] ${l.code}: ${l.message}
          </div>`
        ).join('')}
      </div>
    </div>
  `;
}

async function loadQueryInspector(qKey) {
  const res = await fetch('/api/analytics/' + qKey);
  const data = await res.json();
  const box = document.getElementById('sqlInspectorOutput');
  const cols = data.rows.length > 0 ? Object.keys(data.rows[0]) : [];

  box.innerHTML = `
    <div style="font-family:var(--font-mono); font-size:10.5px; font-weight:700; color:var(--brass-bright); margin-bottom:4px;">
      ${data.title} (${data.latency_us} µs)
    </div>
    <div style="font-family:var(--font-mono); font-size:9.5px; color:var(--cyan); background:rgba(56,189,248,0.08); padding:5px 8px; border-left:2px solid var(--cyan); margin-bottom:6px; word-break:break-word;">
      <strong>Relational Algebra:</strong> ${data.ra}
    </div>
    ${data.query_plan && data.query_plan.length ? `
    <div style="font-family:var(--font-mono); font-size:9px; color:var(--text-secondary); background:var(--bg-slot); padding:4px 8px; border:1px solid var(--border-dim); margin-bottom:6px;">
      <strong style="color:var(--emerald);">Query Plan:</strong> ${data.query_plan.join(' ➔ ')}
    </div>` : ''}
    <div style="overflow-x:auto; border:1px solid var(--border-dim);">
      <table class="market-table" style="font-size:10px;">
        <thead>
          <tr>${cols.map(c => `<th style="padding:4px 7px;">${c}</th>`).join('')}</tr>
        </thead>
        <tbody>
          ${data.rows.map(r => `
            <tr>${cols.map(c => `<td style="padding:4px 7px; font-family:var(--font-mono);">${r[c]}</td>`).join('')}</tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;
}

async function stepBotTick() {
  const res = await fetch('/api/bot-tick', { method: 'POST' });
  const data = await res.json();
  notify(data.detail);
  loadState();
}

function toggleMarketBots() {
  const btn = document.getElementById('btnSimToggle');
  const txt = document.getElementById('simStatusText');
  if (simTimer) {
    clearInterval(simTimer);
    simTimer = null;
    btn.classList.remove('btn-active-sim');
    txt.textContent = 'Off';
  } else {
    btn.classList.add('btn-active-sim');
    txt.textContent = 'Active';
    stepBotTick();
    simTimer = setInterval(stepBotTick, 2400);
  }
}

async function resetDatabase() {
  await fetch('/api/reset', { method: 'POST' });
  notify('Market data and 5 regional trading posts reset to initial state.');
  loadState();
}

window.addEventListener('resize', () => {
  if (selectedListing) renderItemChart(selectedListing.item_id);
});

loadState();

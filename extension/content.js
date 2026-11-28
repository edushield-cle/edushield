// EduShield - quét chủ động trên trang, hiển thị chatbot cảnh báo.
// Mọi phân tích diễn ra trên máy. Không lưu, không gửi nội dung tin nhắn.
// Chỉ khi học sinh bấm "Phân tích sâu" hoặc "Báo cáo" thì bản ĐÃ CHE thông tin cá nhân mới được gửi tới máy chủ EduShield.
(() => {
  // Mỗi lần nạp là một "thế hệ". Khi tiện ích được cài lại/tải lại, bản mới tiếp quản và bản cũ tự dừng.
  const GEN = Math.random().toString(36).slice(2);
  window.__edushieldGen = GEN;
  const alive = () => { try { return window.__edushieldGen === GEN && !!(chrome.runtime && chrome.runtime.id); } catch (e) { return false; } };
  document.querySelectorAll("#edushield-root, #edushield-nudge").forEach((e) => e.remove()); // gỡ nút cũ đã "chết"
  const D = globalThis.EduShieldDetector;
  const HOST = location.hostname;
  const MAX_LEN = 1000, MIN_LEN = 6;

  const st = {
    enabled: false, sens: "can_bang", large: false, salt: "", blocked: new Set(globalThis.EDUSHIELD_BLOCKLIST || []), suppressed: new Set(),
    seenEl: new WeakMap(), seenText: new Set(), domainCache: new Map(), warnedDomains: new Set(),
    share: { enabled: false, mode: "an_danh" }, contacts: [], sensitive: false, pending: { scanned: 0, warnings: 0, links: 0, notRisk: 0 }, here: { scanned: 0, warnings: 0, media: 0, tt: 0 }, mediaScan: true, sendNudge: true, blurViolent: true, nudgeOpen: false, consented: false, on: false, siteOff: false, autoOpened: false, userClosed: false, lastSys: 0, sysNotify: true, evQueue: [], dayActive: false,
  };

  // ---------- tiện ích ----------
  // Mã định danh của một tin chỉ để không đếm trùng: có muối riêng của thiết bị nên người khác không dò ngược bằng cách thử từng câu
  const keyHash = (s) => sha256((st.salt || "") + "|" + s);
  async function sha256(s) {
    const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
    return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
  }
  const send = (msg) => new Promise((res) => {
    try { chrome.runtime.sendMessage(msg, (r) => res(chrome.runtime.lastError ? { ok: false, error: "Không kết nối được tiện ích" } : r)); }
    catch (e) { res({ ok: false, error: String(e) }); }
  });
  // Ghi LOẠI nguy cơ đã gặp trong ngày (chỉ mã loại + mã băm để gỡ khi bấm "Không phải nguy cơ").
  // Dữ liệu này nằm trên máy; chỉ khi học sinh bật "Đóng góp thống kê" thì một gói đã thêm nhiễu mới được gửi.
  const today = () => new Date().toLocaleDateString("sv-SE");
  function flushDaily() {
    if (!st.evQueue.length && !st.dayActive) return;
    const ops = st.evQueue; st.evQueue = [];
    const active = st.dayActive; st.dayActive = false;
    chrome.storage.local.get({ daily: {}, sentDays: [] }, ({ daily, sentDays }) => {
      const day = today();
      if (sentDays.includes(day)) return; // ngày đã gửi thống kê thì không ghi thêm
      const d = daily[day] || { active: false, ev: {} };
      if (active) d.active = true;
      daily[day] = d;
      for (const op of ops) {
        if (op.add) for (const c of op.cats) { d.ev[c] = d.ev[c] || []; if (!d.ev[c].includes(op.key)) d.ev[c].push(op.key); }
        if (op.remove) for (const dd of Object.values(daily)) for (const c in dd.ev) dd.ev[c] = dd.ev[c].filter((k) => k !== op.remove);
      }
      chrome.storage.local.set({ daily });
    });
  }
  function flushStats() {
    if (!alive()) return shutdown();
    flushDaily();
    const p = st.pending;
    if (!p.scanned && !p.warnings && !p.links && !p.notRisk) return;
    st.pending = { scanned: 0, warnings: 0, links: 0, notRisk: 0 };
    chrome.storage.local.get({ stats: { scanned: 0, warnings: 0, links: 0, notRisk: 0 } }, ({ stats }) => {
      for (const k in p) stats[k] = (stats[k] || 0) + p[k];
      chrome.storage.local.set({ stats });
    });
  }
  setInterval(flushStats, 5000);

  // ---------- giao diện chatbot (Shadow DOM để không ảnh hưởng trang) ----------
  const hostEl = document.createElement("div");
  hostEl.id = "edushield-root";
  hostEl.style.cssText = "position:fixed;right:18px;bottom:18px;z-index:2147483647;";
  const root = hostEl.attachShadow({ mode: "open" });
  root.innerHTML = `
  <style>
    *{box-sizing:border-box;font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
    .fab{width:54px;height:54px;border-radius:50%;border:none;background:#1f6feb;color:#fff;font-size:26px;cursor:grab;box-shadow:0 4px 14px rgba(0,0,0,.25);position:relative;touch-action:none}
    .fab:active{cursor:grabbing}
    .panel.left,.toast.left{right:auto;left:0}.panel.below,.toast.below{bottom:auto;top:66px}
    .head{cursor:move;touch-action:none;user-select:none}.toast{touch-action:none;user-select:none}
    .lv{font-size:11px;font-weight:700;padding:1px 7px;border-radius:99px;margin-left:6px;vertical-align:2px;background:#eee;color:#333}
    .msg.khan_cap .lv{background:#d1242f;color:#fff}.msg.canh_bao .lv{background:#fb8500;color:#fff}.msg.luu_y .lv{background:#f2cc60;color:#3d2e00}
    .why{margin:2px 0}.kws{margin:4px 0;font-size:12.5px;color:#57606a}
    .kw{display:inline-block;background:#fff1f0;color:#b42318;border-radius:6px;padding:0 6px;margin:1px 3px 1px 0;font-weight:600}
    .src{font-size:12px;color:#57606a;margin-bottom:2px}
    .btns.sec{margin-top:6px}.btns.sec button{background:transparent;border-color:#e1e4e8;color:#57606a;font-size:12px}
    .btns button:disabled{opacity:.65;cursor:default}
    .undo{display:flex;justify-content:space-between;align-items:center;gap:8px;font-size:13px;color:#57606a}
    .undo button{border:1px solid #d0d7de;background:#fff;border-radius:8px;padding:4px 8px;cursor:pointer;font-size:12.5px}
    .confirm{margin-top:8px;padding:8px;background:#f6f8fa;border:1px dashed #d0d7de;border-radius:8px;font-size:12.5px}
    .confirm textarea{width:100%;height:70px;margin:6px 0;font:inherit;font-size:12.5px;border:1px solid #d0d7de;border-radius:6px;padding:4px}
    .confirm .row2{display:flex;gap:6px}.confirm button{border:1px solid #d0d7de;background:#fff;border-radius:8px;padding:5px 9px;cursor:pointer;font-size:12.5px}.confirm button.primary{background:#1f6feb;color:#fff;border-color:#1f6feb}
    .help{display:flex;gap:6px;flex-wrap:wrap;margin-top:4px}.help button,.help a{border:1px solid #d0d7de;background:#fff;border-radius:8px;padding:4px 8px;font-size:12.5px;cursor:pointer;color:#1f2328;text-decoration:none}
    .fab.off{background:#8c959f}
    .state{border-left:4px solid #8c959f}
    .badge{position:absolute;top:-4px;right:-4px;background:#d1242f;color:#fff;border-radius:10px;font-size:12px;padding:2px 6px;display:none}
    .toast{display:none;position:absolute;right:0;bottom:66px;width:290px;background:#fff;color:#1f2328;border-radius:14px;box-shadow:0 8px 26px rgba(0,0,0,.32);padding:11px 12px;border-left:5px solid #e85d04;cursor:pointer;animation:esIn .25s ease}
    .toast.khan_cap{border-left-color:#d1242f}.toast.show{display:block}
    .toast .tt{font-weight:700;font-size:14px;margin-bottom:3px}.toast .ts{font-size:13px;color:#57606a;line-height:1.35}
    .toast .tb{display:flex;gap:6px;margin-top:8px}.toast button{border:1px solid #d0d7de;background:#f6f8fa;border-radius:8px;padding:5px 10px;font-size:13px;cursor:pointer}.toast button.primary{background:#1f6feb;border-color:#1f6feb;color:#fff}
    @keyframes esIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
    @media (prefers-color-scheme: dark){.toast{background:#161b22;color:#e6edf3}.toast .ts{color:#9da7b3}.toast button{background:#21262d;border-color:#30363d;color:#e6edf3}}
    .panel{display:none;position:absolute;right:0;bottom:66px;width:350px;max-height:70vh;background:#fff;color:#1f2328;border-radius:14px;box-shadow:0 8px 30px rgba(0,0,0,.3);overflow:hidden;flex-direction:column}
    .panel.open{display:flex}
    .head{background:linear-gradient(135deg,#1f6feb,#5b4bdb 60%,#0aa2c0);color:#fff;padding:11px 12px;display:flex;justify-content:space-between;align-items:center;font-weight:700;position:relative;overflow:hidden}.head:before{content:"";position:absolute;width:90px;height:90px;border-radius:50%;background:rgba(255,255,255,.14);right:-20px;top:-40px}.head>*{position:relative}
    .head button{background:none;border:none;color:#fff;font-size:18px;cursor:pointer}
    .body{overflow-y:auto;padding:10px;display:flex;flex-direction:column;gap:10px;background:radial-gradient(circle at 90% 0,rgba(31,111,235,.10),transparent 45%),radial-gradient(circle at 0 100%,rgba(91,75,219,.08),transparent 45%),#f6f8fa}
    .msg{background:#fff;border-radius:12px;padding:10px;border-left:5px solid #999;font-size:13.5px;line-height:1.45}
    .msg.khan_cap{border-color:#d1242f}.msg.canh_bao{border-color:#e85d04}.msg.luu_y{border-color:#d4a72c}.msg.info{border-color:#1f6feb}
    .ttl{font-weight:800;margin-bottom:4px;font-size:14.5px}.msg.khan_cap .ttl{color:#d1242f}.msg.canh_bao .ttl{color:#c2410c}.msg.luu_y .ttl{color:#9a6700}.msg.info .ttl{color:#1f6feb}
    .msg{box-shadow:0 1px 4px rgba(16,24,40,.08)}.msg.khan_cap{background:linear-gradient(180deg,#fff5f5,#fff)}
    .msg b{font-weight:600;background:linear-gradient(transparent 58%,#ffe58a 58%);color:inherit}.msg .ttl b,.msg b.rd{background:none}b.rd{color:#d1242f;font-weight:700}
    .quote{background:#f0f0f0;border-radius:6px;padding:4px 6px;margin:6px 0;font-style:italic;color:#555;word-break:break-word}
    ul{margin:4px 0 6px 18px;padding:0}
    .btns{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
    .btns button{border:1px solid #d0d7de;background:#fff;border-radius:8px;padding:5px 8px;font-size:12.5px;cursor:pointer}
    .btns button.primary{background:#1f6feb;color:#fff;border-color:#1f6feb}.btns button:hover{filter:brightness(.96)}
    .deep{margin-top:8px;padding:8px;background:#eef4ff;border-radius:8px;font-size:13px}
    .foot{font-size:11.5px;color:#57606a;padding:8px 12px;border-top:1px solid #eee;background:#fff}
    .stat{font-size:11.5px;color:#1a7f37;font-weight:600;padding:6px 12px;background:#fff;border-top:1px solid #eee}
    .todo{margin-top:8px;padding:8px;background:#fff8e6;border-radius:8px;font-size:13px}
    .todo ol{margin:4px 0 6px 18px;padding:0}
    .fr{font-size:14px;margin-bottom:4px}
    .sos{margin-top:8px;padding:8px;background:#fff1f0;border-radius:8px;font-size:13px}.sos .c{display:flex;align-items:center;gap:6px;margin:4px 0}.sos .c b{flex:1;background:none}
    .sos button,.sos a{border:1px solid #f0b8bd;background:#fff;border-radius:8px;padding:4px 8px;font-size:12.5px;cursor:pointer;color:#1f2328;text-decoration:none}
    .sup{margin-top:8px;padding:8px;border-radius:8px;background:#eef4ff;font-size:12.5px}.sup .row2{display:flex;gap:6px;margin-top:6px}.sup button{border:1px solid #c8d7f5;background:#fff;border-radius:8px;padding:4px 9px;cursor:pointer;font-size:12.5px}.sup button.primary{background:#1f6feb;color:#fff;border-color:#1f6feb}
    .head .hb{display:flex;gap:4px;align-items:center}.head .sosb{background:#d1242f;border-radius:8px;font-size:13px;padding:3px 8px;font-weight:700}
    .panel.large{font-size:16px}.panel.large .msg{font-size:16px}.panel.large .btns button{font-size:14px;padding:8px 10px}
    @media (prefers-color-scheme: dark){
      .panel{background:#161b22;color:#e6edf3}.body{background:#0d1117}.msg{background:#161b22}.quote{background:#21262d;color:#c9d1d9}
      .btns button{background:#21262d;color:#e6edf3;border-color:#30363d}.btns button.primary{background:#1f6feb;border-color:#1f6feb}
      .msg.khan_cap{background:linear-gradient(180deg,#2a1215,#161b22)}.msg b{background:linear-gradient(transparent 58%,#5c4a00 58%)}.msg .ttl b,.msg b.rd{background:none}b.rd{color:#ff7b72}
      .foot,.stat{background:#161b22;border-color:#30363d;color:#9da7b3}.kw{background:#3b1d1d;color:#ffa198}.confirm,.undo button,.confirm button,.help button,.help a{background:#21262d;border-color:#30363d;color:#e6edf3}.lv{background:#30363d;color:#e6edf3}.stat{color:#3fb950}.deep{background:#12233f}.todo{background:#2a2310}.sos{background:#2a1215}.sup{background:#12233f}.sos button,.sos a,.sup button{background:#21262d;border-color:#30363d;color:#e6edf3}
    }
  </style>
  <div class="toast" id="toast" role="alert"><div class="tt" id="toastTitle"></div><div class="ts" id="toastSub"></div><div class="tb"><button class="primary" id="toastOpen">👀 Xem ngay</button><button id="toastX">Để sau</button></div></div>
  <div class="panel" id="panel">
    <div class="head" id="head" title="Kéo để di chuyển"><span>🛡️ EduShield</span><span class="hb"><button class="sosb" id="sosHead" title="Báo người thân, gọi 111">🆘</button><button id="close" title="Thu gọn">✕</button></span></div>
    <div class="body" id="body">
      <div class="msg info"><div class="ttl">👋 Mình đang để mắt giúp bạn</div>Tin nhắn không rời khỏi máy này.</div>
    </div>
    <div class="stat" id="statline">🟢 Đang bảo vệ</div>
    <div class="foot">AI có thể sai, bạn là người quyết định · Cần giúp: <b>111</b></div>
  </div>
  <button class="fab" id="fab" title="EduShield">🛡️<span class="badge" id="badge"></span></button>`;
  const $ = (id) => root.getElementById(id);
  const panel = $("panel"), body = $("body"), badge = $("badge");
  let unread = 0;
  const toast = $("toast");
  let toastTimer = 0;
  const hideToast = () => { toast.classList.remove("show"); clearTimeout(toastTimer); };
  const openPanel = () => { hideToast(); panel.classList.add("open"); unread = 0; badge.style.display = "none"; };
  const closePanel = () => { panel.classList.remove("open"); st.userClosed = true; }; // đã tự đóng thì các lần sau không tự mở nữa
  let dragged = false; // vừa kéo xong thì không coi là bấm
  $("fab").onclick = () => { if (dragged) { dragged = false; return; } panel.classList.contains("open") ? closePanel() : openPanel(); };
  $("close").onclick = closePanel;
  $("toastOpen").onclick = (e) => { e.stopPropagation(); openPanel(); };
  $("toastX").onclick = (e) => { e.stopPropagation(); hideToast(); };
  toast.onclick = () => { if (dragged) { dragged = false; return; } openPanel(); };
  function showToast(level, title) {
    toast.className = "toast show " + level;
    $("toastTitle").textContent = title;
    $("toastSub").textContent = level === "khan_cap" ? "Cần bạn xem ngay." : "Bấm để xem lý do và việc nên làm.";
    clearTimeout(toastTimer);
    if (level !== "khan_cap") toastTimer = setTimeout(hideToast, 12000);
  }
  // Mục "Cảnh báo gần đây" trong cửa sổ tiện ích: chỉ ngày + mức độ + loại, KHÔNG có nội dung, link hay tên trang
  function rememberAlert(lv, lb) {
    chrome.storage.local.get({ recentAlerts: [], unseenAlerts: 0 }, (s) => {
      const d = new Date().toLocaleDateString("sv-SE");
      chrome.storage.local.set({ recentAlerts: [{ d, lv, lb: String(lb).slice(0, 60) }].concat(s.recentAlerts).slice(0, 30), unseenAlerts: s.unseenAlerts + 1 });
    });
  }
  function sysNotify(level, title) { // thông báo của hệ điều hành, KHÔNG kèm nội dung tin nhắn
    if (!st.sysNotify || level === "luu_y" || Date.now() - st.lastSys < 30000) return;
    st.lastSys = Date.now();
    try { chrome.runtime.sendMessage({ type: "notify", level, title }); } catch (e) {}
  }

  // ---------- KÉO THẢ: học sinh tự đặt EduShield ở chỗ không che nội dung ----------
  let pos = null; // khoảng cách tới mép phải / mép dưới (px)
  function clampPos(r, b) { return { r: Math.round(Math.min(Math.max(r, 4), innerWidth - 62)), b: Math.round(Math.min(Math.max(b, 4), innerHeight - 62)) }; }
  function placePopups() { // khung chat, pop-up mở về phía còn chỗ trống
    const rc = hostEl.getBoundingClientRect();
    const left = rc.left < 370, below = rc.top < 400;
    for (const x of [panel, toast]) { x.classList.toggle("left", left); x.classList.toggle("below", below); }
  }
  function applyPos() { if (pos) { hostEl.style.right = pos.r + "px"; hostEl.style.bottom = pos.b + "px"; } placePopups(); }
  function makeDraggable(handle) {
    let sx = 0, sy = 0, sr = 0, sb = 0, id = null, moved = false;
    handle.addEventListener("pointerdown", (e) => {
      if (e.button !== 0 || (handle.id !== "fab" && e.target.closest("button"))) return;
      id = e.pointerId; sx = e.clientX; sy = e.clientY; moved = false;
      const cs = getComputedStyle(hostEl); sr = parseFloat(cs.right) || 18; sb = parseFloat(cs.bottom) || 18;
      try { handle.setPointerCapture(id); } catch (err) {}
    });
    handle.addEventListener("pointermove", (e) => {
      if (e.pointerId !== id) return;
      const dx = e.clientX - sx, dy = e.clientY - sy;
      if (!moved && Math.hypot(dx, dy) < 6) return;
      moved = true; pos = clampPos(sr - dx, sb - dy); applyPos();
    });
    const end = (e) => {
      if (e.pointerId !== id) return;
      id = null;
      if (moved) { dragged = true; setTimeout(() => (dragged = false), 300); try { chrome.storage.local.set({ widgetPos: pos }); } catch (err) {} }
    };
    handle.addEventListener("pointerup", end); handle.addEventListener("pointercancel", end);
  }
  makeDraggable($("fab")); makeDraggable($("head")); makeDraggable(toast);
  addEventListener("resize", () => { if (pos) pos = clampPos(pos.r, pos.b); applyPos(); });

  function esc(s) { const d = document.createElement("div"); d.textContent = s; return d.innerHTML; }
  const LEVEL_TITLE = { khan_cap: "🚨 Khẩn cấp", canh_bao: "⚠️ Cảnh báo", luu_y: "💡 Cần lưu ý" };

  function addCard(html, level, buttons = []) {
    const card = document.createElement("div");
    card.className = "msg " + level;
    card.innerHTML = html;
    if (buttons.length) {
      const rows = {};
      for (const [label, fn, primary, sec] of buttons) {
        const k = sec ? "sec" : "main";
        if (!rows[k]) { rows[k] = document.createElement("div"); rows[k].className = "btns" + (sec ? " sec" : ""); }
        const bt = document.createElement("button");
        bt.textContent = label; if (primary) bt.className = "primary";
        bt.onclick = () => fn(card, bt);
        rows[k].appendChild(bt);
      }
      if (rows.main) card.appendChild(rows.main);
      if (rows.sec) card.appendChild(rows.sec);
    }
    body.appendChild(card);
    body.scrollTop = body.scrollHeight;
    placePopups();
    if (!panel.classList.contains("open")) {
      // Chỉ tự mở khung chat ĐÚNG MỘT LẦN (và nếu người dùng chưa từng đóng). Từ lần sau chỉ hiện pop-up để chủ động mở.
      const t0 = card.querySelector(".ttl");
      let title = LEVEL_TITLE[level] || "EduShield";
      if (t0) { const c = t0.cloneNode(true); c.querySelectorAll(".lv").forEach((x) => x.remove()); title = c.textContent.trim().slice(0, 60) || title; }
      if (!st.autoOpened && !st.userClosed) { st.autoOpened = true; openPanel(); }
      else { unread++; badge.textContent = unread; badge.style.display = "block"; showToast(level, title); sysNotify(level, title); }
    }
    return card;
  }

  function mark(el, color) {
    if (!el || !el.style) return;
    el.dataset.edushieldOutline = el.style.outline || "";
    el.style.outline = `2px dashed ${color}`;
    el.style.outlineOffset = "2px";
  }
  function unmark(el) { if (el && el.dataset && "edushieldOutline" in el.dataset) { el.style.outline = el.dataset.edushieldOutline; delete el.dataset.edushieldOutline; } }

  // ---------- cảnh báo tin nhắn ----------
  const LV_TAG = { khan_cap: "Khẩn cấp", canh_bao: "Cảnh báo", luu_y: "Cần lưu ý" };
  const LV_ICON = { khan_cap: "🚨", canh_bao: "⚠️", luu_y: "💡" };
  function flash(el) { // làm nổi tin nhắn/ảnh trong 2 giây để học sinh nhận ra
    const o = el.style.boxShadow, t = el.style.transition;
    el.style.transition = "box-shadow .3s"; el.style.boxShadow = "0 0 0 4px rgba(209,36,47,.55)";
    setTimeout(() => { el.style.boxShadow = o; el.style.transition = t; }, 2000);
  }
  function todoBox(card, bt, steps) { // bấm lần nữa để ẩn
    const old = card.querySelector(".todo");
    if (old) { old.remove(); bt.textContent = "📋 Cần làm gì ngay?"; return; }
    const t = document.createElement("div"); t.className = "todo";
    t.innerHTML = `<b>Việc nên làm ngay</b><ol>${steps.map((x) => `<li>${esc(x)}</li>`).join("")}</ol>`;
    const h = document.createElement("div"); h.className = "help";
    const cp = document.createElement("button"); cp.textContent = "📨 Sao chép lời nhờ người lớn giúp";
    cp.title = "Không kèm nội dung tin nhắn";
    cp.onclick = () => navigator.clipboard.writeText(D.HELP_MSG).then(() => (cp.textContent = "✅ Đã sao chép, dán gửi cho người bạn tin")).catch(() => (cp.textContent = D.HELP_MSG));
    const call = document.createElement("a"); call.href = "tel:111"; call.textContent = "📞 Gọi 111";
    h.append(cp, call); t.appendChild(h);
    const firstBtns = card.querySelector(".btns");
    card.insertBefore(t, firstBtns ? firstBtns.nextSibling : null);
    bt.textContent = "📋 Ẩn hướng dẫn";
    t.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }

  // ---------- v1.6: BÁO NGƯỜI THÂN (số điện thoại không hiện trên trang web, tiện ích tự mở cuộc gọi / tin nhắn / Zalo) ----------
  function sosBox(card, bt, catVi) {
    const old = card.querySelector(".sos");
    if (old) { old.remove(); if (bt) bt.textContent = "🆘 Báo người thân"; return; }
    const box = document.createElement("div"); box.className = "sos";
    if (st.contacts.length) {
      box.innerHTML = "<b>Báo cho người bạn tin</b>";
      st.contacts.forEach((name, i) => {
        const row = document.createElement("div"); row.className = "c";
        const nm = document.createElement("b"); nm.textContent = name; row.appendChild(nm);
        for (const [lb, act] of [["📞 Gọi", "call"], ["💬 Nhắn", "sms"], ["Zalo", "zalo"]]) {
          const b = document.createElement("button"); b.textContent = lb;
          b.onclick = () => send({ type: "contactAction", i, action: act, catVi });
          row.appendChild(b);
        }
        box.appendChild(row);
      });
    } else {
      box.innerHTML = "<b>Chưa có số người thân.</b> Bấm biểu tượng EduShield trên thanh trình duyệt → 🆘 để thêm số cha mẹ, thầy cô.";
    }
    const h = document.createElement("div"); h.className = "help";
    const cp = document.createElement("button"); cp.textContent = "📨 Sao chép lời nhờ giúp";
    cp.onclick = () => navigator.clipboard.writeText(D.HELP_MSG).then(() => (cp.textContent = "✅ Đã sao chép")).catch(() => (cp.textContent = D.HELP_MSG));
    const call = document.createElement("a"); call.href = "tel:111"; call.textContent = "📞 111 (miễn phí)";
    h.append(cp, call); box.appendChild(h);
    card.appendChild(box);
    if (bt) bt.textContent = "🆘 Ẩn";
    box.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }
  $("sosHead").onclick = (e) => {
    e.stopPropagation();
    const c = addCard('<div class="ttl">🆘 Cần giúp ngay</div><div class="fr">Bạn không một mình. Báo cho người bạn tin, hoặc gọi 111.</div>', "khan_cap");
    sosBox(c, null, "");
    openPanel();
  };
  // ---------- v1.6: CẢNH BÁO KHẨN CẤP -> gửi về trường theo lựa chọn của học sinh ----------
  function onEmergency(card, cat, catVi) {
    send({ type: "emergency" }); // ẩn danh: tiện ích tự gửi gói thống kê đã trộn nhiễu sau vài phút
    if (!st.share.enabled || st.share.mode !== "danh_tinh") return;
    const box = document.createElement("div"); box.className = "sup";
    let left = 10, timer = 0;
    box.innerHTML = `📨 Sẽ báo thầy cô phụ trách sau <b class="n">${left}</b> giây (tên, lớp, loại nguy cơ; không gửi tin nhắn).`;
    const row = document.createElement("div"); row.className = "row2";
    const now = document.createElement("button"); now.className = "primary"; now.textContent = "Gửi ngay";
    const no = document.createElement("button"); no.textContent = "Không gửi";
    row.append(now, no); box.appendChild(row); card.appendChild(box);
    const go = async () => {
      clearInterval(timer); row.remove();
      box.textContent = "⏳ Đang báo thầy cô…";
      const r = await send({ type: "supportRequest", cat, level: "khan_cap" });
      if (r && r.ok && r.skipped) box.textContent = "ℹ️ Hôm nay đã báo thầy cô về loại nguy cơ này.";
      else if (r && r.ok) box.textContent = "✅ Đã báo thầy cô. Thầy cô sẽ liên hệ riêng với bạn.";
      else {
        box.textContent = "Chưa báo được thầy cô (máy chủ của trường chưa kết nối). ";
        const again = document.createElement("button"); again.textContent = "Thử lại"; again.onclick = go; box.appendChild(again);
      }
    };
    timer = setInterval(() => { left--; const n = box.querySelector(".n"); if (n) n.textContent = left; if (left <= 0) go(); }, 1000);
    now.onclick = go;
    no.onclick = () => { clearInterval(timer); box.textContent = "Đã huỷ, không gửi gì về trường."; };
  }

  async function showAlert(el, text, r, manual = false, media = null) {
    const key = await keyHash(D.norm(text));
    if (!manual && st.suppressed.has(key)) return;
    if (!manual) { st.pending.warnings++; st.evQueue.push({ add: true, cats: r.cats, key }); }
    if (!manual) rememberAlert(r.level, r.cat_vi || r.label_vi);
    const color = r.level === "khan_cap" ? "#d1242f" : "#e85d04";
    if (el) mark(el, color);
    const preview = text.length > 90 ? text.slice(0, 90) + "…" : text;
    const src = media ? `<div class="src">${media.kind === "video" ? "🎬" : "🖼️"} ${esc(media.from)} · bạn đã xem ${media.seconds} giây</div>` : "";
    const html = `<div class="ttl">${LV_ICON[r.level] || "🔔"} ${esc(r.cat_vi || r.label_vi)}<span class="lv">${LV_TAG[r.level] || ""}</span></div>${src}
      <div class="why">🔎 ${esc(r.main)}</div>
      ${r.phrases && r.phrases.length ? `<div class="kws">Cụm từ đáng chú ý: ${r.phrases.map((x) => `<span class="kw">${esc(x)}</span>`).join("")}</div>` : ""}
      <div class="quote">“${esc(preview)}”</div><div class="fr">${esc(r.friendly)}</div>`;
    const steps = media ? [...(D.TODO_MEDIA[r.label] || []), ...(r.todo || []).slice(0, 2)] : (r.todo || []);
    const buttons = [];
    buttons.push(["📋 Cần làm gì ngay?", (card, bt) => todoBox(card, bt, steps), true]);
    if (el) buttons.push([media ? (media.kind === "video" ? "👀 Xem video" : "👀 Xem ảnh") : "👀 Xem tin nhắn", (card, bt) => {
      if (!el.isConnected) { bt.textContent = "Nội dung không còn trên trang"; bt.disabled = true; return; }
      el.scrollIntoView({ behavior: "smooth", block: "center" }); flash(el);
    }]);
    buttons.push(["🆘 Báo người thân", (card, bt) => sosBox(card, bt, r.cat_vi || r.label_vi), false, r.level !== "khan_cap"]);
    buttons.push(["🤖 Phân tích sâu", (card, bt) => deep(card, bt, text), false, true]);
    buttons.push(["📣 Báo cáo ẩn danh", (card, bt) => report(card, bt, text, r.label), false, true]);
    buttons.push(["🙅 Không phải nguy cơ", (card, bt) => notRisk(card, key, el, r, color), false, true]);
    const card = addCard(html, r.level, buttons);
    if (!manual && r.level === "khan_cap") onEmergency(card, r.cat || (r.label === "bat_nat" ? "bn_khac" : "ld_khac"), r.cat_vi || r.label_vi);
  }

  // "Không phải nguy cơ": bỏ cảnh báo, ghi nhận góp ý, cho HOÀN TÁC trong 8 giây
  function setSuppressed(key, on) {
    chrome.storage.local.get({ suppressed: [] }, ({ suppressed }) => {
      const set = new Set(suppressed); on ? set.add(key) : set.delete(key);
      chrome.storage.local.set({ suppressed: [...set].slice(-500) });
    });
  }
  function notRisk(card, key, el, r, color) {
    st.suppressed.add(key); st.pending.notRisk++; st.evQueue.push({ remove: key }); setSuppressed(key, true);
    if (el) unmark(el);
    const kids = [...card.childNodes]; kids.forEach((n) => n.remove());
    const u = document.createElement("div"); u.className = "undo";
    u.innerHTML = "<span>✅ Đã bỏ cảnh báo này. Cảm ơn bạn góp ý!</span>";
    const ub = document.createElement("button"); ub.textContent = "↩️ Hoàn tác";
    u.appendChild(ub); card.appendChild(u);
    const timer = setTimeout(() => card.remove(), 8000);
    ub.onclick = () => {
      clearTimeout(timer);
      st.suppressed.delete(key); st.pending.notRisk = Math.max(0, st.pending.notRisk - 1);
      st.evQueue.push({ add: true, cats: r.cats, key }); setSuppressed(key, false);
      if (el) mark(el, color);
      u.remove(); kids.forEach((n) => card.appendChild(n));
    };
  }

  // Bước xác nhận dùng chung: học sinh THẤY (và sửa được) bản đã che trước khi bất cứ thứ gì rời trình duyệt
  function confirmSend(card, bt, title, okLabel, onOk) {
    const old = card.querySelector(".confirm"); if (old) old.remove();
    const m0 = D.mask(bt.dataset.text || "");
    const w = document.createElement("div"); w.className = "confirm";
    w.innerHTML = `<b>${esc(title)}</b><br><small>Đã tự che số điện thoại, số tài khoản, link, email, tên. Bạn có thể sửa thêm.</small><textarea></textarea>`;
    const ta = w.querySelector("textarea"); ta.value = m0.masked;
    const row = document.createElement("div"); row.className = "row2";
    const ok = document.createElement("button"); ok.className = "primary"; ok.textContent = okLabel;
    const no = document.createElement("button"); no.textContent = "Huỷ";
    row.append(ok, no); w.appendChild(row); card.appendChild(w);
    ta.focus();
    no.onclick = () => { w.remove(); bt.disabled = false; };
    ok.onclick = () => { const m = D.mask(ta.value); w.remove(); onOk(m.masked, [...new Set(m0.domains.concat(m.domains))]); };
    bt.disabled = true;
  }

  function deep(card, bt, text) {
    bt.dataset.text = text;
    confirmSend(card, bt, "Gửi bản đã che để AI phân tích sâu?", "🤖 Gửi phân tích", async (masked, domains) => {
      bt.textContent = "⏳ Đang phân tích…";
      const res = await send({ type: "analyze", masked, domains });
      const old = card.querySelector(".deep"); if (old) old.remove();
      const box = document.createElement("div"); box.className = "deep";
      if (res && res.ok) {
        const f = res.data.final;
        box.innerHTML = `<b>🤖 AI đánh giá: ${esc(f.level_vi)}</b><br>${f.reasons.slice(0, 3).map(esc).join("<br>")}${f.need_human_review ? "<br><i>AI chưa chắc chắn: nên nhờ thầy cô hoặc cha mẹ xem giúp.</i>" : ""}`;
        bt.textContent = "✅ Đã phân tích"; bt.disabled = true;
      } else {
        box.innerHTML = "Chưa kết nối được máy chủ phân tích. Kết quả ở trên (phân tích ngay trên máy) vẫn dùng được.";
        bt.textContent = "🤖 Thử phân tích lại"; bt.disabled = false;
      }
      card.appendChild(box);
    });
  }

  function report(card, bt, text, label) {
    bt.dataset.text = text;
    confirmSend(card, bt, "Gửi báo cáo ẩn danh để cảnh báo cho các bạn khác?", "📣 Gửi báo cáo", async (masked, domains) => {
      bt.textContent = "⏳ Đang gửi…";
      const res = await send({ type: "report", masked, domains, label });
      if (res && res.ok) { bt.textContent = "✅ Đã báo cáo, cảm ơn bạn"; bt.disabled = true; }
      else { bt.textContent = "📣 Chưa gửi được, thử lại"; bt.disabled = false; }
    });
  }

  // ---------- quét văn bản ----------
  function skip(el) {
    return !el || el.closest("#edushield-root, #edushield-nudge, [data-edushield-ignore], script, style, noscript, textarea, input, [contenteditable=''], [contenteditable='true'], [role='textbox']");
  }
  function unitOf(textNode) {
    let el = textNode.parentElement;
    while (el && el.parentElement && el.parentElement !== document.body) {
      const disp = getComputedStyle(el).display;
      if (!disp.startsWith("inline")) break;
      el = el.parentElement;
    }
    return el;
  }
  // ---------- CHỈ QUÉT PHẦN ĐANG HIỂN THỊ TRÊN MÀN HÌNH ----------
  // Không đọc, không phân tích nội dung nằm ngoài khung nhìn (phần chưa cuộn tới hoặc đã cuộn qua).
  // Ở bước đăng ký chỉ ghi nhớ "phần tử nào tồn tại"; chữ chỉ được đọc khi phần tử thật sự đang hiện trong khung nhìn.
  const queue = new Set();
  const registered = new WeakSet();
  function inView(el) {
    if (!el || !el.isConnected || document.hidden) return false;
    try { if (el.checkVisibility && !el.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true })) return false; } catch (e) {}
    const r = el.getBoundingClientRect();
    const vw = window.innerWidth || document.documentElement.clientWidth, vh = window.innerHeight || document.documentElement.clientHeight;
    const w = Math.min(r.right, vw) - Math.max(r.left, 0), h = Math.min(r.bottom, vh) - Math.max(r.top, 0);
    if (w <= 0 || h <= 0 || r.width <= 0 || r.height <= 0) return false;
    // phần tử phải hiện ít nhất một nửa; phần tử rất cao thì phần hiện phải chiếm một nửa khung nhìn
    return (w * h) / (r.width * r.height) >= 0.5 || h >= 0.5 * vh;
  }
  const io = new IntersectionObserver((entries) => {
    if (!alive()) return shutdown();
    if (!st.enabled) return;
    for (const en of entries) {
      if (!en.isIntersecting) continue;
      const el = en.target;
      if (el.tagName === "A") { if (inView(el)) checkAnchor(el); continue; }
      queue.add(el);
    }
    if (queue.size) schedule();
  }, { threshold: [0, 0.25, 0.5, 1] });
  function register(el) { if (!el || registered.has(el)) return; registered.add(el); io.observe(el); }
  function retrigger(el) { if (registered.has(el)) { io.unobserve(el); io.observe(el); } else register(el); }
  // Chỉ GHI NHỚ phần tử (chưa đọc chữ). Duyệt theo lô để trang lớn như Facebook/Zalo không bị bỏ sót tin
  // (bản cũ dừng ở 2.000 nút chữ đầu tiên nên tin nhắn nằm sâu trong trang không bao giờ được quét).
  function collect(root, changed = false) {
    if (!root || !alive()) return;
    const reg = changed ? retrigger : register;
    if (root.nodeType === Node.TEXT_NODE) { const u = unitOf(root); if (u && !skip(u)) reg(u); return; }
    if (root.nodeType !== Node.ELEMENT_NODE || skip(root)) return;
    const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, { acceptNode: (n) => (n.nodeValue && n.nodeValue.trim() ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT) });
    const step = () => {
      let n, k = 0;
      while ((n = w.nextNode())) {
        const u = unitOf(n);
        if (u && !skip(u)) reg(u);
        if (++k >= 2500) { setTimeout(step, 20); return; }
      }
    };
    step();
    root.querySelectorAll && root.querySelectorAll("a[href]").forEach(reg);
    if (root.matches && root.matches("a[href]")) reg(root);
    root.querySelectorAll && root.querySelectorAll("img,video").forEach(registerMedia);
    if (root.matches && root.matches("img,video")) registerMedia(root);
  }
  let timer = null;
  function schedule() { if (!timer) timer = setTimeout(processQueue, 400); }
  document.addEventListener("visibilitychange", () => { if (!document.hidden) schedule(); });
  function processQueue() {
    timer = null;
    if (!alive()) return shutdown();
    if (!st.enabled) { queue.clear(); return; }
    if (document.hidden) return; // tab đang ẩn: chưa quét gì, khi hiện lại sẽ kiểm tra tiếp
    let n = 0;
    for (const el of queue) {
      queue.delete(el);
      if (++n > 150) { schedule(); break; }
      if (!inView(el)) { retrigger(el); continue; } // đã cuộn khỏi màn hình trong lúc chờ: bỏ qua, khi hiện lại sẽ quét
      const text = (el.innerText || "").trim();
      if (text.length < MIN_LEN || text.length > MAX_LEN || st.seenEl.get(el) === text || st.seenText.has(text)) continue;
      st.seenEl.set(el, text); st.seenText.add(text);
      if (st.seenText.size > 5000) st.seenText.clear();
      st.pending.scanned++; st.here.scanned++; st.dayActive = true;
      const r = D.analyze(text, { sens: st.sens });
      if (r.warn) { st.here.warnings++; showAlert(el, text, r); }
      else if (r.frame === "tuyen_truyen") st.here.tt++; // nhắc tới nguy cơ để tuyên truyền: không cảnh báo
    }
    paintState();
  }

  // ---------- ẢNH / VIDEO: chỉ kiểm tra khi học sinh đã XEM ít nhất 5 giây ----------
  // Đọc phần CHỮ đi kèm (mô tả ảnh, chú thích, phụ đề video, mã QR nếu trình duyệt hỗ trợ). Không gửi ảnh đi đâu.
  const VIEW_MS = 5000, MEDIA_MIN = 100;
  const mediaReg = new WeakSet(), mediaDone = new WeakSet(), mediaTimers = new Map();
  const mio = new IntersectionObserver((entries) => {
    if (!alive()) return shutdown();
    for (const en of entries) {
      if (en.isIntersecting && st.enabled && st.blurViolent) violentCheck(en.target);
      if (en.isIntersecting && en.intersectionRatio >= 0.5 && st.enabled && st.mediaScan && !document.hidden) startView(en.target);
      else stopView(en.target);
    }
  }, { threshold: [0, 0.5, 1] });
  function registerMedia(el) {
    if (!el || mediaReg.has(el) || skip(el)) return;
    mediaReg.add(el); mio.observe(el);
    if (el.tagName === "VIDEO") { // nạp phụ đề ở chế độ ẩn (không hiện lên màn hình) để đọc được chữ
      try { for (const tr of el.textTracks) if (tr.mode === "disabled") tr.mode = "hidden"; } catch (e) {}
    }
  }
  function startView(el) {
    if (mediaDone.has(el) || mediaTimers.has(el)) return;
    mediaTimers.set(el, setTimeout(() => { mediaTimers.delete(el); if (!document.hidden && inView(el)) checkMedia(el); }, VIEW_MS));
  }
  function stopView(el) { clearTimeout(mediaTimers.get(el)); mediaTimers.delete(el); }
  document.addEventListener("visibilitychange", () => { if (document.hidden) for (const el of [...mediaTimers.keys()]) stopView(el); });
  const GENERIC = /^(có thể là|may be|image may contain|không có mô tả|no photo description|photo|ảnh|image|video|hình ảnh)[^a-zA-ZÀ-ỹ]*$/i;
  async function mediaText(el) {
    const parts = [], from = new Set();
    const add = (t, f) => { t = (t || "").replace(/\s+/g, " ").trim(); if (t.length >= 6 && !GENERIC.test(t) && !parts.includes(t)) { parts.push(t.slice(0, 600)); from.add(f); } };
    add(el.getAttribute("alt"), "mô tả ảnh"); add(el.getAttribute("aria-label"), "mô tả"); add(el.getAttribute("title"), "tiêu đề");
    const lb = el.getAttribute("aria-labelledby");
    if (lb) lb.split(/\s+/).forEach((id) => { const x = document.getElementById(id); if (x) add(x.innerText, "mô tả"); });
    const fig = el.closest("figure"); const fc = fig && fig.querySelector("figcaption"); if (fc) add(fc.innerText, "chú thích");
    if (el.tagName === "VIDEO") {
      try { for (const tr of el.textTracks) { if (tr.mode === "disabled") tr.mode = "hidden"; for (const c of tr.cues || []) add(c.text, "phụ đề video"); } } catch (e) {}
    }
    // Mã QR / chữ trong ảnh: chỉ khi trình duyệt có sẵn bộ nhận dạng (chạy trên máy). Ảnh khác nguồn thường bị trình duyệt chặn đọc.
    if ("BarcodeDetector" in self) { try { for (const c of await new BarcodeDetector({ formats: ["qr_code"] }).detect(el)) add(c.rawValue, "mã QR trong ảnh"); } catch (e) {} }
    if ("TextDetector" in self) { try { for (const t of await new TextDetector().detect(el)) add(t.rawValue, "chữ trong ảnh"); } catch (e) {} }
    return { text: parts.join(" · "), from: [...from].join(", ") };
  }
  async function checkMedia(el) {
    if (mediaDone.has(el) || !st.enabled || !st.mediaScan) return;
    mediaDone.add(el); mio.unobserve(el);
    const rc = el.getBoundingClientRect();
    if (rc.width < MEDIA_MIN || rc.height < MEDIA_MIN) return;
    const a = el.closest("a[href]"); if (a) checkAnchor(a); // ảnh dẫn tới link nguy hiểm
    const { text, from } = await mediaText(el);
    if (!text) return;
    if (st.blurViolent && violentCheck(el, text)) return; // đã làm mờ: không cần cảnh báo thêm
    st.pending.scanned++; st.here.scanned++; st.here.media++; st.dayActive = true;
    const r = D.analyze(text, { sens: st.sens });
    if (!r.warn && r.frame === "tuyen_truyen") st.here.tt++;
    if (r.warn) { st.here.warnings++; showAlert(el, text, r, false, { kind: el.tagName === "VIDEO" ? "video" : "ảnh", from: "Đọc từ " + from, seconds: VIEW_MS / 1000 }); }
    paintState();
  }

  // ---------- v1.9: NHẮC TRƯỚC KHI GỬI và LÀM MỜ NỘI DUNG BẠO LỰC ----------
  // Chỉ nhắc, không chặn: học sinh luôn có thể "Vẫn gửi" / "Vẫn xem". Không lưu, không gửi nội dung; không báo ai.
  // Nhà trường chỉ thấy (nếu học sinh bật gửi thống kê) một ô có/không đã trộn nhiễu: "hôm nay có được nhắc trước khi gửi không".
  const nHost = document.createElement("div");
  nHost.id = "edushield-nudge";
  nHost.style.cssText = "position:fixed;left:50%;bottom:24px;transform:translateX(-50%);z-index:2147483647;display:none;width:min(440px,calc(100vw - 24px));";
  const nRoot = nHost.attachShadow({ mode: "open" });
  nRoot.innerHTML = `<style>
    *{box-sizing:border-box;font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
    .card{background:#fff;color:#1f2328;border-radius:16px;box-shadow:0 10px 34px rgba(0,0,0,.35);padding:14px 16px;border-top:5px solid #8250df;animation:in .2s ease}
    .card.ld{border-top-color:#e85d04}.card.md{border-top-color:#d1242f}
    @keyframes in{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
    .t{font-weight:800;font-size:15.5px;margin-bottom:4px}.b{font-size:13.5px;line-height:1.45;color:#3d444d}
    .q{margin:8px 0;padding:6px 9px;background:#f6f8fa;border-radius:8px;font-size:13px;font-style:italic;color:#57606a;word-break:break-word}
    .rw{display:flex;flex-direction:column;gap:5px;margin:6px 0}.rw:empty{display:none}
    .rw button{text-align:left;border:1px dashed #c8b6f0;background:#faf7ff;border-radius:9px;padding:6px 9px;font-size:13px;cursor:pointer;color:#1f2328}
    .rh{font-size:12.5px;color:#57606a;margin-top:6px}
    .row{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
    .row button{border:1px solid #d0d7de;background:#fff;border-radius:9px;padding:7px 11px;font-size:13px;cursor:pointer;color:#1f2328}
    .row button.p{background:#1f6feb;border-color:#1f6feb;color:#fff;font-weight:600}
    .f{font-size:11.5px;color:#57606a;margin-top:8px}
    @media (prefers-color-scheme: dark){.card{background:#161b22;color:#e6edf3}.b{color:#c9d1d9}.q{background:#21262d;color:#9da7b3}.rw button{background:#1d1630;border-color:#4b3a78;color:#e6edf3}.row button{background:#21262d;border-color:#30363d;color:#e6edf3}.f,.rh{color:#9da7b3}}
  </style><div class="card" id="card" role="alertdialog" aria-labelledby="t"><div class="t" id="t"></div><div class="b" id="b"></div><div class="q" id="q"></div><div class="rh" id="rh"></div><div class="rw" id="rw"></div><div class="row" id="row"></div><div class="f" id="f"></div></div>`;
  const n$ = (id) => nRoot.getElementById(id);
  let nudgeEsc = null;
  let pendingMedia = null; // ảnh bị làm mờ lúc học sinh đang xem lời nhắc gửi tin: hiện thẻ sau, không che lời nhắc
  function closeNudge() { nHost.style.display = "none"; st.nudgeOpen = false; st.nudgeText = ""; if (nudgeEsc) { removeEventListener("keydown", nudgeEsc, true); nudgeEsc = null; }
    if (pendingMedia) { const f = pendingMedia; pendingMedia = null; setTimeout(f, 300); } }
  function nudgeCount(field) {
    chrome.storage.local.get({ nudgeStats: { shown: 0, fixed: 0, sent: 0, blurred: 0, shownMedia: 0 } }, ({ nudgeStats }) => {
      nudgeStats[field] = (nudgeStats[field] || 0) + 1; chrome.storage.local.set({ nudgeStats });
    });
  }
  function nudgeEvent(cat) { st.dayActive = true; keyHash(cat + "|" + today()).then((key) => st.evQueue.push({ add: true, cats: [cat], key })); }
  function openNudge(cls, title, bodyHtml, quote, footer) {
    if (!nHost.isConnected) document.documentElement.appendChild(nHost);
    n$("card").className = "card " + cls; n$("t").textContent = title; n$("b").innerHTML = bodyHtml;
    n$("q").textContent = quote || ""; n$("q").style.display = quote ? "" : "none";
    n$("rw").textContent = ""; n$("rh").textContent = ""; n$("row").textContent = ""; n$("f").textContent = footer;
    nHost.style.display = "block"; st.nudgeOpen = true;
  }
  const nbtn = (label, cls, fn) => { const b = document.createElement("button"); b.textContent = label; if (cls) b.className = cls; b.onclick = fn; n$("row").appendChild(b); return b; };

  // ----- tin MÌNH SẮP GỬI -----
  const COMPOSE = "textarea, input:not([type]), input[type=text], input[type=search], [contenteditable=''], [contenteditable='true'], [role='textbox']";
  let lastCompose = null;
  const bypass = new Map(); // tin học sinh đã chọn "Vẫn gửi" (giữ 60 giây, chỉ trong bộ nhớ của trang)
  function composeOf(t) {
    if (!t || !t.closest) return null;
    const el = t.closest(COMPOSE);
    if (!el || el.closest("#edushield-root, #edushield-nudge")) return null;
    if (el.type === "password" || /password|otp|one-time/i.test(el.autocomplete || "")) return null;
    return el;
  }
  const isField = (el) => el.tagName === "INPUT" || el.tagName === "TEXTAREA";
  const textOf = (el) => String((isField(el) ? el.value : el.innerText) || "");
  function setText(el, v) {
    el.focus();
    if (isField(el)) {
      const proto = el.tagName === "INPUT" ? HTMLInputElement.prototype : HTMLTextAreaElement.prototype;
      Object.getOwnPropertyDescriptor(proto, "value").set.call(el, v); // để các trang dùng React cũng nhận giá trị mới
      el.dispatchEvent(new Event("input", { bubbles: true }));
    } else {
      try { document.execCommand("selectAll", false); document.execCommand("insertText", false, v); } catch (e) { el.textContent = v; }
    }
  }
  function gate(el, how) {
    if (!alive() || !st.enabled || !st.sendNudge) return false;
    const text = textOf(el).trim();
    if (!text) return false;
    const now = Date.now();
    for (const [k, t] of bypass) if (now - t > 60000) bypass.delete(k);
    if (bypass.has(text)) { bypass.delete(text); return false; }
    if (st.nudgeOpen && st.nudgeText === text) { closeNudge(); nudgeCount("sent"); return false; } // bấm gửi lần nữa = vẫn gửi
    const res = D.outgoing(text, { sens: st.sens });
    if (!res.nudge) return false;
    showSendNudge(el, text, res, how);
    return true;
  }
  function showSendNudge(el, text, res, how) {
    const cls = res.kind === "bat_nat" ? "bn" : "ld";
    const why = res.why ? ` <b>(${esc(res.why)})</b>` : "";
    openNudge(cls, "✋ " + res.title, esc(res.body) + why, text.length > 140 ? text.slice(0, 140) + "…" : text,
      "EduShield chỉ nhắc, bạn là người quyết định. Tin này không được lưu hay gửi cho ai.");
    st.nudgeText = text;
    nudgeCount("shown"); nudgeEvent("hv_nhac_gui");
    if (res.rewrite && res.rewrite.length) {
      n$("rh").textContent = res.kind === "lua_dao" ? "Nếu bạn đang cảnh báo mọi người, có thể gửi thế này:" : "Hoặc nói theo cách khác:";
      for (const v of res.rewrite) {
        const b = document.createElement("button"); b.textContent = "💬 " + v;
        b.onclick = () => { closeNudge(); nudgeCount("fixed"); setText(el, v); };
        n$("rw").appendChild(b);
      }
    }
    nbtn("✏️ Sửa lại", "p", () => { closeNudge(); nudgeCount("fixed"); el.focus(); });
    nbtn("🗑️ Không gửi nữa", "", () => { closeNudge(); nudgeCount("fixed"); setText(el, ""); });
    nbtn("Vẫn gửi", "", () => {
      closeNudge(); nudgeCount("sent"); bypass.set(text, Date.now());
      if (how.button) { how.button.click(); return; }
      el.focus();
      for (const type of ["keydown", "keypress", "keyup"]) el.dispatchEvent(new KeyboardEvent(type, { key: "Enter", code: "Enter", keyCode: 13, which: 13, bubbles: true, cancelable: true }));
    });
    nudgeEsc = (e) => { if (e.key === "Escape") { closeNudge(); el.focus(); } };
    addEventListener("keydown", nudgeEsc, true);
  }
  document.addEventListener("focusin", (e) => { const c = composeOf(e.target); if (c) lastCompose = c; }, true);
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Enter" || e.shiftKey || e.isComposing || !e.isTrusted) return;
    const el = composeOf(e.target);
    if (el && gate(el, { enter: true })) { e.preventDefault(); e.stopImmediatePropagation(); }
  }, true);
  const SEND_LABEL = /^(gửi|gửi tin|gửi tin nhắn|send|đăng|post|trả lời|reply|bình luận|comment|nhấn enter để gửi)\b/i;
  document.addEventListener("click", (e) => {
    if (!e.isTrusted || !e.target.closest) return;
    const b = e.target.closest("button, [role='button'], input[type='submit']");
    if (!b || b.closest("#edushield-root, #edushield-nudge")) return;
    const label = String(b.getAttribute("aria-label") || b.getAttribute("title") || b.value || b.innerText || "").trim();
    if (!SEND_LABEL.test(label)) return;
    const el = lastCompose && lastCompose.isConnected ? lastCompose : null;
    if (el && gate(el, { button: b })) { e.preventDefault(); e.stopImmediatePropagation(); }
  }, true);

  // ----- ẢNH / VIDEO CÓ DẤU HIỆU BẠO LỰC: làm mờ ngay khi hiện ra, học sinh tự chọn có xem tiếp hay không -----
  const violentDone = new WeakSet();
  function quickMediaText(el) {
    const parts = [el.getAttribute("alt"), el.getAttribute("aria-label"), el.getAttribute("title")];
    const fig = el.closest("figure"); const fc = fig && fig.querySelector("figcaption"); if (fc) parts.push(fc.innerText);
    if (el.tagName === "VIDEO") { try { for (const tr of el.textTracks) for (const c of tr.cues || []) parts.push(c.text); } catch (e) {} }
    const post = el.closest("article, [role='article']"); if (post) parts.push(String(post.innerText || "").slice(0, 400));
    return parts.filter(Boolean).join(" · ");
  }
  function violentCheck(el, text) {
    if (violentDone.has(el) || !st.blurViolent || !st.enabled) return false;
    const rc = el.getBoundingClientRect(); if (rc.width < MEDIA_MIN || rc.height < MEDIA_MIN) return false;
    const v = D.violentMedia(text || quickMediaText(el));
    if (!v.hit) return false;
    violentDone.add(el);
    el.dataset.edushieldBlur = "1"; el.dataset.edushieldFilter = el.style.filter || "";
    el.style.filter = "blur(26px) grayscale(.4)";
    if (el.tagName === "VIDEO") { try { el.pause(); } catch (e) {} el.addEventListener("play", () => { if (el.dataset.edushieldBlur === "1") el.pause(); }); }
    mark(el, "#8250df");
    nudgeCount("blurred"); nudgeEvent("hv_bao_luc");
    const card = () => mediaCard(el, v);
    if (st.nudgeOpen && st.nudgeText) pendingMedia = card; else card();
    return true;
  }
  function mediaCard(el, v) {
    if (el.dataset.edushieldBlur !== "1") return;
    const kind = el.tagName === "VIDEO" ? "video" : "ảnh";
    openNudge("md", `🙈 Đã làm mờ một ${kind} có dấu hiệu bạo lực`,
      `Xem hoặc chia sẻ ${kind} bạo lực có thể làm người bị hại tổn thương thêm, và làm mình quen dần với bạo lực. Nếu đây là chuyện xảy ra với bạn hoặc bạn bè, hãy báo thầy cô, cha mẹ hoặc gọi <b>111</b>.`,
      "", "Chữ đi kèm có cụm “" + v.word + "”. EduShield chỉ đọc chữ, không gửi ảnh đi đâu.");
    nbtn("🙈 Giữ mờ", "p", () => { closeNudge(); });
    nbtn("👁️ Vẫn xem", "", () => { closeNudge(); el.dataset.edushieldBlur = "0"; el.style.filter = el.dataset.edushieldFilter || ""; unmark(el); });
    nbtn("🆘 Cần giúp", "", () => { closeNudge(); const c = addCard('<div class="ttl">🆘 Cần giúp ngay</div><div class="fr">Bạn không một mình. Báo cho người bạn tin, hoặc gọi 111.</div>', "khan_cap"); sosBox(c, null, ""); openPanel(); });
  }

  // ---------- kiểm tra link (so mã băm tên miền, chạy trên máy) ----------
  function realUrl(a) {
    try {
      const u = new URL(a.href, location.href);
      if (/^l[m]?\.facebook\.com$/.test(u.hostname) && u.searchParams.get("u")) return new URL(u.searchParams.get("u"));
      return u;
    } catch (e) { return null; }
  }
  async function isBlocked(hostname) {
    const h = hostname.toLowerCase().replace(/^www\./, "");
    if (st.domainCache.has(h)) return st.domainCache.get(h);
    const AL = globalThis.EDUSHIELD_ALLOWLIST || { domains: [], suffixes: [] };
    if (AL.domains.some((x) => h === x || h.endsWith("." + x)) || AL.suffixes.some((x) => h.endsWith(x))) { st.domainCache.set(h, false); return false; }
    const parts = h.split(".");
    let bad = false;
    for (let i = 0; i + 1 < parts.length; i++) {
      if (st.blocked.has(await sha256(parts.slice(i).join(".")))) { bad = true; break; }
    }
    st.domainCache.set(h, bad);
    return bad;
  }
  async function checkAnchor(a) {
    if (!st.enabled || a.dataset.edushieldLink || !inView(a)) return;
    const u = realUrl(a);
    if (!u || !/^https?:$/.test(u.protocol) || u.hostname === HOST) return;
    a.dataset.edushieldLink = "1";
    if (await isBlocked(u.hostname)) {
      a.dataset.edushieldLink = "bad";
      mark(a, "#d1242f");
      a.title = "EduShield: link này đã bị nhiều bạn báo cáo lừa đảo";
      if (!st.warnedDomains.has(u.hostname)) {  // cảnh báo ngay khi link xuất hiện, chưa cần bấm
        st.warnedDomains.add(u.hostname);
        st.pending.warnings++;
        keyHash("link|" + u.hostname).then((key) => st.evQueue.push({ add: true, cats: ["lua_dao_bat_ky", "link_nguy_hiem"], key }));
        const msgEl = a.closest("[dir='auto']") || a.parentElement;
        rememberAlert("khan_cap", "Link nguy hiểm");
        const lc = addCard(`<div class="ttl">🚨 Link nguy hiểm<span class="lv">Khẩn cấp</span></div><div class="why">🔎 <b>${esc(u.hostname)}</b> đã bị nhiều bạn báo cáo lừa đảo.</div>
          <div class="fr"><b class="rd">Đừng bấm</b>, đừng đăng nhập hay nhập mã OTP ở trang đó.</div>`, "khan_cap",
          [["📋 Cần làm gì ngay?", (card, bt) => todoBox(card, bt, D.TODO_CAT.link_nguy_hiem), true],
           ["👀 Xem tin nhắn", (card, bt) => { if (!msgEl || !msgEl.isConnected) { bt.textContent = "Tin không còn trên trang"; bt.disabled = true; return; } msgEl.scrollIntoView({ behavior: "smooth", block: "center" }); flash(msgEl); }],
           ["🆘 Báo người thân", (card, bt) => sosBox(card, bt, "Link lừa đảo")]]);
        onEmergency(lc, "link_nguy_hiem", "Link lừa đảo");
      }
    }
  }
  document.addEventListener("click", (e) => {
    if (!st.enabled) return;
    const a = e.target.closest && e.target.closest("a[href]");
    if (!a || a.dataset.edushieldLink !== "bad" || a.dataset.edushieldAllow) return;
    e.preventDefault(); e.stopPropagation();
    st.pending.links++;
    const u = realUrl(a);
    addCard(`<div class="ttl">🛑 Đã chặn một link<span class="lv">Khẩn cấp</span></div><div class="why">🔎 <b>${esc(u ? u.hostname : "")}</b> đã bị nhiều bạn báo cáo lừa đảo.</div>
      <div class="fr">Trang kiểu này hay đòi đăng nhập, mã OTP hoặc chuyển tiền.</div>`, "khan_cap", [
      ["🚫 Không mở", (card) => card.remove(), true],
      ["📋 Cần làm gì ngay?", (card, bt) => todoBox(card, bt, D.TODO_CAT.link_nguy_hiem)],
      ["Tôi hiểu rủi ro, vẫn mở", (card) => { a.dataset.edushieldAllow = "1"; card.remove(); a.click(); }, false, true],
    ]);
  }, true);

  // ---------- kiểm tra thủ công (chuột phải) ----------
  chrome.runtime.onMessage.addListener((msg) => {
    if (msg.type === "manualCheck" && msg.text) {
      const r = D.analyze(msg.text, { sens: st.sens });
      if (r.warn) showAlert(null, msg.text, r, true);
      else if (r.frame === "tuyen_truyen") addCard(`<div class="ttl">ℹ️ Nội dung tuyên truyền, cảnh báo</div><div class="quote">“${esc(msg.text.slice(0, 90))}”</div>
        <div class="fr">Tin này nhắc tới thủ đoạn để mọi người cảnh giác, không nhắm vào bạn. Nếu ai đó gửi riêng cho bạn kèm yêu cầu chuyển tiền, đọc mã hay giữ bí mật, hãy hỏi người lớn.</div>`, "info",
        [["🤖 Phân tích sâu", (card, bt) => deep(card, bt, msg.text), true]]);
      else addCard(`<div class="ttl">✅ Chưa thấy dấu hiệu rõ ràng</div><div class="quote">“${esc(msg.text.slice(0, 90))}”</div>
        <div class="fr">Vẫn thấy lo? Hỏi người lớn bạn tin.</div>`, "info",
        [["🤖 Phân tích sâu", (card, bt) => deep(card, bt, msg.text), true]]);
      openPanel();
    } else if (msg.type === "settingsChanged") loadSettings();
  });
  // Cửa sổ tiện ích hỏi "trên trang này có đang quét không?" (chỉ trả về con số, không có nội dung)
  chrome.runtime.onMessage.addListener((msg, sender, reply) => {
    if (msg.type !== "ping" || !alive()) return;
    reply({ ok: true, sensitive: st.sensitive, consented: st.consented, enabled: st.on, siteOff: st.siteOff, scanning: st.enabled, scanned: st.here.scanned, warnings: st.here.warnings, media: st.here.media });
  });

  // ---------- khởi động ----------
  const observer = new MutationObserver((muts) => {
    if (!alive()) return shutdown();
    if (!st.enabled) return;
    for (const m of muts) {
      if (m.type === "characterData") collect(m.target, true);
      else m.addedNodes.forEach((x) => collect(x, true)); // phần tử được dùng lại với chữ mới cũng được quét lại
    }
    schedule();
  });
  let watchTimer = 0, observedBody = null, stopped = false;
  function shutdown() { try { nHost.remove(); } catch (e) {} // bản cũ dừng hẳn khi tiện ích đã được tải lại
    if (stopped) return; stopped = true;
    try { observer.disconnect(); io.disconnect(); mio.disconnect(); } catch (e) {}
    clearInterval(watchTimer);
  }
  function watchBody() {
    if (document.body && observedBody !== document.body) { // trang thay cả thẻ body (ứng dụng một trang)
      observedBody = document.body;
      observer.observe(document.body, { childList: true, subtree: true, characterData: true });
      if (st.enabled) { collect(document.body); schedule(); }
    }
    if (!hostEl.isConnected) document.documentElement.appendChild(hostEl); // trang xoá mất nút: gắn lại
  }
  // Thẻ trạng thái trong khung chat: cho biết vì sao chưa quét và nút để sửa ngay
  let stateCard = null;
  function paintState() {
    const fab = $("fab"), line = $("statline");
    fab.classList.toggle("off", !st.enabled);
    if (!st.consented) { fab.title = "EduShield chưa được bật"; line.textContent = "⏸️ Chưa bật: bấm “Bắt đầu dùng” để EduShield quét giúp bạn"; }
    else if (!st.on) { fab.title = "EduShield đang tắt"; line.textContent = "⏸️ Bảo vệ đang tắt"; }
    else { fab.title = "EduShield đang bảo vệ"; line.textContent = `🟢 Đang bảo vệ · ${st.here.scanned} đoạn · ${st.here.warnings} cảnh báo` + (st.here.tt ? ` · ${st.here.tt} tuyên truyền` : ""); line.title = st.here.tt ? "Tin tuyên truyền, cảnh báo nhắc tới nguy cơ nhưng không nhắm vào bạn nên EduShield không cảnh báo" : ""; }
    line.style.color = st.enabled ? "" : "#9a6700";
    if (stateCard) { stateCard.remove(); stateCard = null; }
    if (!st.enabled) {
      stateCard = document.createElement("div");
      stateCard.className = "msg state";
      const btn = document.createElement("button");
      btn.className = "primary";
      if (!st.consented) {
        stateCard.innerHTML = `<div class="ttl">⏸️ EduShield chưa được bật</div>Bạn chưa hoàn tất bước đồng ý, nên mình <b class="rd">chưa quét gì</b> trên trang này.`;
        btn.textContent = "▶️ Bắt đầu dùng"; btn.onclick = () => send({ type: "openOnboarding" });
      } else {
        stateCard.innerHTML = `<div class="ttl">⏸️ Bảo vệ đang tắt</div>Bạn đã tắt EduShield trong cửa sổ tiện ích.`;
        btn.textContent = "🛡️ Bật lại"; btn.onclick = () => chrome.storage.local.set({ enabled: true });
      }
      const bx = document.createElement("div"); bx.className = "btns"; bx.appendChild(btn);
      stateCard.appendChild(bx);
      body.insertBefore(stateCard, body.firstChild);
    }
  }
  function loadSettings() {
    chrome.storage.local.get({ enabled: true, consented: false, sens: "can_bang", large: false, devSalt: "", sysNotify: true, mediaScan: true, widgetPos: null, disabledSites: [], suppressed: [], blocklist: [], share: { enabled: false, mode: "an_danh" }, contacts: [], sendNudge: true, blurViolent: true }, (s) => {
      st.sendNudge = s.sendNudge !== false; st.blurViolent = s.blurViolent !== false;
      st.share = s.share || st.share; st.contacts = (s.contacts || []).map((c) => String(c.name || "Người thân")); // chỉ lấy TÊN GỌI, không lấy số
      if (!s.devSalt) { s.devSalt = [...crypto.getRandomValues(new Uint8Array(12))].map((x) => x.toString(16).padStart(2, "0")).join(""); chrome.storage.local.set({ devSalt: s.devSalt }); }
      st.sysNotify = s.sysNotify !== false; st.mediaScan = s.mediaScan !== false;
      if (s.widgetPos && typeof s.widgetPos.r === "number") { pos = clampPos(s.widgetPos.r, s.widgetPos.b); applyPos(); } st.salt = s.devSalt; st.sens = s.sens; st.large = s.large; panel.classList.toggle("large", !!s.large);
      st.consented = !!s.consented; st.on = !!s.enabled; st.siteOff = s.disabledSites.includes(HOST);
      st.sensitive = !!(globalThis.EDUSHIELD_SENSITIVE && globalThis.EDUSHIELD_SENSITIVE.test(HOST)); // ngân hàng, email...: không quét
      st.enabled = st.consented && st.on && !st.siteOff && !st.sensitive; // chưa đồng ý thì KHÔNG quét gì cả
      st.suppressed = new Set(s.suppressed);
      s.blocklist.forEach((h) => st.blocked.add(h));
      // Nút luôn hiện để học sinh biết EduShield có mặt; chỉ ẩn khi chính học sinh tắt trên trang này
      hostEl.style.display = st.siteOff || st.sensitive ? "none" : "block";
      paintState();
      if (st.enabled) { collect(document.body); schedule(); }
    });
  }
  document.documentElement.appendChild(hostEl);
  watchBody();
  watchTimer = setInterval(() => (alive() ? watchBody() : shutdown()), 3000);
  document.addEventListener("mouseover", (e) => { const a = e.target.closest && e.target.closest("a[href]"); if (a) checkAnchor(a); }, true);
  loadSettings();
  chrome.storage.onChanged.addListener((ch) => { if (!alive()) return; if (ch.consented || ch.enabled || ch.disabledSites || ch.sens || ch.large || ch.sysNotify || ch.mediaScan || ch.share || ch.contacts || ch.sendNudge || ch.blurViolent) loadSettings(); });
})();

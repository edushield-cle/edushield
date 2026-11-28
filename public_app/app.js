// EduShield (điện thoại) - PWA. Toàn bộ phân tích chạy trong máy. KHÔNG lưu nội dung tin nhắn.
(function () {
  const D = EduShieldDetector, M = EDUSHIELD_MODEL;
  const $ = (id) => document.getElementById(id);
  const KEY = "edushield_m1";
  const today = () => new Date().toLocaleDateString("sv-SE");
  const CFG = globalThis.EDUSHIELD_CONFIG || {};
  const COLLECT = CFG.collect !== false;
  const SCHOOL = CFG.school || "", SERVER = (CFG.server || "http://127.0.0.1:8765").replace(/\/$/, "");
  const DEF = { consented: false, sens: "can_bang", large: false, share: { enabled: false, parental: false, mode: "an_danh", name: "", lop: "" }, daily: {}, sentDays: [], alerts: [], notify: false, unseen: 0, contacts: [], supportSent: [], emgPending: false };
  let S;
  function load() { try { S = Object.assign({}, DEF, JSON.parse(localStorage.getItem(KEY) || "{}")); } catch (e) { S = JSON.parse(JSON.stringify(DEF)); } S.share = Object.assign({}, DEF.share, S.share); }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} }
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  // ---- băm tên miền: crypto.subtle nếu có, nếu không dùng bản JS thuần ----
  async function sha(s) {
    if (globalThis.crypto && crypto.subtle) {
      const b = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
      return [...new Uint8Array(b)].map((x) => x.toString(16).padStart(2, "0")).join("");
    }
    return EduShieldSha256(s);
  }
  const BL = new Set((globalThis.EDUSHIELD_BLOCKLIST && (EDUSHIELD_BLOCKLIST.hashes || EDUSHIELD_BLOCKLIST)) || []);
  const AL = globalThis.EDUSHIELD_ALLOWLIST || { domains: [], suffixes: [] };
  function allowed(d) {
    return AL.domains.some((x) => d === x || d.endsWith("." + x)) || AL.suffixes.some((x) => d.endsWith(x));
  }
  async function badDomains(text) {
    const out = [];
    for (const d of D.mask(text).domains) {
      if (allowed(d)) continue;
      const parts = d.split(".");
      for (let i = 0; i < parts.length - 1; i++) { if (BL.has(await sha(parts.slice(i).join(".")))) { out.push(d); break; } }
    }
    return out;
  }

  // ---- ghi nhận theo ngày: chỉ MÃ LOẠI nguy cơ, không nội dung, không giờ ----
  function record(cats) {
    const d = today(); S.daily[d] = S.daily[d] || { active: true, ev: {} };
    S.daily[d].active = true;
    for (const c of cats) S.daily[d].ev[c] = 1;
    save();
  }
  function markActive() { const d = today(); S.daily[d] = S.daily[d] || { active: true, ev: {} }; save(); }

  async function check(text) {
    const r = D.analyze(text, { sens: S.sens });
    const bad = await badDomains(text);
    const cats = r.cats.slice();
    if (bad.length) { cats.push("link_nguy_hiem"); }
    if (r.warn || bad.length) record(cats); else markActive();
    render(r, bad);
    if (r.warn || bad.length) alertUser(bad.length ? "khan_cap" : r.level, bad.length ? "Link nguy hiểm" : (r.cat_vi || r.label_vi));
    if (bad.length || (r.warn && r.level === "khan_cap")) emergency(bad.length ? "link_nguy_hiem" : (r.cat || "ld_khac"));
  }

  // ---- v1.9: TIN MÌNH SẮP GỬI: chỉ nhắc, không chặn, không báo ai ----
  function checkOutgoing() {
    const box = $("outRes"), t = $("outTxt").value.trim();
    box.innerHTML = "";
    if (!t) return;
    const o = D.outgoing(t, { sens: S.sens });
    const card = document.createElement("div"); card.className = "res " + (o.nudge ? "warn" : "ok");
    const copy = (v) => { try { navigator.clipboard.writeText(v); } catch (e) {} };
    if (!o.nudge) {
      card.innerHTML = "<b>✅ Không thấy điều đáng lo.</b><p class='small'>Bạn có thể sao chép rồi gửi.</p>";
      const b = document.createElement("button"); b.className = "sec"; b.textContent = "📋 Sao chép tin"; b.onclick = () => { copy(t); b.textContent = "✅ Đã sao chép"; };
      card.appendChild(b); box.appendChild(card); return;
    }
    S.nudges = (S.nudges || 0) + 1; save(); record(["hv_nhac_gui"]);
    card.innerHTML = `<b>✋ ${esc(o.title)}</b><p>${esc(o.body)}${o.why ? " <b>(" + esc(o.why) + ")</b>" : ""}</p>`;
    if (o.rewrite && o.rewrite.length) {
      const h = document.createElement("p"); h.className = "small"; h.textContent = o.kind === "lua_dao" ? "Nếu bạn đang cảnh báo mọi người, có thể gửi thế này:" : "Hoặc nói theo cách khác (bấm để dùng):";
      card.appendChild(h);
      for (const v of o.rewrite) { const b = document.createElement("button"); b.className = "chip"; b.textContent = "💬 " + v; b.onclick = () => { $("outTxt").value = v; S.nudgeFixed = (S.nudgeFixed || 0) + 1; save(); checkOutgoing(); }; card.appendChild(b); }
    }
    const p = document.createElement("p"); p.className = "small"; p.textContent = "EduShield chỉ nhắc, bạn là người quyết định."; card.appendChild(p);
    box.appendChild(card);
  }

  // ---- v1.6: cảnh báo khẩn cấp -> gửi về trường theo lựa chọn của học sinh ----
  function emergency(cat) {
    if (!COLLECT || !shareReady()) return;
    // Ẩn danh: gửi gói đã trộn nhiễu của hôm nay sau 20-90 giây (nếu đóng app trước thì gửi ở lần mở sau)
    S.emgPending = true; save();
    setTimeout(() => send(today()).then((r) => { if (r.ok || (r.error && /đã gửi một gói/.test(r.error))) { S.emgPending = false; save(); } }), 20000 + Math.random() * 70000);
    if (S.share.mode !== "danh_tinh") return;
    const box = document.createElement("div"); box.className = "sup";
    let left = 10;
    box.innerHTML = `📨 Sẽ báo thầy cô phụ trách sau <b class="n">${left}</b> giây (tên, lớp, loại nguy cơ; không gửi tin nhắn). <br><button id="supNow">Gửi ngay</button><button class="sec" id="supNo">Không gửi</button>`;
    const card = $("result").querySelector(".card"); if (card) card.appendChild(box);
    const go = async () => {
      clearInterval(t); box.textContent = "⏳ Đang báo thầy cô…";
      const r = await support(cat);
      box.textContent = r.ok ? (r.skipped ? "ℹ️ Hôm nay đã báo thầy cô về loại nguy cơ này." : "✅ Đã báo thầy cô. Thầy cô sẽ liên hệ riêng với bạn.") : "Chưa báo được thầy cô: " + r.error;
    };
    const t = setInterval(() => { left--; const n = box.querySelector(".n"); if (n) n.textContent = left; if (left <= 0) go(); }, 1000);
    box.querySelector("#supNow").onclick = go;
    box.querySelector("#supNo").onclick = () => { clearInterval(t); box.textContent = "Đã huỷ, không gửi gì về trường."; };
  }
  async function support(cat) {
    const key = today() + "|" + cat;
    if (S.supportSent.includes(key)) return { ok: true, skipped: true };
    try {
      const r = await fetch(SERVER + "/hotro", { method: "POST", headers: { "Content-Type": "application/json" }, credentials: "omit",
        body: JSON.stringify({ v: 1, school: SCHOOL, name: S.share.name, lop: S.share.lop, cat, level: "khan_cap" }) });
      if (!r.ok) return { ok: false, error: "máy chủ trả về " + r.status };
      S.supportSent = S.supportSent.concat(key).slice(-60); save(); return { ok: true };
    } catch (e) { return { ok: false, error: "không kết nối được máy chủ của trường." }; }
  }
  // ---- v1.6: báo người thân (số chỉ lưu trên điện thoại này) ----
  const HELP_SMS = (cv) => "[EduShield] Con/em đang gặp chuyện trên mạng" + (cv ? " (" + cv + ")" : "") + ", cần người giúp ngay. Gọi lại cho con/em nhé.";
  const isIOS0 = /iPhone|iPad|iPod/.test(navigator.userAgent);
  function ctRow(c, catVi, extra) {
    const ph = c.phone.replace(/[^\d+]/g, ""), loc = ph.replace(/^\+?84/, "0");
    return `<div class="ct"><b>${esc(c.name)}</b><a href="tel:${esc(ph)}">📞 Gọi</a><a href="sms:${esc(ph)}${isIOS0 ? "&" : "?"}body=${encodeURIComponent(HELP_SMS(catVi))}">💬 Nhắn</a>` +
      `<a href="https://zalo.me/${esc(loc)}" target="_blank" rel="noopener">Zalo</a>${extra || ""}</div>`;
  }
  function contactLinks(catVi) {
    if (!S.contacts.length) return `<p class="small">Chưa có số người thân. Vào tab <b>🆘 Cần giúp</b> để thêm.</p>`;
    return S.contacts.map((c) => ctRow(c, catVi)).join("");
  }
  function renderContacts() {
    $("ctList").innerHTML = S.contacts.length ? S.contacts.map((c, i) => ctRow(c, "", `<button class="danger" data-del="${i}">✕</button>`)).join("")
      : `<p class="small">Chưa có ai. Thêm cha mẹ, người thân hoặc thầy cô để báo nhanh khi gặp chuyện.</p>`;
    $("ctList").querySelectorAll("[data-del]").forEach((b) => (b.onclick = () => { S.contacts.splice(+b.dataset.del, 1); save(); renderContacts(); }));
    $("ctAddBtn").classList.toggle("hide", S.contacts.length >= 3);
  }

  // ---- mục Cảnh báo + pop-up + thông báo hệ thống (không kèm nội dung tin nhắn) ----
  const LV_IC = { khan_cap: "🚨", canh_bao: "⚠️", luu_y: "💡" }, LV_VI = { khan_cap: "Khẩn cấp", canh_bao: "Cảnh báo", luu_y: "Cần lưu ý" };
  const notifySupported = () => "Notification" in window;
  function alertUser(lv, label) {
    S.alerts = [{ d: today(), lv, lb: String(label).slice(0, 60) }].concat(S.alerts || []).slice(0, 30);
    S.unseen = (S.unseen || 0) + 1; save(); renderAlerts();
    showPop(lv, label);
    if (lv !== "luu_y") sysNotify(lv, label);
  }
  function showPop(lv, label) {
    const old = document.querySelector(".pop"); if (old) old.remove();
    const p = document.createElement("div");
    p.className = "pop " + lv; p.setAttribute("role", "alert");
    p.innerHTML = `<b>${LV_IC[lv] || "🔔"} ${esc(label)}</b><span class="small">Xem lý do và việc nên làm bên dưới · kéo để di chuyển</span>`;
    // Kéo để di chuyển; chạm nhẹ (không kéo) thì đóng
    let sx = 0, sy = 0, ox = 0, oy = 0, moved = false, id = null;
    p.addEventListener("pointerdown", (e) => { id = e.pointerId; sx = e.clientX; sy = e.clientY; const rc = p.getBoundingClientRect(); ox = rc.left; oy = rc.top; moved = false; try { p.setPointerCapture(id); } catch (err) {} });
    p.addEventListener("pointermove", (e) => {
      if (e.pointerId !== id) return;
      const dx = e.clientX - sx, dy = e.clientY - sy;
      if (!moved && Math.hypot(dx, dy) < 6) return;
      moved = true; p.style.transform = "none"; p.style.animation = "none";
      p.style.left = Math.min(Math.max(ox + dx, 4), innerWidth - p.offsetWidth - 4) + "px";
      p.style.top = Math.min(Math.max(oy + dy, 4), innerHeight - p.offsetHeight - 4) + "px";
    });
    p.addEventListener("pointerup", (e) => { if (e.pointerId !== id) return; id = null; if (!moved) p.remove(); });
    document.body.appendChild(p);
    setTimeout(() => p.remove(), lv === "khan_cap" ? 15000 : 8000);
  }
  async function sysNotify(lv, label) {
    if (!S.notify || !notifySupported() || Notification.permission !== "granted") return;
    const title = lv === "luu_y_test" ? "EduShield 🔔" : `EduShield: ${LV_IC[lv] || ""} ${LV_VI[lv] || "Cảnh báo"}`;
    const opt = { body: `${label}. Mở EduShield để xem gợi ý, bạn là người quyết định.`, icon: "icon-192.png", badge: "icon-192.png", tag: "edushield-alert", renotify: true };
    try { const reg = navigator.serviceWorker && (await navigator.serviceWorker.getRegistration()); if (reg) return reg.showNotification(title, opt); } catch (e) {}
    try { new Notification(title, opt); } catch (e) {}
  }
  function renderAlerts() {
    const list = S.alerts || [];
    $("alList").innerHTML = list.length ? list.map((a) => `<div class="al"><span class="lvb">${LV_IC[a.lv] || "🔔"}</span><div><b>${esc(a.lb)}</b><small>${esc(LV_VI[a.lv] || "")} · ${esc(a.d)}</small></div></div>`).join("")
      : `<p class="small">✅ Chưa có cảnh báo nào.</p>`;
    const c = $("alCnt"); c.textContent = S.unseen; c.classList.toggle("hide", !S.unseen);
    const on = S.notify && notifySupported() && Notification.permission === "granted";
    $("ntPill").textContent = on ? "Đang bật" : "Đang tắt"; $("ntPill").className = "pill " + (on ? "on" : "off");
    $("ntBtn").textContent = on ? "🔕 Tắt thông báo" : "🔔 Bật thông báo";
    const ios = /iPhone|iPad|iPod/.test(navigator.userAgent);
    $("ntHint").textContent = !notifySupported() ? (ios ? "iPhone/iPad: cần “Thêm vào Màn hình chính” rồi mở app từ biểu tượng (iOS 16.4 trở lên) mới bật được thông báo." : "Trình duyệt này chưa hỗ trợ thông báo.")
      : Notification.permission === "denied" ? "Bạn đã chặn thông báo. Vào cài đặt trang web của trình duyệt để cho phép lại." : "";
  }
  async function toggleNotify() {
    if (S.notify && notifySupported() && Notification.permission === "granted") { S.notify = false; save(); return renderAlerts(); }
    if (!notifySupported()) return renderAlerts();
    let perm = Notification.permission;
    if (perm === "default") { try { perm = await Notification.requestPermission(); } catch (e) {} }
    S.notify = perm === "granted"; save(); renderAlerts();
    if (S.notify) sysNotify("luu_y_test", "Thông báo đã bật");
  }
  function render(r, bad) {
    const el = $("result");
    if (!r.warn && !bad.length && r.frame === "tuyen_truyen") {
      el.innerHTML = `<div class="card lv"><b>ℹ️ Nội dung tuyên truyền, cảnh báo</b><p class="small">Tin này nhắc tới thủ đoạn lừa đảo hoặc bắt nạt để mọi người cảnh giác, không nhắm vào bạn. Nếu ai đó gửi riêng cho bạn kèm yêu cầu chuyển tiền, đọc mã hay giữ bí mật, hãy hỏi người lớn.</p></div>`;
      return;
    }
    if (!r.warn && !bad.length) {
      el.innerHTML = `<div class="card lv"><b>✅ Chưa thấy dấu hiệu rõ ràng</b><p class="small">Mô hình có thể sai. Nếu bạn vẫn thấy lo, hãy tin cảm giác của mình và hỏi một người lớn đáng tin.</p></div>`;
      return;
    }
    const lv = bad.length ? "khan_cap" : r.level;
    const todo = bad.length ? D.TODO_CAT.link_nguy_hiem.concat(r.warn ? r.todo.slice(0, 2) : []) : (r.todo && r.todo.length ? r.todo : D.TODO.lua_dao);
    const TAG = { khan_cap: "Khẩn cấp", canh_bao: "Cảnh báo", luu_y: "Cần lưu ý" };
    el.innerHTML = `<div class="card lv ${lv}"><b>${lv === "khan_cap" ? "🚨" : lv === "canh_bao" ? "⚠️" : "💡"} ${esc(bad.length ? "Link nguy hiểm" : (r.cat_vi || r.label_vi))}</b> <span class="pill lvp ${lv}">${TAG[lv] || ""}</span>
      ${bad.length ? `<p>🔎 <b class="rd">Đừng bấm:</b> ${bad.map(esc).join(", ")} (đã bị báo cáo lừa đảo)</p>` : ""}
      ${r.warn ? `<p>🔎 ${esc(r.main)}</p>${r.phrases && r.phrases.length ? `<p class="small">Cụm từ đáng chú ý: ${r.phrases.map((x) => `<span class="kw">${esc(x)}</span>`).join(" ")}</p>` : ""}<p class="small">${esc(r.friendly)}</p>` : ""}
      <button id="todoBtn">📋 Cần làm gì ngay?</button><button class="sec" id="sosBtn">🆘 Báo người thân</button><button class="sec" id="notRisk">🙅 Không phải nguy cơ</button><div id="todoBox"></div><div id="sosBox"></div></div>`;
    $("sosBtn").onclick = () => { $("sosBox").innerHTML = $("sosBox").innerHTML ? "" : `<div class="todo"><b>🆘 Báo cho người bạn tin</b>${contactLinks(bad.length ? "Link lừa đảo" : (r.cat_vi || r.label_vi))}<a href="tel:111">📞 Gọi 111 (miễn phí)</a></div>`; };
    $("todoBtn").onclick = () => {
      if ($("todoBox").innerHTML) { $("todoBox").innerHTML = ""; $("todoBtn").textContent = "📋 Cần làm gì ngay?"; return; }
      $("todoBox").innerHTML = `<div class="todo"><b>📝 Việc nên làm ngay</b><ol>${todo.map((x) => `<li>${esc(x)}</li>`).join("")}</ol>
        <button class="sec" id="cp">📨 Sao chép lời nhờ người lớn giúp</button> <a href="tel:111">📞 Gọi 111</a><p class="small">Lời nhờ giúp không kèm nội dung tin nhắn.</p></div>`;
      $("todoBtn").textContent = "📋 Ẩn hướng dẫn";
      $("cp").onclick = () => { (navigator.clipboard ? navigator.clipboard.writeText(D.HELP_MSG) : Promise.reject()).then(() => ($("cp").textContent = "✅ Đã sao chép")).catch(() => ($("cp").textContent = D.HELP_MSG)); };
    };
    $("notRisk").onclick = () => {
      const d = S.daily[today()]; if (d) d.ev = {}; save(); el.innerHTML = `<div class="card">Đã bỏ ghi nhận hôm nay. Cảm ơn bạn đã góp ý.</div>`; info();
    };
  }

  const SAMPLES = [
    "Cô chủ nhiệm đây, em chuyển gấp 500k tiền học phí vào stk 190355667788 nhé, không là bị khoá tài khoản",
    "Đồ ngu, cả lớp ghét mày, biến đi cho khuất mắt",
    "Mai ra sân trường nhé, mình cùng ôn bài môn Toán",
    "Công an khuyến cáo: đối tượng giả danh công an gọi điện doạ học sinh liên quan vụ án, yêu cầu giữ bí mật và chuyển tiền. Tuyệt đối không làm theo, hãy báo bố mẹ ngay.",
  ];

  // ---- Randomized Response ----
  const rand01 = () => crypto.getRandomValues(new Uint32Array(1))[0] / 4294967296;
  function trueBits(d) { const b = {}; for (const c of M.categories) b[c] = d && d.ev && d.ev[c] ? 1 : 0; return b; }
  function packet(day, d) {
    const p = Math.exp(M.epsilon) / (1 + Math.exp(M.epsilon)), bits = {}, t = trueBits(d);
    for (const c in t) bits[c] = rand01() < p ? t[c] : 1 - t[c];
    return { v: 1, school: SCHOOL, grade: "", day, eps: M.epsilon, bits };
  }
  function shareReady() { return S.share.enabled && S.share.parental && /^[A-Za-z0-9_]{2,30}$/.test(SCHOOL); }
  async function send(day) {
    if (!COLLECT) return { ok: false, error: "Bản công khai không gửi dữ liệu." };
    if (!shareReady()) return { ok: false, error: "Chưa bật gửi thống kê." };
    if (S.sentDays.includes(day)) return { ok: false, error: "Hôm nay đã gửi một gói. Mỗi ngày chỉ gửi một lần." };
    const d = S.daily[day]; if (!d || !d.active) return { ok: false, error: "Hôm nay bạn chưa dùng EduShield nên không có gì để gửi." };
    try {
      const r = await fetch(SERVER + "/thongke", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(packet(day, d)), credentials: "omit" });
      if (!r.ok) return { ok: false, error: [502, 503, 504, 404].includes(r.status) ? "Máy chủ của trường đang tắt (server.py chưa chạy). Báo thầy cô kiểm tra." : "Máy chủ trả về " + r.status };
      S.sentDays.push(day); S.sentDays = S.sentDays.slice(-30); delete S.daily[day]; save(); return { ok: true };
    } catch (e) { return { ok: false, error: "Không kết nối được máy chủ của trường (máy chủ đang tắt, cổng chưa để Public, hoặc mất mạng). Máy sẽ tự thử lại khi mở app." }; }
  }

  function dataSummary() {
    const dl = {}; for (const [d, v] of Object.entries(S.daily)) { dl[d] = {}; for (const [c, x] of Object.entries(v.ev || {})) if (x) dl[d][c] = 1; }
    return JSON.stringify({ dongY: S.consented, canhBaoGanDay: S.alerts, thongBao: S.notify, doNhay: S.sens, theoNgay: dl, daGuiCacNgay: S.sentDays, dongGopThongKe: S.share.enabled }, null, 1);
  }
  function info() {
    const n = Object.keys(S.daily).length;
    $("localInfo").textContent = `Máy này chỉ lưu: lựa chọn của bạn và mã loại nguy cơ theo ngày (${n} ngày). Không có nội dung tin nhắn, không có link, không có giờ. Danh sách cảnh báo: ${(S.alerts || []).length} mục (chỉ loại và ngày).`;
  }
  function tab(t) {
    for (const k of ["check", "alerts", "stats", "help"]) $("tab-" + k).classList.toggle("hide", k !== t);
    if (t === "alerts") { S.unseen = 0; save(); renderAlerts(); }
    document.querySelectorAll("nav button").forEach((b) => b.classList.toggle("on", b.dataset.t === t));
  }

  function init() {
    load();
    document.querySelectorAll("nav button").forEach((b) => (b.onclick = () => tab(b.dataset.t)));
    $("agree").onchange = () => ($("startBtn").disabled = !$("agree").checked);
    const dots = document.querySelectorAll(".dots i");
    document.querySelectorAll("[data-go]").forEach((b) => (b.onclick = () => { const n = +b.dataset.go; ["c1", "c2", "c3"].forEach((k, i) => $(k).classList.toggle("hide", i + 1 !== n)); dots.forEach((d, i) => d.classList.toggle("on", i + 1 === n)); }));
    document.querySelectorAll("[data-s]").forEach((b) => (b.onclick = () => { $("txt").value = SAMPLES[+b.dataset.s]; check($("txt").value); }));
    $("sens").value = S.sens; $("large").checked = S.large; document.body.classList.toggle("large", !!S.large);
    $("sens").onchange = () => { S.sens = $("sens").value; save(); };
    $("large").onchange = () => { S.large = $("large").checked; document.body.classList.toggle("large", S.large); save(); };
    $("ntBtn").onclick = toggleNotify;
    $("alClear").onclick = () => { S.alerts = []; S.unseen = 0; save(); renderAlerts(); };
    renderAlerts();
    $("seeData").onclick = () => { $("dataOut").classList.toggle("hide"); $("dataOut").textContent = dataSummary(); };
    if (!COLLECT) { $("shareCard").classList.add("hide"); $("noCollect").classList.remove("hide"); S.share.enabled = false; }
    $("startBtn").onclick = () => { S.consented = true; save(); $("consent").classList.add("hide"); $("tab-check").classList.remove("hide"); };
    $("checkBtn").onclick = () => { const t = $("txt").value.trim(); if (t) check(t); };
    $("clearBtn").onclick = () => { $("txt").value = ""; $("result").innerHTML = ""; };
    $("outBtn").onclick = checkOutgoing;
    const msg = (t, err) => { const m = $("shMsg"); m.classList.toggle("hide", !t); m.textContent = t || ""; m.classList.toggle("err", !!err); };
    const HINT = { tat: "Không gửi gì về trường.", an_danh: "Mỗi ngày một gói có/không đã trộn nhiễu; tự gửi khi có cảnh báo khẩn cấp. Không có tên, không có nội dung.",
      danh_tinh: "Khi có cảnh báo khẩn cấp, sau 10 giây (bạn có thể huỷ) EduShield báo thầy cô: tên, lớp, loại nguy cơ. Không gửi nội dung tin nhắn." };
    let mode = S.share.enabled ? S.share.mode || "an_danh" : "tat";
    const paint = () => {
      document.querySelectorAll("#modeSeg button").forEach((b) => b.classList.toggle("on", b.dataset.m === mode));
      $("modeHint").textContent = HINT[mode];
      $("idBox").classList.toggle("hide", mode !== "danh_tinh");
      $("consentRow").classList.toggle("hide", mode === "tat" || S.share.parental);
      const on = !!S.share.enabled; $("shPill").textContent = !on ? "Đang tắt" : S.share.mode === "danh_tinh" ? "Có tên – lớp" : "Ẩn danh"; $("shPill").className = "pill " + (on ? "on" : "off");
      $("shSend").classList.toggle("hide", !on); $("shPrev").classList.toggle("hide", !on);
    };
    $("stName").value = S.share.name || ""; $("stCls").value = S.share.lop || "";
    document.querySelectorAll("#modeSeg button").forEach((b) => (b.onclick = () => { mode = b.dataset.m; msg(""); paint(); }));
    const explain = (r) => r.ok ? "Đã lưu và gửi gói ẩn danh ✓" : (r.error && /đã gửi một gói/.test(r.error) ? "Đã lưu ✓ Hôm nay đã gửi một gói." : (r.error && /chưa dùng/.test(r.error) ? "Đã lưu ✓ Máy sẽ tự gửi khi có dữ liệu." : "Đã lưu. Chưa gửi được: " + r.error));
    $("shSave").onclick = async () => {
      if (mode === "tat") { S.share.enabled = false; save(); paint(); return msg("Đã tắt. Không còn gì được gửi về trường.", false); }
      const nm = $("stName").value.replace(/\s+/g, " ").trim(), cls = $("stCls").value.replace(/\s+/g, " ").trim();
      if (mode === "danh_tinh" && (nm.length < 2 || !cls)) return msg("Nhập họ tên và lớp để thầy cô biết ai cần hỗ trợ.", true);
      if (!S.share.parental && !$("parental").checked) return msg("Hãy tích ô xác nhận tự nguyện tham gia.", true);
      S.share = { enabled: true, parental: true, mode, name: mode === "danh_tinh" ? nm : "", lop: mode === "danh_tinh" ? cls : "" }; save(); paint();
      const r = await send(today()); const noData = r.error && /chưa dùng|đã gửi một gói/.test(r.error); msg(explain(r), !r.ok && !noData); info();
    };
    $("shSend").onclick = async () => { const r = await send(today()); const noData = r.error && /chưa dùng|đã gửi một gói/.test(r.error); msg(explain(r).replace("Đã lưu và ", "").replace("Đã lưu ✓ ", "").replace("Đã lưu. ", ""), !r.ok && !noData); info(); };
    $("shPrev").onclick = () => {
      const d = today(), t = trueBits(S.daily[d]), p = packet(d, S.daily[d]);
      $("shOut").classList.toggle("hide");
      $("shOut").textContent = "Gói ẩn danh SẼ gửi (đã trộn nhiễu):\n" + JSON.stringify(p, null, 1) + "\n\nNhà trường không nhận: nội dung, link, giờ, mã máy." +
        (S.share.mode === "danh_tinh" ? "\nKhi có cảnh báo khẩn cấp, yêu cầu hỗ trợ gồm: tên, lớp, loại nguy cơ." : "");
    };
    paint();
    // Người hỗ trợ khẩn cấp
    $("ctAddBtn").onclick = () => $("ctForm").classList.remove("hide");
    $("ctCancel").onclick = () => $("ctForm").classList.add("hide");
    $("ctSave").onclick = () => {
      const name = $("ctName").value.trim(), phone = $("ctPhone").value.replace(/[^\d+]/g, "");
      if (!name || !/^(\+?84|0)\d{8,10}$/.test(phone)) { alert("Nhập tên gọi và số điện thoại Việt Nam hợp lệ (vd 0912345678)."); return; }
      S.contacts = S.contacts.concat({ name: name.slice(0, 30), phone }).slice(0, 3); save();
      $("ctName").value = ""; $("ctPhone").value = ""; $("ctForm").classList.add("hide"); renderContacts();
    };
    renderContacts();
    // Dán từ bộ nhớ tạm (sau khi “Sao chép” tin nhắn trong Zalo, Messenger)
    $("pasteBtn").onclick = async () => {
      try { const t = (await navigator.clipboard.readText()).trim(); if (t) { $("txt").value = t; check(t); } else alert("Bộ nhớ tạm đang trống. Hãy nhấn giữ tin nhắn → Sao chép trước."); }
      catch (e) { $("txt").focus(); alert("Trình duyệt không cho đọc bộ nhớ tạm. Hãy nhấn giữ ô bên trên → Dán, rồi bấm Kiểm tra."); }
    };
    if (COLLECT && S.emgPending && shareReady()) send(today()).then((r) => { if (r.ok) { S.emgPending = false; save(); } });
    // Tự động gửi các ngày đã kết thúc khi mở ứng dụng (ứng dụng web không chạy nền)
    if (COLLECT && shareReady()) for (const day of Object.keys(S.daily).sort()) if (day < today()) send(day);
    $("wipe").onclick = () => { if (confirm("Xoá toàn bộ dữ liệu EduShield trên máy này?")) { try { localStorage.removeItem(KEY); } catch (e) {} load(); location.href = location.pathname; } };
    info();
    // ---- cài app và chia sẻ ----
    const standalone = matchMedia("(display-mode: standalone)").matches || navigator.standalone === true;
    const isIOS = /iPhone|iPad|iPod/.test(navigator.userAgent) || (/Macintosh/.test(navigator.userAgent) && navigator.maxTouchPoints > 1);
    let deferred = null;
    window.addEventListener("beforeinstallprompt", (e) => { e.preventDefault(); deferred = e; $("installBtn").classList.remove("hide"); });
    window.addEventListener("appinstalled", () => { $("installBtn").classList.add("hide"); $("installHint").textContent = "Đã cài app ✓"; });
    $("installBtn").onclick = async () => { if (!deferred) return; deferred.prompt(); try { await deferred.userChoice; } catch (e) {} deferred = null; $("installBtn").classList.add("hide"); };
    if (standalone) $("installHint").textContent = "Bạn đang dùng app đã cài ✓";
    else if (isIOS) $("installHint").textContent = "iPhone/iPad: mở bằng Safari → nút Chia sẻ → “Thêm vào Màn hình chính”.";
    const guideUrl = new URL("cai-dat.html", location.href).href;
    $("shareApp").onclick = async () => {
      const m = $("installMsg"); m.classList.remove("hide", "err");
      try { if (navigator.share) { await navigator.share({ title: "EduShield AI", text: "Cài EduShield để nhận cảnh báo tin nhắn xấu và lừa đảo:", url: guideUrl }); m.classList.add("hide"); return; } } catch (e) { m.classList.add("hide"); return; }
      try { await navigator.clipboard.writeText(guideUrl); m.textContent = "Đã sao chép đường link hướng dẫn cài đặt ✓"; } catch (e) { m.textContent = "Link hướng dẫn: " + guideUrl; }
    };
    if (!S.consented) { $("consent").classList.remove("hide"); $("tab-check").classList.add("hide"); }
    // Web Share Target: học sinh CHỦ ĐỘNG bấm “Chia sẻ → EduShield” nên app kiểm tra ngay
    const q = new URLSearchParams(location.search), shared = [q.get("title"), q.get("text"), q.get("url")].filter(Boolean).join("\n");
    if (shared) { $("txt").value = shared; history.replaceState(null, "", location.pathname); if (S.consented) check(shared); }
    if ("serviceWorker" in navigator && (location.protocol === "https:" || location.hostname === "localhost" || location.hostname === "127.0.0.1")) navigator.serviceWorker.register("sw.js").catch(() => {});
  }
  init();
  globalThis.__EduShieldApp = { check, packet, sha };
  // ---- v1.8: Thực chiến giả lập: hiện Chỉ số miễn dịch số; nếu tới giờ diễn tập thì báo "tin nhắn mới" ----
  (async function drillCard() {
    const DR = globalThis.EduShieldDrill; if (!DR) return;
    const st = await DR.load(), d = DR.dii(st), el = document.getElementById("drillState"), card = document.getElementById("drillCard");
    if (!el || !card) return;
    el.textContent = `Chỉ số miễn dịch số ${d.value}/100 · ${d.level}`;
    if (st.enabled && st.consent && st.next && Date.now() >= st.next) {
      const sc = DR.pick(st); st.pending = sc.id; await DR.save(st);
      card.classList.add("due"); card.href = "drill.html?id=" + sc.id;
      el.innerHTML = `📩 <b>Tin nhắn mới từ ${sc.from.replace(/[<>&]/g, "")}</b>`;
      try {
        if (Notification.permission === "granted" && navigator.serviceWorker) {
          const reg = await navigator.serviceWorker.ready;
          reg.showNotification("📩 " + sc.from, { body: sc.msgs[0], icon: "icon-192.png", tag: "drill", data: { url: "drill.html?id=" + sc.id } });
        }
      } catch (e) {}
    }
  })();
})();

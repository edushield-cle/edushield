// EduShield - tiến trình nền: menu chuột phải, kết nối máy chủ, và gửi thống kê ẩn danh hằng ngày.
importScripts("config.js", "model.js", "drill.js"); // cấu hình trường/máy chủ do người triển khai đặt; danh mục loại nguy cơ và mức riêng tư epsilon
const M = globalThis.EDUSHIELD_MODEL;
const DEPLOY = globalThis.EDUSHIELD_DEPLOY || { school: "", server: "http://127.0.0.1:8765" };
const DEFAULT_SERVER = DEPLOY.server;
const DEFAULT_SHARE = { enabled: false, parental: false, mode: "an_danh", name: "", lop: "" };

chrome.runtime.onInstalled.addListener((d) => {
  if (d.reason === "install") chrome.tabs.create({ url: chrome.runtime.getURL("onboarding.html") }); // màn hình đồng ý, mặc định chưa quét gì
  chrome.contextMenus.create({ id: "edushield-check", title: "Kiểm tra với EduShield", contexts: ["selection"] });
  chrome.alarms.create("edushield-daily", { periodInMinutes: 60 });
  refreshBlocklist();
  injectIntoOpenTabs(); // tab Zalo/Messenger đang mở sẵn cũng được bảo vệ ngay, không cần tải lại trang
});
// Chrome chỉ tự chạy tiện ích ở trang MỞ SAU khi cài. Với trang đã mở từ trước, ta chủ động nạp vào.
async function injectIntoOpenTabs() {
  const cs = chrome.runtime.getManifest().content_scripts[0];
  try {
    const tabs = await chrome.tabs.query({ url: cs.matches });
    for (const t of tabs) chrome.scripting.executeScript({ target: { tabId: t.id }, files: cs.js }).catch(() => {});
  } catch (e) {}
}
chrome.runtime.onStartup.addListener(() => { refreshBlocklist(); flushDaily(); });
chrome.alarms.onAlarm.addListener((a) => {
  if (a.name === "edushield-daily") flushDaily();
  if (a.name === "edushield-emg") flushDaily(true); // gói ẩn danh của hôm nay, gửi sau cảnh báo khẩn cấp
  if (a.name === "edushield-drill") drillFire();
});

// ---------- v1.8: THỰC CHIẾN GIẢ LẬP (học sinh tự bật). Tin diễn tập luôn là thông báo của EduShield. ----------
async function drillFire() {
  const D = globalThis.EduShieldDrill, st = await D.load();
  if (!st.enabled || !st.consent) return;
  const sc = D.pick(st);
  st.pending = sc.id; st.next = D.scheduleNext(st); await D.save(st);
  if (st.next) chrome.alarms.create("edushield-drill", { when: st.next });
  chrome.notifications.create("drill-" + sc.id + "-" + Date.now(), {
    type: "basic", iconUrl: "icon128.png", title: "📩 " + sc.from, message: sc.msgs[0].slice(0, 120), priority: 1,
  });
}
function drillSchedule(next) {
  chrome.alarms.clear("edushield-drill", () => { if (next && next > Date.now()) chrome.alarms.create("edushield-drill", { when: next }); });
}

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "edushield-check" && tab && tab.id !== undefined) {
    chrome.tabs.sendMessage(tab.id, { type: "manualCheck", text: info.selectionText }).catch(() => {});
  }
});

async function call(path, payload, base = DEFAULT_SERVER) {
  const opt = payload ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) } : {};
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 25000);
  try {
    const r = await fetch(base + path, { ...opt, signal: ctrl.signal, credentials: "omit" });
    // Cổng Codespaces để Private: GitHub chuyển hướng sang trang đăng nhập github.com thay vì tới server.py
    if (r.redirected && /github\.com/.test(new URL(r.url).hostname)) return { ok: false, error: "Bị chuyển sang trang đăng nhập GitHub", kind: "private" };
    if (!r.ok) return { ok: false, error: "HTTP " + r.status, kind: [502, 503, 504, 404].includes(r.status) ? "server_off" : "http" };
    try { return { ok: true, data: await r.json() }; }
    catch (e) { return { ok: false, error: "Trả về trang không phải của EduShield", kind: "private" }; }
  } catch (e) {
    return { ok: false, error: String(e), kind: e.name === "AbortError" ? "timeout" : "network" };
  } finally {
    clearTimeout(t);
  }
}

async function refreshBlocklist() {
  const r = await call("/blocklist");
  if (r.ok && Array.isArray(r.data.hashes)) chrome.storage.local.set({ blocklist: r.data.hashes });
}

// ---------- Thống kê ẩn danh: Randomized Response ----------
function rand01() { return crypto.getRandomValues(new Uint32Array(1))[0] / 4294967296; }
function trueBits(dayData) {
  const bits = {};
  for (const c of M.categories) bits[c] = dayData && dayData.ev && dayData.ev[c] && dayData.ev[c].length ? 1 : 0;
  return bits;
}
function randomize(bits, eps) {
  const p = Math.exp(eps) / (1 + Math.exp(eps)); // xác suất giữ đúng
  const out = {};
  for (const c in bits) out[c] = rand01() < p ? bits[c] : 1 - bits[c];
  return out;
}
// Gói gửi đi: chỉ gồm các trường dưới đây. Không có ID máy, không giờ phút, không nội dung, không link.
function buildPacket(day, dayData, share) {
  return { v: 1, school: DEPLOY.school, grade: "", day, eps: M.epsilon, bits: randomize(trueBits(dayData), M.epsilon) };
}

async function flushDaily(force = false) {
  const s = await chrome.storage.local.get({ daily: {}, share: DEFAULT_SHARE, sentDays: [] });
  const t = new Date().toLocaleDateString("sv-SE");
  const limit = new Date(Date.now() - 7 * 864e5).toLocaleDateString("sv-SE");
  let sent = 0, error = "", kind = "";
  for (const day of Object.keys(s.daily).sort()) {
    if (day === t && !force) continue; // chỉ gửi ngày đã kết thúc
    const d = s.daily[day];
    // Mỗi ngày chỉ gửi MỘT gói: gửi nhiều gói nhiễu độc lập cho cùng một ngày sẽ làm lộ giá trị thật khi lấy trung bình
    if (s.sentDays.includes(day)) { delete s.daily[day]; continue; }
    if (s.share.enabled && s.share.parental && DEPLOY.school && d.active) {
      const r = await call("/thongke", buildPacket(day, d, s.share), DEPLOY.server);
      if (!r.ok && day >= limit) { error = r.error; kind = r.kind || kind; continue; } // thử lại sau, tối đa 7 ngày
      if (r.ok) { sent++; s.sentDays.push(day); }
    }
    delete s.daily[day]; // gửi xong (hoặc không tham gia) thì xoá luôn dữ liệu ngày đó trên máy
  }
  await chrome.storage.local.set({ daily: s.daily, sentDays: s.sentDays.slice(-30) });
  const todayDone = (await chrome.storage.local.get({ sentDays: [] })).sentDays.includes(t);
  return { ok: !error, sent, error, kind, todayDone };
}

// Thông báo hệ thống: chỉ có mức độ, KHÔNG có nội dung tin nhắn. Bấm vào thì đưa người dùng về đúng tab.
chrome.notifications.onClicked.addListener((id) => {
  const dm = /^drill-([a-z0-9]+)-/.exec(id);
  if (dm) { chrome.tabs.create({ url: chrome.runtime.getURL("drill.html?id=" + dm[1]) }); chrome.notifications.clear(id); return; }
  const m = /^es-(\d+)-(\d+)-/.exec(id);
  if (!m) return;
  chrome.tabs.update(+m[2], { active: true }, () => { void chrome.runtime.lastError; });
  chrome.windows.update(+m[1], { focused: true }, () => { void chrome.runtime.lastError; });
  chrome.notifications.clear(id);
});
function showSysNotification(msg, sender) {
  const t = sender && sender.tab;
  if (!t) return;
  chrome.notifications.create(`es-${t.windowId}-${t.id}-${Date.now()}`, {
    type: "basic", iconUrl: "icon128.png",
    title: "EduShield: " + String(msg.title || "Cần bạn chú ý").slice(0, 40),
    message: "Có nội dung cần bạn xem. Mở trang đang dùng để xem chi tiết, bạn là người quyết định.",
    priority: msg.level === "khan_cap" ? 2 : 1,
  });
}

// ---------- v1.6: CẢNH BÁO KHẨN CẤP -> gửi về trường (theo lựa chọn của học sinh) ----------
// Ẩn danh: gửi gói thống kê của hôm nay sau 2-10 phút ngẫu nhiên (để thời điểm gửi không trùng đúng lúc gặp nguy cơ).
async function onEmergency() {
  const { share } = await chrome.storage.local.get({ share: DEFAULT_SHARE });
  if (!share.enabled || !share.parental) return { ok: true, scheduled: false };
  chrome.alarms.create("edushield-emg", { delayInMinutes: 2 + Math.random() * 8 });
  return { ok: true, scheduled: true };
}
// Có tên - lớp: chỉ gửi tên, lớp, LOẠI nguy cơ, mức độ. Mỗi loại tối đa một lần mỗi ngày.
async function supportRequest(cat, level) {
  const s = await chrome.storage.local.get({ share: DEFAULT_SHARE, supportSent: [] });
  const sh = s.share;
  if (!sh.enabled || !sh.parental || sh.mode !== "danh_tinh" || !sh.name || !sh.lop || !DEPLOY.school) return { ok: false, error: "Chưa bật chế độ có tên - lớp" };
  const day = new Date().toLocaleDateString("sv-SE"), key = day + "|" + cat;
  if (s.supportSent.includes(key)) return { ok: true, skipped: true };
  const r = await call("/hotro", { v: 1, school: DEPLOY.school, name: sh.name, lop: sh.lop, cat, level }, DEPLOY.server);
  if (r.ok) await chrome.storage.local.set({ supportSent: s.supportSent.concat(key).slice(-60) });
  return r;
}
// Báo người thân: số điện thoại chỉ đọc ở đây (không đưa vào trang web đang mở)
const HELP_SMS = (catVi) => "[EduShield] Con/em đang gặp chuyện trên mạng" + (catVi ? " (" + catVi + ")" : "") + ", cần người giúp ngay. Gọi lại cho con/em nhé.";
async function contactAction(i, action, catVi) {
  const { contacts } = await chrome.storage.local.get({ contacts: [] });
  const c = contacts[i]; if (!c) return { ok: false };
  const ph = c.phone.replace(/[^\d+]/g, ""), local = ph.replace(/^\+?84/, "0");
  const url = action === "call" ? "tel:" + ph : action === "sms" ? "sms:" + ph + "?body=" + encodeURIComponent(HELP_SMS(catVi)) : "https://zalo.me/" + local;
  await chrome.tabs.create({ url });
  return { ok: true };
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg && msg.type === "drillSchedule") { drillSchedule(msg.next); sendResponse({ ok: true }); return; }
  if (msg.type === "notify") { showSysNotification(msg, sender); return; }
  if (msg.type === "emergency") { onEmergency().then(sendResponse); return true; }
  if (msg.type === "supportRequest") { supportRequest(String(msg.cat || ""), msg.level === "khan_cap" ? "khan_cap" : "canh_bao").then(sendResponse); return true; }
  if (msg.type === "contactAction") { contactAction(+msg.i, msg.action, msg.catVi || "").then(sendResponse); return true; }
  if (msg.type === "shareSet") {
    const sh = Object.assign({}, DEFAULT_SHARE, msg.share || {});
    chrome.storage.local.set({ share: sh }, () => (sh.enabled ? flushDaily(true).then(sendResponse) : sendResponse({ ok: true })));
    return true;
  }
  if (msg.type === "openOnboarding") { chrome.tabs.create({ url: chrome.runtime.getURL("onboarding.html") }); return; }
  if (msg.type === "inject" && msg.tabId !== undefined) {
    const cs = chrome.runtime.getManifest().content_scripts[0];
    chrome.scripting.executeScript({ target: { tabId: msg.tabId }, files: cs.js }).then(() => sendResponse({ ok: true })).catch((e) => sendResponse({ ok: false, error: String(e) }));
    return true;
  }
  if (msg.type === "analyze") call("/analyze", { masked: msg.masked, domains: msg.domains }).then(sendResponse);
  else if (msg.type === "report") call("/report", { masked: msg.masked, domains: msg.domains, label: msg.label }).then((r) => { refreshBlocklist(); sendResponse(r); });
  else if (msg.type === "health") call("/health").then((r) => sendResponse({ ...r, server: DEFAULT_SERVER }));
  else if (msg.type === "sharePreview") {
    chrome.storage.local.get({ daily: {}, share: DEFAULT_SHARE }, (s) => {
      const day = new Date().toLocaleDateString("sv-SE");
      const d = s.daily[day];
      sendResponse({ ok: true, trueBits: trueBits(d), packet: buildPacket(day, d, s.share), p: Math.exp(M.epsilon) / (1 + Math.exp(M.epsilon)) });
    });
  } else if (msg.type === "shareOn") {
    // Học sinh bấm "Gửi": bật gửi tự động mỗi ngày và gửi ngay gói của hôm nay. Không cần nhập gì thêm.
    chrome.storage.local.get({ share: DEFAULT_SHARE }, ({ share }) => {
      chrome.storage.local.set({ share: { ...share, enabled: true, parental: true } }, () => flushDaily(true).then(sendResponse));
    });
  } else if (msg.type === "shareOff") {
    chrome.storage.local.get({ share: DEFAULT_SHARE }, ({ share }) => chrome.storage.local.set({ share: { ...share, enabled: false } }, () => sendResponse({ ok: true })));
  } else if (msg.type === "shareNow") flushDaily(true).then(sendResponse);
  else return false;
  return true;
});

// Số cảnh báo chưa xem hiện trên biểu tượng tiện ích
function paintBadge(n) { chrome.action.setBadgeText({ text: n ? String(Math.min(n, 99)) : "" }); chrome.action.setBadgeBackgroundColor({ color: "#d1242f" }); }
chrome.storage.onChanged.addListener((ch) => { if (ch.unseenAlerts) paintBadge(ch.unseenAlerts.newValue || 0); });
chrome.storage.local.get({ unseenAlerts: 0 }, (s) => paintBadge(s.unseenAlerts));

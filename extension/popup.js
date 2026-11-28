const $ = (id) => document.getElementById(id);
// Mở trong một tab (quay về từ Thực chiến giả lập) thay vì cửa sổ nhỏ của tiện ích
const FULL = new URLSearchParams(location.search).has("full");
if (FULL) document.documentElement.classList.add("full");
let host = "";
const escH = (x) => String(x).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

function notifyTab() {
  chrome.tabs.query({ active: true, currentWindow: true }, ([tab]) => {
    if (tab && tab.id !== undefined) chrome.tabs.sendMessage(tab.id, { type: "settingsChanged" }).catch(() => {});
  });
}

// ---------- Cài đặt ----------
chrome.tabs.query({ active: true, currentWindow: true }, ([tab]) => {
  try { host = new URL(tab.url).hostname; } catch (e) { host = ""; }
  $("site").textContent = host || "(trang không hỗ trợ)";
  chrome.storage.local.get({ enabled: true, disabledSites: [], stats: {}, sens: "can_bang", large: false, sysNotify: true, mediaScan: true, sendNudge: true, blurViolent: true, nudgeStats: {} }, (s) => {
    $("sens").value = s.sens; $("large").checked = s.large; $("sysNotify").checked = s.sysNotify !== false; $("mediaScan").checked = s.mediaScan !== false; $("sendNudge").checked = s.sendNudge !== false; $("blurViolent").checked = s.blurViolent !== false;
    const ns = s.nudgeStats || {}; $("nudgeLine").textContent = `✋ Đã nhắc trước khi gửi ${ns.shown || 0} lần · bạn tự sửa ${ns.fixed || 0} lần · 🙈 đã làm mờ ${ns.blurred || 0} ảnh/video (chỉ lưu trên máy này)`;
    $("enabled").checked = s.enabled;
    $("siteOn").checked = !s.disabledSites.includes(host);
    for (const k of ["scanned", "warnings", "links", "notRisk"]) $(k).textContent = s.stats[k] || 0;
  });
});
$("sens").onchange = (e) => chrome.storage.local.set({ sens: e.target.value }, notifyTab);
$("mediaScan").onchange = (e) => chrome.storage.local.set({ mediaScan: e.target.checked }, notifyTab);
$("sendNudge").onchange = (e) => chrome.storage.local.set({ sendNudge: e.target.checked }, notifyTab);
$("blurViolent").onchange = (e) => chrome.storage.local.set({ blurViolent: e.target.checked }, notifyTab);
$("sysNotify").onchange = (e) => chrome.storage.local.set({ sysNotify: e.target.checked }, notifyTab);
$("large").onchange = (e) => chrome.storage.local.set({ large: e.target.checked }, notifyTab);
$("mydata").onclick = () => chrome.tabs.create({ url: chrome.runtime.getURL("mydata.html") });
$("enabled").onchange = (e) => chrome.storage.local.set({ enabled: e.target.checked }, notifyTab);
$("siteOn").onchange = (e) => {
  chrome.storage.local.get({ disabledSites: [] }, ({ disabledSites }) => {
    const set = new Set(disabledSites);
    e.target.checked ? set.delete(host) : set.add(host);
    chrome.storage.local.set({ disabledSites: [...set] }, notifyTab);
  });
};
$("clear").onclick = () => {
  if (!confirm("Xoá toàn bộ dữ liệu EduShield trên máy này (kể cả số người thân, lựa chọn gửi về trường)?")) return;
  chrome.storage.local.clear(() => location.reload());
};

// ---------- Người hỗ trợ khẩn cấp: số điện thoại CHỈ lưu trên máy ----------
const maskPhone = (p) => p.length > 6 ? p.slice(0, 3) + "•••" + p.slice(-3) : p;
function renderContacts() {
  chrome.storage.local.get({ contacts: [] }, ({ contacts }) => {
    $("ctList").innerHTML = contacts.length ? "" : '<small>Chưa có ai. Thêm cha mẹ, người thân hoặc thầy cô để báo nhanh khi gặp chuyện.</small>';
    contacts.forEach((c, i) => {
      const row = document.createElement("div"); row.className = "ct";
      row.innerHTML = `<b>${escH(c.name)} <small>${escH(maskPhone(c.phone))}</small></b>`;
      for (const [lb, act] of [["📞", "call"], ["💬", "sms"], ["Zalo", "zalo"]]) {
        const b = document.createElement("button"); b.className = "btn"; b.style.cssText = "color:#1f2328;padding:4px 8px;font-size:12px"; b.textContent = lb; b.title = { call: "Gọi", sms: "Nhắn tin", zalo: "Mở Zalo" }[act];
        b.onclick = () => chrome.runtime.sendMessage({ type: "contactAction", i, action: act, cat: "" });
        row.appendChild(b);
      }
      const del = document.createElement("button"); del.textContent = "✕"; del.title = "Xoá";
      del.onclick = () => { contacts.splice(i, 1); chrome.storage.local.set({ contacts }, renderContacts); };
      row.appendChild(del);
      $("ctList").appendChild(row);
    });
    $("ctAddBtn").classList.toggle("hide", contacts.length >= 3);
  });
}
$("ctAddBtn").onclick = () => { $("ctForm").classList.remove("hide"); $("ctName").focus(); };
$("ctCancel").onclick = () => $("ctForm").classList.add("hide");
$("ctSave").onclick = () => {
  const name = $("ctName").value.trim(), phone = $("ctPhone").value.replace(/[^\d+]/g, "");
  if (!name || !/^(\+?84|0)\d{8,10}$/.test(phone)) { msg("Nhập tên gọi và số điện thoại Việt Nam hợp lệ (vd 0912345678).", true); return; }
  chrome.storage.local.get({ contacts: [] }, ({ contacts }) => {
    contacts.push({ name: name.slice(0, 30), phone }); chrome.storage.local.set({ contacts: contacts.slice(0, 3) }, () => {
      $("ctName").value = ""; $("ctPhone").value = ""; $("ctForm").classList.add("hide"); msg(""); renderContacts();
    });
  });
};
$("sosTop").onclick = () => {
  $("sosCard").scrollIntoView({ behavior: "smooth", block: "start" });
  $("sosCard").style.boxShadow = "0 0 0 3px rgba(209,36,47,.45)"; setTimeout(() => ($("sosCard").style.boxShadow = ""), 1600);
  chrome.storage.local.get({ contacts: [] }, ({ contacts }) => { if (!contacts.length) $("ctAddBtn").click(); });
};
renderContacts();

// ---------- Chẩn đoán kết nối máy chủ ----------
const DEPLOY_CFG = globalThis.EDUSHIELD_DEPLOY || { school: "", server: "http://127.0.0.1:8765" };
const serverOrigin = () => { try { return new URL(DEPLOY_CFG.server).origin; } catch (e) { return ""; } };
const isLocal = () => /^http:\/\/(127\.0\.0\.1|localhost):8765$/.test(serverOrigin());
async function hasPermission() {
  const o = serverOrigin();
  if (!o || isLocal()) return true;
  try { return await chrome.permissions.contains({ origins: [o + "/*"] }); } catch (e) { return false; }
}
function explain(r, permitted) {
  if (r && r.ok) return "";
  if (!permitted) return "Tiện ích chưa được cấp quyền kết nối tới máy chủ của trường. Bấm “Cho phép kết nối”.";
  if (isLocal()) return "Tiện ích đang gửi tới máy chủ trên CHÍNH máy này (" + serverOrigin() + "). Nếu máy chủ chạy trên GitHub Codespaces, hãy nạp tiện ích từ gói EduShield_Extension.zip tạo bằng build_public.py --collect.";
  const k = r && r.kind;
  if (k === "private") return "Cổng 8765 của Codespace đang để Private. Tab PORTS → chuột phải 8765 → Port Visibility → Public.";
  if (k === "server_off") return "Codespace đang mở nhưng server.py không chạy. Trong Terminal của Codespace, chạy lại: bash chay_codespace.sh";
  if (k === "timeout" || k === "network") return "Không tới được máy chủ: Codespace đã dừng, mất mạng, hoặc link máy chủ đã đổi.";
  return "Máy chủ trả lỗi " + ((r && r.error) || "không rõ") + ".";
}
async function checkServer() {
  const permitted = await hasPermission();
  chrome.runtime.sendMessage({ type: "health" }, (r) => {
    const ok = r && r.ok;
    $("dot").style.background = ok ? "#1a7f37" : "#999";
    $("server").textContent = ok ? "Máy chủ của trường: đang kết nối" + (r.data.llm ? " · LLM bật" : "") : "Chưa kết nối được máy chủ";
    $("serverWhy").style.display = ok ? "none" : "block";
    $("serverUrl").textContent = DEPLOY_CFG.server || "(chưa đặt)";
    $("serverReason").textContent = explain(r, permitted);
    $("grantBtn").style.display = permitted ? "none" : "inline-block";
  });
}
checkServer();
$("grantBtn").onclick = async () => { const o = serverOrigin(); if (o) await chrome.permissions.request({ origins: [o + "/*"] }); checkServer(); };
$("recheckBtn").onclick = () => { $("serverReason").textContent = "Đang kiểm tra lại…"; checkServer(); };

// ---------- Gửi về nhà trường: Tắt / Ẩn danh / Có tên – lớp ----------
const msg = (t, err) => { const m = $("shareMsg"); m.style.display = t ? "block" : "none"; m.textContent = t || ""; m.className = "msg" + (err ? " err" : ""); };
const HINT = {
  tat: "Không gửi gì về trường.",
  an_danh: "Mỗi ngày một gói có/không đã trộn nhiễu; tự gửi khi có cảnh báo khẩn cấp. Không có tên, không có nội dung.",
  danh_tinh: "Khi có cảnh báo khẩn cấp, sau 10 giây (bạn có thể huỷ) EduShield báo thầy cô: tên, lớp, loại nguy cơ. Không gửi nội dung tin nhắn.",
};
let share = { enabled: false, parental: false, mode: "an_danh", name: "", lop: "" }, mode = "tat";
function paintMode(m) {
  mode = m;
  document.querySelectorAll("#modeSeg label").forEach((l) => l.classList.toggle("on", l.dataset.m === m));
  $("modeHint").textContent = HINT[m];
  $("idBox").classList.toggle("hide", m !== "danh_tinh");
  $("consentRow").classList.toggle("hide", m === "tat" || share.parental);
  $("schoolBtns").classList.remove("hide");
  $("shareNow").classList.toggle("hide", !share.enabled || m === "tat");
  $("sharePreview").classList.toggle("hide", !share.enabled || m === "tat");
}
function paintPill() {
  const on = share.enabled;
  $("pill").textContent = !on ? "Đang tắt" : share.mode === "danh_tinh" ? "Có tên – lớp" : "Ẩn danh";
  $("pill").className = "pill " + (on ? "on" : "off");
}
document.querySelectorAll("#modeSeg label").forEach((l) => (l.onclick = () => { paintMode(l.dataset.m); msg(""); }));
chrome.storage.local.get({ share }, (s) => {
  share = Object.assign(share, s.share);
  $("stName").value = share.name || ""; $("stCls").value = share.lop || "";
  paintMode(share.enabled ? share.mode || "an_danh" : "tat"); paintPill();
});
async function ensurePermission() {
  const o = serverOrigin();
  if (!o || isLocal()) return true;
  if (await hasPermission()) return true;
  return chrome.permissions.request({ origins: [o + "/*"] });
}
function describe(r) {
  if (!r || (!r.ok && r.error)) { checkServer(); return { t: "Đã lưu. Chưa gửi được: " + explain(r, true) + " Máy sẽ tự thử lại.", err: true }; }
  if (r.sent > 0) return { t: "Đã lưu và gửi gói ẩn danh ✓", err: false };
  if (r.todayDone) return { t: "Đã lưu ✓ Hôm nay đã gửi một gói (mỗi ngày chỉ một gói).", err: false };
  return { t: "Đã lưu ✓ Máy sẽ tự gửi khi có dữ liệu.", err: false };
}
$("shareSave").onclick = async () => {
  if (mode === "tat") {
    share = { ...share, enabled: false };
    chrome.runtime.sendMessage({ type: "shareSet", share }, () => { paintMode("tat"); paintPill(); msg("Đã tắt. Không còn gì được gửi về trường.", false); });
    return;
  }
  const nm = $("stName").value.replace(/\s+/g, " ").trim(), cls = $("stCls").value.replace(/\s+/g, " ").trim();
  if (mode === "danh_tinh" && (nm.length < 2 || !cls)) { msg("Nhập họ tên và lớp để thầy cô biết ai cần hỗ trợ.", true); return; }
  if (!share.parental && !$("parental").checked) { msg("Hãy tích ô xác nhận tự nguyện tham gia.", true); return; }
  if (!DEPLOY_CFG.school) { msg("Bản tiện ích này chưa được nhà trường cài mã trường nên chưa gửi được.", true); return; }
  if (!(await ensurePermission())) { msg("Chưa cấp quyền kết nối tới máy chủ của trường.", true); return; }
  share = { enabled: true, parental: true, mode, name: mode === "danh_tinh" ? nm : "", lop: mode === "danh_tinh" ? cls : "" };
  $("shareSave").disabled = true;
  chrome.runtime.sendMessage({ type: "shareSet", share }, (r) => {
    $("shareSave").disabled = false; paintMode(mode); paintPill();
    const d = describe(r); msg(d.t, d.err);
  });
};
$("shareNow").onclick = async () => {
  if (!(await ensurePermission())) { msg("Chưa cấp quyền kết nối tới máy chủ của trường.", true); return; }
  $("shareNow").disabled = true;
  chrome.runtime.sendMessage({ type: "shareNow" }, (r) => { $("shareNow").disabled = false; const d = describe(r); msg(d.t.replace("Đã lưu và ", "").replace("Đã lưu ✓ ", "").replace("Đã lưu. ", ""), d.err); });
};
$("sharePreview").onclick = () => {
  chrome.runtime.sendMessage({ type: "sharePreview" }, (r) => {
    const out = $("previewOut");
    out.style.display = out.style.display === "block" ? "none" : "block";
    out.textContent = "Gói ẩn danh sẽ gửi (đã trộn nhiễu, mỗi ô giữ đúng " + Math.round(r.p * 100) + "%):\n" + JSON.stringify(r.packet, null, 1) +
      (share.mode === "danh_tinh" ? "\n\nKhi có cảnh báo khẩn cấp, yêu cầu hỗ trợ gồm: tên, lớp, loại nguy cơ, mức độ. Không có nội dung tin nhắn." : "");
  });
};

// ---------- Cảnh báo gần đây (chỉ mức độ, loại, ngày) ----------
const LV_IC = { khan_cap: "🚨", canh_bao: "⚠️", luu_y: "💡" }, LV_VI = { khan_cap: "Khẩn cấp", canh_bao: "Cảnh báo", luu_y: "Cần lưu ý" };
function renderAlerts() {
  chrome.storage.local.get({ recentAlerts: [], unseenAlerts: 0 }, (s) => {
    const pill = $("alNew"); pill.textContent = s.unseenAlerts + " mới"; pill.className = "pill " + (s.unseenAlerts ? "new" : "off");
    $("alList").innerHTML = s.recentAlerts.length ? s.recentAlerts.map((a) => `<div class="al"><span class="lvb">${LV_IC[a.lv] || "🔔"}</span><div><b>${escH(a.lb)}</b><small>${escH(LV_VI[a.lv] || "")} · ${escH(a.d)}</small></div></div>`).join("")
      : "<small>✅ Chưa có cảnh báo nào.</small>";
    if (s.unseenAlerts) chrome.storage.local.set({ unseenAlerts: 0 });
  });
}
$("alClear").onclick = () => chrome.storage.local.set({ recentAlerts: [], unseenAlerts: 0 }, renderAlerts);
renderAlerts();

// ---------- Trạng thái quét trên trang đang mở ----------
function pageBtn(label, fn, primary) {
  const b = document.createElement("button"); b.className = "btn" + (primary ? " primary" : ""); b.textContent = label; b.onclick = fn; $("pageBtns").appendChild(b);
}
const testPage = () => chrome.tabs.create({ url: chrome.runtime.getURL("thu-nghiem.html") });
function pageState(text, pill, cls) { $("pageState").innerHTML = text; $("pagePill").textContent = pill; $("pagePill").className = "pill " + cls; }
function checkPage() {
  $("pageBtns").innerHTML = "";
  chrome.tabs.query({ active: true, currentWindow: true }, ([tab]) => {
    const url = (tab && tab.url) || "";
    const isTest = url.startsWith(chrome.runtime.getURL("thu-nghiem.html"));
    if (!isTest && !/^https?:\/\//.test(url)) {
      pageState("Trang này không phải trang web nên EduShield không quét.", "Không hỗ trợ", "off");
      pageBtn("🧪 Trang thử nghiệm", testPage, true);
      return;
    }
    if (!isTest && globalThis.EDUSHIELD_SENSITIVE && EDUSHIELD_SENSITIVE.test(host)) {
      pageState("Trang nhạy cảm (ngân hàng, ví, email, dịch vụ công): EduShield <b class=\"rd\">không quét</b> để tôn trọng riêng tư.", "Bỏ qua", "off");
      return;
    }
    chrome.tabs.sendMessage(tab.id, { type: "ping" }, (r) => {
      if (chrome.runtime.lastError || !r || !r.ok) {
        pageState("EduShield <b class=\"rd\">chưa chạy</b> trên trang này.", "Chưa chạy", "new");
        pageBtn("⚡ Chạy ngay", () => chrome.runtime.sendMessage({ type: "inject", tabId: tab.id }, () => setTimeout(checkPage, 600)), true);
        pageBtn("🔄 Tải lại trang", () => { chrome.tabs.reload(tab.id); window.close(); });
        return;
      }
      if (!r.consented) {
        pageState("Bạn <b class=\"rd\">chưa hoàn tất bước đồng ý</b>.", "Chưa bật", "new");
        pageBtn("▶️ Bắt đầu dùng", () => chrome.tabs.create({ url: chrome.runtime.getURL("onboarding.html") }), true);
      } else if (!r.enabled) pageState("Bảo vệ đang tắt.", "Đang tắt", "off");
      else if (r.siteOff) pageState("Đã tắt trên trang này.", "Đang tắt", "off");
      else pageState(`Đã quét <b>${r.scanned}</b> đoạn (<b>${r.media || 0}</b> ảnh/video) · <b>${r.warnings}</b> cảnh báo`, "Đang quét", "on");
    });
  });
}
checkPage();
chrome.storage.onChanged.addListener((ch) => { if (ch.consented || ch.enabled || ch.disabledSites) setTimeout(checkPage, 300); });

// ---------- v1.8: Thực chiến giả lập ----------
(async function drillCard() {
  const D = globalThis.EduShieldDrill; if (!D) return;
  const st = await D.load(), d = D.dii(st);
  const el = document.getElementById("drillState");
  if (el) el.textContent = `Chỉ số miễn dịch số: ${d.value}/100 · ${d.level}` + (st.enabled ? " · đang bật" : "");
  const b = document.getElementById("drillBtn");
  if (b) b.onclick = () => (FULL ? (location.href = "drill.html") : chrome.tabs.create({ url: chrome.runtime.getURL("drill.html") }));
})();

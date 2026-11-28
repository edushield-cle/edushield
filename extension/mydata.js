const $ = (i) => document.getElementById(i);
function show() {
  chrome.storage.local.get(null, (s) => {
    $("st").textContent = `Đồng ý: ${s.consented ? "có" : "chưa"} · Đang bật: ${s.enabled === false ? "không" : "có"} · Độ nhạy: ${s.sens || "cân bằng"} · Số tin đã bỏ qua (mã băm): ${(s.suppressed || []).length} · Tên miền trong danh sách cảnh báo (mã băm): ${(s.blocklist || []).length}`;
    const dl = {};
    for (const [d, v] of Object.entries(s.daily || {})) { dl[d] = {}; for (const [c, a] of Object.entries(v.ev || {})) if (a.length) dl[d][c] = a.length; }
    $("daily").textContent = Object.keys(dl).length ? JSON.stringify(dl, null, 1) : "(trống)";
    const sh = s.share || {};
    $("share").textContent = sh.enabled ? `Đang bật: máy tự gửi một gói ẩn danh mỗi ngày cho trường. Đã gửi ${(s.sentDays || []).length} ngày gần đây (mỗi ngày tối đa một gói đã trộn nhiễu).` : "Đang tắt. Không có gì được gửi.";
  });
}
$("delDaily").onclick = () => chrome.storage.local.set({ daily: {} }, show);
$("stopShare").onclick = () => chrome.storage.local.get({ share: {} }, ({ share }) => chrome.storage.local.set({ share: { ...share, enabled: false } }, show));
$("wipe").onclick = () => { if (confirm("Xoá toàn bộ dữ liệu EduShield và rút lại đồng ý?")) chrome.storage.local.clear(show); };
show();

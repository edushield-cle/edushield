// Xuất mô hình + nội dung giao diện cho ứng dụng gốc Android/iOS từ ĐÚNG bộ phát hiện của tiện ích.
// Chạy: node native/tools/export_native.js
const fs = require("fs"), path = require("path"), vm = require("vm");
const ROOT = path.join(__dirname, "..", "..");
const ext = path.join(ROOT, "extension");
const ctx = { console }; ctx.globalThis = ctx; vm.createContext(ctx);
for (const f of ["model.js", "blocklist.js", "detector.js"]) vm.runInContext(fs.readFileSync(path.join(ext, f), "utf8"), ctx);
const M = ctx.EDUSHIELD_MODEL, D = ctx.EduShieldDetector;
const ui = { VI: D.VI, CAT_VI: D.CAT_VI, TODO: D.TODO, TODO_CAT: D.TODO_CAT, HELP_MSG: D.HELP_MSG,
  SENS: { it: 0.15, can_bang: 0, nhay: -0.15 } };
const mkdir = (p) => fs.mkdirSync(p, { recursive: true });
// Android: tài sản (assets) đọc bằng lõi Java
const aAssets = path.join(ROOT, "native", "android", "app", "src", "main", "assets");
mkdir(aAssets);
const lean = Object.assign({}, M); delete lean.eval; delete lean.categories;
fs.writeFileSync(path.join(aAssets, "model.json"), JSON.stringify(lean));
fs.writeFileSync(path.join(aAssets, "ui.json"), JSON.stringify(ui));
fs.writeFileSync(path.join(aAssets, "blocklist.json"), JSON.stringify({ hashes: ctx.EDUSHIELD_BLOCKLIST, allow: ctx.EDUSHIELD_ALLOWLIST }));
// iOS: chạy NGUYÊN VĂN model.js + detector.js bằng JavaScriptCore
const iShared = path.join(ROOT, "native", "ios", "Shared", "js");
mkdir(iShared);
for (const f of ["model.js", "blocklist.js", "detector.js"]) fs.copyFileSync(path.join(ext, f), path.join(iShared, f));
// Diễn tập (dùng chung cho tiện ích, app web, Android WebView, iOS WKWebView)
for (const dir of [path.join(aAssets, "drill"), path.join(ROOT, "native", "ios", "Shared", "drill")]) {
  mkdir(dir);
  for (const f of ["drill.html", "drill.js", "drill.css", "drill-page.js"]) {
    const src = path.join(ROOT, "mobile", f);
    if (fs.existsSync(src)) fs.copyFileSync(src, path.join(dir, f));
  }
}
// Kết quả mong đợi để kiểm tra lõi Java cho ra GIỐNG HỆT bản JavaScript
const samples = JSON.parse(fs.readFileSync(path.join(ROOT, "tests", "extension_samples.json"), "utf8"));
const extra = ["Cô chủ nhiệm đây, em chuyển gấp 500k tiền học phí vào stk 190355667788 nhé", "CẢNH BÁO: tài khoản của bạn bị khoá, xác minh tại https://bank-xacminh.top ngay",
  "Công an khuyến cáo: tuyệt đối không cung cấp mã OTP cho người lạ, hãy báo bố mẹ.", "mày mà mách cô thì đừng trách tao, tan học tao chờ ở cổng",
  "Tin “bạn trúng iPhone, bấm link nhận quà https://qua-tang.xyz” là lừa đảo, đừng bấm nhé"];
const exp = [...samples.map((s) => s.text), ...extra].map((t) => {
  const r = D.analyze(t, {});
  return { text: t, norm: D.norm(t), probs: M.classes.map((c) => r.probs[c]), label: r.label, warn: r.warn, level: r.level, frame: r.frame, cat: r.cat || "" };
});
fs.writeFileSync(path.join(ROOT, "native", "tools", "core_expected.json"), JSON.stringify(exp));
console.log("Đã xuất model.json, ui.json cho Android; model.js/detector.js cho iOS;", exp.length, "mẫu kiểm tra");

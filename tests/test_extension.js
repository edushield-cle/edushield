// Kiểm tra bản JavaScript cho kết quả giống bản Python.  Chạy: node tests/test_extension.js
const fs = require("fs"), path = require("path"), vm = require("vm");
const ext = path.join(__dirname, "..", "extension");
const ctx = { console }; ctx.globalThis = ctx; vm.createContext(ctx);
for (const f of ["model.js", "blocklist.js", "detector.js"]) vm.runInContext(fs.readFileSync(path.join(ext, f), "utf8"), ctx);
const D = ctx.EduShieldDetector, M = ctx.EDUSHIELD_MODEL;
const samples = JSON.parse(fs.readFileSync(path.join(__dirname, "extension_samples.json"), "utf8"));
let normBad = 0, maxDiff = 0;
for (const s of samples) {
  if (D.norm(s.text) !== s.norm) { normBad++; if (normBad < 4) console.log("Lệch chuẩn hoá:", JSON.stringify(s.text), "|", D.norm(s.text), "|", s.norm); }
  const r = D.analyze(s.text);
  M.classes.forEach((c, i) => { maxDiff = Math.max(maxDiff, Math.abs(r.probs[c] - s.probs[i])); });
}
console.log(`So khớp ${samples.length} mẫu: lệch chuẩn hoá ${normBad}, sai lệch xác suất lớn nhất ${maxDiff.toFixed(4)}`);
const cases = [
  "Tuyển CTV chốt đơn tại nhà 500k/ngày không cần cọc, ib zalo 0912345678",
  "mày mà mách cô thì đừng trách tao, tan học tao chờ ở cổng",
  "haha thằng quỷ này lại quên trả sách cho tao hả",
  "tối nay call nhóm làm thuyết trình văn lúc 8h nhé",
  "Cô chủ nhiệm đây, em chuyển gấp 500k tiền học phí vào stk 190355667788 nhé",
];
for (const c of cases) { const r = D.analyze(c); console.log(r.warn ? "CẢNH BÁO" : "bỏ qua  ", r.level.padEnd(9), r.label.padEnd(12), r.p, "|", c); }
console.log("Che PII:", JSON.stringify(D.mask("gọi 0912 345 678, stk 190355667788, vào https://www.abc.xyz/a")));
if (normBad || maxDiff > 0.002) { console.log("THẤT BẠI"); process.exit(1); } else console.log("OK");

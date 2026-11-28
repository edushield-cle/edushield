// TN11: Lời nhắc trước khi gửi (v1.9) trên tập KIỂM TRA (câu sinh từ khuôn mô hình chưa thấy)
// Đo: tỉ lệ tin có hại được nhắc; tỉ lệ tin bình thường bị nhắc nhầm, tách riêng tin đùa giỡn bạn bè.
const fs = require("fs"), path = require("path");
global.window = global; global.self = global;
require(path.join(__dirname, "../extension/model.js")); require(path.join(__dirname, "../extension/detector.js"));
const D = global.EduShieldDetector;
function csv(f) { const s = fs.readFileSync(f, "utf8").replace(/^﻿/, ""); const rows = []; let row = [], cur = "", q = false;
  for (let i = 0; i < s.length; i++) { const c = s[i];
    if (q) { if (c === '"') { if (s[i + 1] === '"') { cur += '"'; i++; } else q = false; } else cur += c; }
    else if (c === '"') q = true; else if (c === ",") { row.push(cur); cur = ""; } else if (c === "\n") { row.push(cur.replace(/\r$/, "")); rows.push(row); row = []; cur = ""; } else cur += c; }
  if (cur || row.length) { row.push(cur); rows.push(row); }
  const h = rows.shift(); return rows.filter(r => r.length === h.length).map(r => Object.fromEntries(h.map((k, i) => [k, r[i]]))); }
const rows = csv(path.join(__dirname, "../data/bo_huan_luyen_10000.csv")).filter(r => r.split === "test" && r.co_link === "0");
const g = {};
const add = (k, hit) => { g[k] = g[k] || [0, 0]; g[k][0]++; if (hit) g[k][1]++; };
for (const r of rows) {
  const o = D.outgoing(r.text, { sens: "can_bang" });
  add(r.label, o.nudge);
  if (r.label === "binh_thuong") add("bt:" + r.category, o.nudge);
}
const pct = (a) => (100 * a[1] / a[0]).toFixed(1);
const out = ["nhom,so_tin,bi_nhac,ti_le_phan_tram"];
// Tập viết tay độc lập (câu do nhóm tự viết, không sinh từ khuôn)
for (const r of csv(path.join(__dirname, "../data/kiem_tra_viet_tay.csv"))) add("viet_tay:" + r.label, D.outgoing(r.text, { sens: "can_bang" }).nudge);
for (const k of Object.keys(g).sort()) if (g[k]) { out.push(`${k},${g[k][0]},${g[k][1]},${pct(g[k])}`); console.log(k.padEnd(22), g[k][0], "tin, bị nhắc", g[k][1], `(${pct(g[k])}%)`); }
fs.writeFileSync(path.join(__dirname, "../results/tn11_nhac_gui.csv"), out.join("\n") + "\n");

// TN10 (v1.8): MÔ PHỎNG chế độ Thực chiến giả lập trên 1.000 "học sinh ảo" (chưa thử trên học sinh thật).
// Câu hỏi: (1) lịch diễn tập THÍCH ỨNG (ưu tiên nhóm yếu) có giúp nâng kỹ năng yếu nhất nhanh hơn chọn NGẪU NHIÊN không?
//          (2) Chỉ số miễn dịch số có phản ánh đúng kỹ năng thật (tương quan) không?
// Chạy: node tests/sim_dien_tap.js  -> results/tn10_dien_tap.csv
const fs = require("fs"), path = require("path");
require(path.join(__dirname, "..", "mobile", "drill.js"));
const D = globalThis.EduShieldDrill, G = Object.keys(D.GROUPS), DAY = 864e5;
function mulberry(a) { return () => { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
function pearson(x, y) { const n = x.length, mx = x.reduce((a, b) => a + b) / n, my = y.reduce((a, b) => a + b) / n; let sxy = 0, sx = 0, sy = 0; for (let i = 0; i < n; i++) { sxy += (x[i] - mx) * (y[i] - my); sx += (x[i] - mx) ** 2; sy += (y[i] - my) ** 2; } return sxy / Math.sqrt(sx * sy); }
function learnerAnswer(sc, q, rng) {
  const best = sc.act.reduce((b, x, i) => (x[1] > sc.act[b][1] ? i : b), 0);
  let a = best;
  if (rng() > q) { const others = sc.act.map((_, i) => i).filter((i) => i !== best); a = others[Math.floor(rng() * others.length)]; }
  const picked = sc.sig.map((s) => (s[1] ? rng() < q : rng() < (1 - q) * 0.3));
  return { a, picked, ok: sc.act[a][1] >= 90 };
}
function run(strategy, seed, N) {
  const rng = mulberry(seed);
  const a0 = 0.1 + 0.7 * rng(), q = {}; // năng lực chung của học sinh ảo + chênh lệch theo từng nhóm kỹ năng
  G.forEach((g) => (q[g] = Math.min(0.95, Math.max(0.05, a0 + 0.3 * (rng() - 0.5)))));
  let st = D.blank(); st.enabled = true; let now = Date.UTC(2026, 8, 1);
  const snap = {};
  for (let k = 1; k <= N; k++) {
    if (strategy !== "khong_dien_tap") {
      const sc = strategy === "thich_ung" ? D.pick(st, rng, now) : D.SCENARIOS[Math.floor(rng() * D.SCENARIOS.length)];
      const ans = learnerAnswer(sc, q[sc.g], rng);
      const r = D.score(sc, ans.a, ans.picked, 20000);
      D.update(st, sc, r, now);
      q[sc.g] += (ans.ok ? 0.08 : 0.25) * (1 - q[sc.g]); // học từ phản hồi sau mỗi lần diễn tập (sai thì học được nhiều hơn)
    }
    const gap = 3.5 * DAY; now += gap;
    G.forEach((g) => (q[g] = 0.3 + (q[g] - 0.3) * Math.pow(0.5, 3.5 / 120))); // quên dần
    if ([5, 10, 20, 30].includes(k)) {
      const vals = G.map((g) => q[g]);
      const dd = D.dii(st, now);
      snap[k] = { mean: vals.reduce((a, b) => a + b) / vals.length, min: Math.min(...vals), share: vals.filter((v) => v >= 0.7).length / vals.length, dii: dd.value,
        pairs: G.filter((g) => dd.by[g].n > 0).map((g) => [dd.by[g].m, 100 * q[g]]) };
    }
  }
  return snap;
}
const rows = [["chien_luoc", "so_lan_dien_tap", "ky_nang_TB", "ky_nang_nhom_yeu_nhat", "ti_le_nhom_dat_0_7", "tuong_quan_chi_so_voi_ky_nang", "tuong_quan_theo_nhom"]];
const out = {};
for (const s of ["khong_dien_tap", "ngau_nhien", "thich_ung"]) {
  const runs = []; for (let i = 0; i < 1000; i++) runs.push(run(s, 1000 + i, 30));
  for (const k of [5, 10, 20, 30]) {
    const m = (f) => runs.reduce((a, r) => a + f(r[k]), 0) / runs.length;
    const corr = s === "khong_dien_tap" ? NaN : pearson(runs.map((r) => r[k].dii), runs.map((r) => r[k].mean * 100));
    const pr = runs.flatMap((r) => r[k].pairs);
    const corrG = pr.length ? pearson(pr.map((p) => p[0]), pr.map((p) => p[1])) : NaN;
    const row = [s, k, (100 * m((x) => x.mean)).toFixed(1), (100 * m((x) => x.min)).toFixed(1), (100 * m((x) => x.share)).toFixed(1), corr.toFixed(3), corrG.toFixed(3)];
    rows.push(row); out[s + k] = row;
  }
}
fs.mkdirSync(path.join(__dirname, "..", "results"), { recursive: true });
fs.writeFileSync(path.join(__dirname, "..", "results", "tn10_dien_tap.csv"), "﻿" + rows.map((r) => r.join(",")).join("\n"));
console.log(rows.map((r) => r.join("\t")).join("\n"));

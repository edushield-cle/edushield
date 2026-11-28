"""Mô phỏng 750 học sinh trong 4 tuần để (1) có dữ liệu demo cho trang /truong và
(2) ĐO độ chính xác của thống kê ẩn danh theo từng mức riêng tư ε.

Chạy:  python simulate_school.py
Kết quả: results/tn6_rieng_tu.csv và dữ liệu demo trường "THPT_DEMO" (toàn trường, không chia khối) trong data/thongke.json.
       Đổi tên trường:  python simulate_school.py --school TEN_TRUONG
       Nếu trường đó đã có số liệu THẬT, chương trình dừng lại để không ghi đè (thêm --ghi-de nếu chắc chắn).
Toàn bộ là dữ liệu MÔ PHỎNG có đáp án, dùng để kiểm chứng phương pháp.
"""
import os
import random
import sys
from collections import defaultdict
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "src"))

import pandas as pd

from privacy_stats import ALLOWED_EPS, CAT_CODES, CAT_INFO, EPSILON, Aggregator, randomize, validate_packet

N_PER_GRADE, PARTICIPATION, ACTIVE, DAYS = 250, 0.7, 0.8, 28
BASE = {"ld_otp": .01, "ld_chuyen_tien": .02, "ld_trung_thuong": .03, "ld_viec_lam": .02, "ld_de_doa": .01,
        "ld_thong_tin": .01, "ld_the_cao": .005, "ld_khac": .01, "link_nguy_hiem": .015,
        "bn_de_doa": .01, "bn_phat_tan": .005, "bn_tran_lot": .003, "bn_lang_ma": .04, "bn_co_lap": .015,
        "bn_tin_don": .01, "bn_khac": .01, "hv_nhac_gui": .02, "hv_bao_luc": .015}


def true_rate(cat, grade, week):
    r = BASE[cat]
    if cat == "ld_viec_lam" and week == 2:   # tuần 3: một chiến dịch "tuyển CTV" bùng phát
        r = 0.08
    if cat == "bn_co_lap" and week == 3:     # tuần 4: tẩy chay trong nhóm lớp tăng
        r = 0.045
    if cat == "bn_lang_ma" and grade == "10":  # khối 10 bị lăng mạ nhiều hơn
        r *= 1.5
    return r


def simulate(eps, seed=0, end=None):
    rng = random.Random(seed)
    if end is None:  # kết thúc vào Chủ nhật gần nhất để có đúng 4 tuần lịch trọn vẹn
        t = date.today()
        end = t - timedelta(days=t.weekday() + 1)
    start = end - timedelta(days=DAYS - 1)
    students = [(g, i) for g in ("10", "11", "12") for i in range(N_PER_GRADE) if rng.random() < PARTICIPATION]
    agg = Aggregator()
    truth = defaultdict(lambda: defaultdict(int))  # (tuần) -> mã -> số lượt thật
    tn = defaultdict(int)
    for k in range(DAYS):
        day = start + timedelta(days=k)
        week = k // 7
        wk = (day - timedelta(days=day.weekday())).isoformat()
        for g, _ in students:
            if rng.random() > ACTIVE:
                continue
            bits = {c: int(rng.random() < true_rate(c, g, week)) for c in BASE}
            bits["lua_dao_bat_ky"] = int(any(bits[c] for c in BASE if CAT_INFO[c]["group"] == "lua_dao"))
            bits["bat_nat_bat_ky"] = int(any(bits[c] for c in BASE if CAT_INFO[c]["group"] == "bat_nat"))
            tn[wk] += 1
            for c in CAT_CODES:
                truth[wk][c] += bits[c]
            pk = {"school": "THPT_DEMO", "grade": g, "day": day.isoformat(), "eps": eps, "bits": randomize(bits, eps, rng)}
            agg.add(validate_packet(pk, today=day + timedelta(days=1)), save=False)
    return agg, truth, tn


def evaluate():
    rows = []
    for eps in ALLOWED_EPS:
        for seed in range(5):
            agg, truth, tn = simulate(eps, seed)
            for r in agg.report("THPT_DEMO", "week"):
                if r["hidden"] or r["period"] not in tn:
                    continue
                for c in CAT_CODES:
                    t = truth[r["period"]][c] / tn[r["period"]]
                    e = r["cats"][c]
                    rows.append({"eps": eps, "seed": seed, "cat": c, "true": t, "est": e["pct"],
                                 "abs_err_pp": 100 * abs(e["pct"] - t), "covered": e["pct_lo"] <= t <= e["pct_hi"]})
    df = pd.DataFrame(rows)
    p = lambda eps: __import__("math").exp(eps) / (1 + __import__("math").exp(eps))
    summary = df.groupby("eps").agg(sai_so_tuyet_doi_TB_diem_pct=("abs_err_pp", "mean"),
                                    sai_so_lon_nhat_diem_pct=("abs_err_pp", "max"),
                                    ty_le_khoang_tin_cay_chua_gia_tri_that=("covered", "mean")).round(3)
    summary.insert(0, "xac_suat_giu_dung", [round(p(e), 3) for e in summary.index])
    # Phát hiện được đợt bùng phát "tuyển CTV" ở tuần 3 không?
    hits = 0
    for seed in range(5):
        agg, _, _ = simulate(EPSILON, seed)
        rep = [r for r in agg.report("THPT_DEMO", "week") if not r["hidden"]]
        top = max((c for c in CAT_CODES if not c.endswith("bat_ky")), key=lambda c: rep[2]["cats"][c]["est"]) if len(rep) > 2 else None
        hits += top == "ld_viec_lam"
    return summary, hits


if __name__ == "__main__":
    import argparse, json
    ap = argparse.ArgumentParser()
    ap.add_argument("--school", default="THPT_DEMO")
    ap.add_argument("--ghi-de", action="store_true", help="cho phép ghi đè trường đã có số liệu thật")
    a = ap.parse_args()
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    print(f"Mô phỏng {3 * N_PER_GRADE} học sinh, {int(PARTICIPATION*100)}% tham gia, {DAYS} ngày, 5 lần lặp mỗi mức ε...")
    summary, hits = evaluate()
    print(summary.to_string())
    print(f"\nε = {EPSILON}: đợt bùng phát 'tuyển CTV' ở tuần 3 được xếp hạng nhất trong {hits}/5 lần mô phỏng")
    summary.to_csv(os.path.join(ROOT, "results", "tn6_rieng_tu.csv"))
    # Ghi dữ liệu demo (ε mặc định) cho trang /truong: gộp thành số liệu TOÀN TRƯỜNG (khối để trống, giống gói thật)
    path = os.path.join(ROOT, "data", "thongke.json")
    mark = os.path.join(ROOT, "data", "truong_mo_phong.json")  # danh sách trường chỉ chứa dữ liệu mô phỏng
    demo_schools = set(json.load(open(mark, encoding="utf-8"))) if os.path.exists(mark) else set()
    store = Aggregator(path)
    has_real = any(k.startswith(a.school + "|") for k in store.cells) and a.school not in demo_schools
    if has_real and not a.ghi_de:
        raise SystemExit(f"Trường {a.school} đã có số liệu thật trong {path}. Không ghi đè. Dùng --school TEN_KHAC hoặc thêm --ghi-de.")
    for k in [k for k in store.cells if k.startswith(a.school + "|") or k.startswith("THPT_DEMO|")]:
        del store.cells[k]
    demo, _, _ = simulate(EPSILON, seed=0)
    for key, cell in demo.cells.items():
        _, _, day, eps = key.split("|")
        dst = store.cells[f"{a.school}||{day}|{eps}"]
        dst["n"] += cell["n"]
        for c in CAT_CODES:
            dst["s"][c] += cell["s"][c]
    store.save()
    demo_schools = demo_schools | {a.school}
    json.dump(sorted(demo_schools), open(mark, "w", encoding="utf-8"))
    print(f"\nĐã ghi dữ liệu MÔ PHỎNG toàn trường cho {a.school} vào {path}")
    print(f"Chạy  python server.py  rồi mở  http://127.0.0.1:8765/truong?school={a.school}")

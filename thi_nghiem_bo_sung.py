"""THÍ NGHIỆM 8 (v1.6): bổ sung dữ liệu từ thủ đoạn do cơ quan chức năng công bố có giúp mô hình chính xác hơn không?

- Mô hình A: chỉ học bộ 10.000 tin cũ (như bản 1.5).
- Mô hình B: học bộ cũ + phần huấn luyện của bộ bổ sung (2.640 tin, 88 lõi câu, 7 nguồn).
Cả hai chọn ngưỡng trên tập kiểm định của dữ liệu mình được học, rồi đo trên:
  (1) tập kiểm tra cũ (1.556 tin) và (2) TẬP KIỂM TRA ĐỘC LẬP của bộ bổ sung (810 tin, lõi câu chưa từng thấy).
Chạy:  python thi_nghiem_bo_sung.py   -> results/tn8_bo_sung.csv
"""
import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import export_extension as E  # noqa: E402


def load_supp():
    with open(os.path.join(ROOT, "data", "bo_bo_sung_nguon_tin_cay.csv"), encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return {sp: [r for r in rows if r["split"] == sp] for sp in ("train", "val", "doc_lap")}


def fit(train_rows, val_rows):
    vec, coef, b = E.train(train_rows)
    w = E.prune(vec, coef)
    saved = dict(E.RULE)
    E.RULE.clear(); E.RULE.update({"p_warn": 0.6, "p_warn_with_signal": 0.4, "sev_signal": 3})
    tuned = E.tune_rule(val_rows, w, b)
    if tuned and tuned[1]["p_warn"] >= 0.6:
        E.RULE.update(tuned[1])
    rule = dict(E.RULE)
    E.RULE.clear(); E.RULE.update(saved)
    return w, b, rule


def main():
    old, new = E.load10k(), load_supp()
    out = []
    for name, tr, va in (("A. Chỉ bộ 10.000 tin cũ", old["train"], old["val"]),
                         ("B. Bộ cũ + bộ bổ sung từ nguồn tin cậy", old["train"] + new["train"], old["val"] + new["val"])):
        w, b, rule = fit(tr, va)
        for test_name, te in (("Tập kiểm tra cũ", old["test"]), ("Tập kiểm tra độc lập (bổ sung)", new["doc_lap"])):
            m = E.metrics(te, w, b, rule)
            out.append({"mo_hinh": name, "tap_do": test_name, "so_tin": len(te), **m, "nguong": json.dumps(rule)})
            print(name, "|", test_name, len(te), m)
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    with open(os.path.join(ROOT, "results", "tn8_bo_sung.csv"), "w", encoding="utf-8-sig", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(out[0]))
        wr.writeheader(); wr.writerows(out)
    print("Đã ghi results/tn8_bo_sung.csv")


if __name__ == "__main__":
    main()

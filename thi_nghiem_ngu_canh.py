"""TN9 (v1.7): Phân biệt TUYÊN TRUYỀN với ĐANG GẶP NGUY CƠ.

So sánh 4 cấu hình, CÙNG cách chọn ngưỡng trên tập kiểm định (không nhìn tập kiểm tra):
  A. Mô hình v1.6: 3 nhãn, chỉ từ + cặp từ, dữ liệu cũ (10.000 tin + bộ bổ sung)
  B. Thêm bộ phân biệt ngữ cảnh nhưng vẫn 3 nhãn (tuyên truyền gộp vào bình thường)
  C. 4 nhãn: thêm nhãn riêng "tuyên truyền"
  D. 4 nhãn + đặc trưng khung ngữ cảnh (cảnh báo, ngôi thứ ba, phủ định, trích dẫn, kể lại, xưng danh...)
Đo trên: tập kiểm tra cũ, tập độc lập bổ sung (v1.6), tập độc lập ngữ cảnh, và TẬP VIẾT TAY (208 câu học sinh tự viết,
không sinh từ khuôn câu, đã kiểm tra không trùng với dữ liệu huấn luyện).
Chạy: python thi_nghiem_ngu_canh.py  -> results/tn9_ngu_canh.csv
"""
import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import export_extension as X  # noqa: E402

CFG = {
    "A. v1.6 (3 nhãn, dữ liệu cũ)": dict(classes=["binh_thuong", "bat_nat", "lua_dao"], frame=False, ctx=False, C=2.0),
    "B. + dữ liệu ngữ cảnh, 3 nhãn": dict(classes=["binh_thuong", "bat_nat", "lua_dao"], frame=False, ctx=True, C=2.0),
    "C. + nhãn tuyên truyền (4 nhãn)": dict(classes=["binh_thuong", "bat_nat", "lua_dao", "tuyen_truyen"], frame=False, ctx=True, C=2.0),
    "D. + đặc trưng khung ngữ cảnh": dict(classes=["binh_thuong", "bat_nat", "lua_dao", "tuyen_truyen"], frame=True, ctx=True, C=2.0),
}


def run(name, cfg):
    X.CLASSES[:] = cfg["classes"]
    X.USE_FRAME = cfg["frame"]
    X.C_REG = cfg["C"]
    X.RULE.update({"p_warn": 0.6, "p_warn_with_signal": 0.4})
    D, S, N = X.load10k(), X.load_supp(), X.load_ctx()
    tr = D["train"] + S["train"] + (N["train"] if cfg["ctx"] else [])
    va = D["val"] + S["val"] + (N["val"] if cfg["ctx"] else [])
    vec, coef, b = X.train(tr)
    w = X.prune(vec, coef)
    tuned = X.tune_rule(va, w, b)
    if tuned and tuned[1]["p_warn"] >= 0.6:
        X.RULE.update(tuned[1])
    out = {"cau_hinh": name, "nguong": dict(X.RULE), "kiem_dinh": X.metrics(va, w, b),
           "test_cu": X.metrics(D["test"], w, b), "doc_lap_v16": X.metrics(S["doc_lap"], w, b),
           "ngu_canh_doc_lap": X.metrics(N["doc_lap"], w, b), "viet_tay": X.vt_metrics(X.load_vt(), w, b)}
    vt = out["viet_tay"]
    out["viet_tay_tong"] = {
        "bao_nham_tuyen_truyen": vt["tuyen_truyen"]["ti_le_canh_bao"], "bao_nham_tin_thuong_kho": vt["thuong_kho"]["ti_le_canh_bao"],
        "bat_dung_truc_tiep": vt["truc_tiep"]["ti_le_canh_bao"], "bat_dung_gia_canh_bao": vt["gia_canh_bao"]["ti_le_canh_bao"]}
    return out


def main():
    res = [run(n, c) for n, c in CFG.items()]
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    rows = []
    for r in res:
        for k in ("kiem_dinh", "test_cu", "doc_lap_v16", "ngu_canh_doc_lap"):
            rows.append([r["cau_hinh"], k, r[k]["macro_f1"], r[k]["bao_nham"], r[k]["bat_dung"], ""])
        for g, v in r["viet_tay"].items():
            rows.append([r["cau_hinh"], "viet_tay_" + g, "", "", "", v["ti_le_canh_bao"]])
    with open(os.path.join(ROOT, "results", "tn9_ngu_canh.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cau_hinh", "tap_do", "macro_f1", "bao_nham", "bat_dung", "ti_le_canh_bao_viet_tay"])
        w.writerows(rows)
    for r in res:
        print(json.dumps({k: r[k] for k in ("cau_hinh", "nguong", "kiem_dinh", "test_cu", "doc_lap_v16", "ngu_canh_doc_lap", "viet_tay_tong")}, ensure_ascii=False))


if __name__ == "__main__":
    main()

"""Kiểm tra chất lượng và đánh giá trên bộ 10.000 mẫu tổng hợp. Chạy:  python eval_10k.py
Train trên split=train, chọn/đối chiếu trên val, BÁO CÁO trên test (mẫu câu chưa từng thấy)."""
import json, os, re, sys, warnings
warnings.filterwarnings("ignore")
ROOT = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(ROOT, "src"))
import numpy as np, pandas as pd
from sklearn.metrics import classification_report, confusion_matrix
from text_model import TextClassifier, LABELS, normalize
from pii import mask_pii

df = pd.read_csv(os.path.join(ROOT, "data", "bo_huan_luyen_10000.csv"))
print("== Kiểm tra chất lượng ==")
print("Tổng:", len(df), "| trùng văn bản:", df.text.duplicated().sum(), "| trùng sau chuẩn hoá:", df.text.map(normalize).duplicated().sum())
tr, va, te = (df[df.split == s] for s in ("train", "val", "test"))
print("Rò rỉ template giữa các tập:", len(set(tr.template_id) & set(te.template_id)) + len(set(tr.template_id) & set(va.template_id)) + len(set(va.template_id) & set(te.template_id)))
# văn bản gần như trùng giữa train và test sau chuẩn hoá
ntr = set(tr.text.map(normalize)); print("Văn bản test trùng văn bản train (sau chuẩn hoá):", int(te.text.map(normalize).isin(ntr).sum()))
# PII thật? số điện thoại/stk phải thuộc mẫu giả
bad = df.text.str.contains(r"(?<!\d)09(?!00000)\d{8}(?!\d)", regex=True).sum(); print("Số điện thoại KHÔNG thuộc dạng giả 0900000xxx:", int(bad))
print("Độ dài chữ (ký tự) trung vị / lớn nhất:", int(df.text.str.len().median()), int(df.text.str.len().max()))

def fit(rows): return TextClassifier().fit(rows.to_dict("records"))
m = fit(tr)
def pred(d):
    p = m.predict_proba(d.text.tolist()); return [max(x, key=x.get) for x in p], p
print("\n== Mô hình văn bản 3 nhãn (train -> test mẫu câu mới) ==")
for name, d in (("val", va), ("test", te)):
    y, _ = pred(d); r = classification_report(d.label, y, labels=LABELS, output_dict=True, zero_division=0)
    print(name, "macro-F1 %.3f" % r["macro avg"]["f1-score"], {k: round(r[k]["f1-score"], 3) for k in LABELS})
y, probs = pred(te)
cm = confusion_matrix(te.label, y, labels=LABELS); print("Ma trận nhầm lẫn (hàng=thật, cột=đoán):", LABELS); print(cm)
te = te.assign(pred=y, pmax=[max(p.values()) for p in probs])
print("\n== Theo loại chi tiết trên test (tỉ lệ đoán đúng nhãn 3 lớp) ==")
g = te.assign(ok=(te.label == te.pred)).groupby("category").ok.agg(["mean", "count"]).round(3).sort_values("mean"); print(g.to_string())
print("\n== Mẫu khó vs thường ==")
print(te.assign(ok=(te.label == te.pred)).groupby("do_kho").ok.agg(["mean", "count"]).round(3).to_string())
nm = te[te.label == "binh_thuong"]; print("Báo động giả (tin bình thường bị đoán là nguy cơ):", round(float((nm.pred != "binh_thuong").mean()), 3))
print("  - riêng nhóm đùa giỡn:", round(float((nm[nm.category == "bt_dua_gion"].pred != "binh_thuong").mean()), 3), "| cảnh báo đúng:", round(float((nm[nm.category == "bt_canh_bao_dung"].pred != "binh_thuong").mean()), 3), "| tài chính hợp lệ:", round(float((nm[nm.category == "bt_tai_chinh_hop_le"].pred != "binh_thuong").mean()), 3))

# 16 mã chi tiết do quy tắc: so với loại thật trên TEST
sys.path.insert(0, ROOT)
src = open(os.path.join(ROOT, "export_extension.py"), encoding="utf-8").read()
ns = {}; exec(compile(src[src.index("RX = {"):src.index("# Quy tắc ra cảnh báo")], "sig", "exec"), {"re": re}, ns)
RX, SIG = ns["RX"], ns["SIGNALS"]
import unicodedata
def nrm(t):
    t = t.replace("đ", "d").replace("Đ", "D"); t = "".join(c for c in unicodedata.normalize("NFD", t) if not ("̀" <= c <= "ͯ")).lower()
    t = re.sub(RX["url"], " urltoken ", t); t = re.sub(RX["phone"], " phonetoken ", t); t = re.sub(RX["num"], " numtoken ", t)
    return " ".join(re.sub(r"[^a-z0-9]+", " ", t).split())
def cats(text, label):
    n = nrm(text); out = set()
    for lab, pat, _d, _s, c in SIG:
        if lab == label and c and re.search(pat, n): out.add(c)
    if label == "lua_dao" and "urltoken" in n: out.add("link_nguy_hiem")
    return out
risk = te[te.label != "binh_thuong"]
rows = []
for c, d in risk.groupby("category"):
    hit = np.mean([c in cats(t, l) for t, l in zip(d.text, d.label)])
    rows.append((c, len(d), round(float(hit), 3)))
print("\n== 16 mã chi tiết bằng quy tắc: tỉ lệ mẫu test có đúng mã thật trong tập mã được gán ==")
print(pd.DataFrame(rows, columns=["loai_that", "so_mau", "ty_le_co_dung_ma"]).sort_values("ty_le_co_dung_ma").to_string(index=False))
print("(link_nguy_hiem ở đây chỉ tính khi có link; ld_khac/bn_khac không có quy tắc riêng)")

"""Kiểm tra rò rỉ: tập kiểm tra viết tay có câu nào quá giống câu dùng để huấn luyện / chọn ngưỡng không?
Độ giống = Jaccard trên tập cặp từ (đã bỏ dấu, viết thường). Ngưỡng 0,5: coi là gần trùng."""
import csv, os, re, sys, unicodedata
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def norm(t):
    t = t.replace("đ", "d").replace("Đ", "D")
    t = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", " ", t).split()

def bigr(t):
    w = norm(t)
    return {a + " " + b for a, b in zip(w, w[1:])}

def load(fn, splits):
    p = os.path.join(ROOT, "data", fn)
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8-sig") as f:
        return [r["text"] for r in csv.DictReader(f) if r["split"] in splits]

def main(thr=0.5):
    train = load("bo_huan_luyen_10000.csv", ("train", "val")) + load("bo_bo_sung_nguon_tin_cay.csv", ("train", "val")) \
        + load("bo_phan_biet_ngu_canh.csv", ("train", "val"))
    tb = [bigr(t) for t in train]
    inv = {}
    for i, s in enumerate(tb):
        for g in s:
            inv.setdefault(g, []).append(i)
    with open(os.path.join(ROOT, "data", "kiem_tra_viet_tay.csv"), encoding="utf-8-sig") as f:
        test = list(csv.DictReader(f))
    worst = []
    for r in test:
        b = bigr(r["text"])
        cand = {i for g in b for i in inv.get(g, [])}
        best, bi = 0.0, None
        for i in cand:
            j = len(b & tb[i]) / max(1, len(b | tb[i]))
            if j > best:
                best, bi = j, i
        worst.append((best, r["id"], r["text"], train[bi] if bi is not None else ""))
    worst.sort(reverse=True)
    n = sum(1 for w in worst if w[0] >= thr)
    print(f"{len(test)} câu kiểm tra, {len(train)} câu huấn luyện/kiểm định; số câu có độ giống >= {thr}: {n}")
    print("Độ giống lớn nhất trung bình: %.3f" % (sum(w[0] for w in worst) / len(worst)))
    for w in worst[:12]:
        print("%.2f %s | %s\n       ~ %s" % (w[0], w[1], w[2][:90], w[3][:90]))
    return worst

if __name__ == "__main__":
    main()

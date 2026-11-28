"""Thí nghiệm: nhận diện theo TỪ / CỤM TỪ của từng nhãn so với mô hình học từ câu.

Chạy:  python thi_nghiem_tu_khoa.py
Kết quả:
  - data/bo_tu_khoa.csv           bộ cụm từ theo nhãn (rút từ tập huấn luyện + cụm từ do học sinh tự soạn)
  - results/tn7_tu_khoa.csv       bảng so sánh 3 phương án trên tập kiểm tra (khuôn câu chưa từng thấy)

Ba phương án:
  A. Chỉ cụm từ: tin có cụm từ của nhãn nào thì gán nhãn đó (cộng điểm theo độ tin cậy của cụm từ)
  B. Mô hình hiện tại: hồi quy logistic trên từ và cặp từ, học từ câu
  C. Kết hợp: mô hình B + đặc trưng "có cụm từ của nhóm X"
Ngưỡng của từng phương án được chọn trên tập KIỂM ĐỊNH (val), không nhìn tập kiểm tra.
"""
import csv
import math
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict

import numpy as np
from sklearn.metrics import f1_score

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, ROOT)
import export_extension as E  # noqa: E402

CLASSES = E.CLASSES
MIN_SUPPORT, MIN_PREC = 6, 0.9
from tu_khoa import SEED  # noqa: E402  (bộ cụm từ do học sinh tự soạn)


SEED_NORM = set()


def label_of_cat(c):
    return "lua_dao" if c.startswith("ld_") or c == "link_nguy_hiem" else "bat_nat"


def ngrams(toks, nmax=3):
    out = set()
    for n in range(1, nmax + 1):
        for i in range(len(toks) - n + 1):
            out.add(" ".join(toks[i:i + n]))
    return out


def strip_char(c):
    if c in "đĐ":
        return "d"
    d = unicodedata.normalize("NFD", c)
    base = "".join(x for x in d if not ("̀" <= x <= "ͯ"))
    return base.lower() if base else ""


def surface(text, phrase):
    """Tìm dạng CÓ DẤU của cụm từ trong câu gốc để hiển thị cho học sinh."""
    chars = [(strip_char(c), i) for i, c in enumerate(text)]
    s = "".join(a for a, _ in chars)
    idx = [i for a, i in chars for _ in a]
    m = re.search(r"(?<![a-z0-9])" + r"[^a-z0-9]+".join(map(re.escape, phrase.split())) + r"(?![a-z0-9])", s)
    if not m:
        return None
    return text[idx[m.start()]: idx[m.end() - 1] + 1]


def build_lexicon(train):
    """Rút cụm từ 1-3 từ có độ chính xác cao cho từng nhãn nguy cơ từ tập huấn luyện."""
    cnt = defaultdict(Counter)   # cụm từ -> đếm theo nhãn
    cat = defaultdict(Counter)   # cụm từ -> đếm theo nhóm chi tiết
    ex = {}
    for r in train:
        toks = E.norm(r["text"]).split()
        for g in ngrams(toks):
            if any(t in ("numtoken", "phonetoken", "urltoken", "linkoktoken") for t in g.split()):
                continue
            cnt[g][r["label"]] += 1
            if r["label"] != "binh_thuong":
                cat[g][r["category"]] += 1
                ex.setdefault(g, r["text"])
    lex = {}
    for g, c in cnt.items():
        tot = sum(c.values())
        lab, k = c.most_common(1)[0]
        if lab == "binh_thuong" or tot < MIN_SUPPORT or k / tot < MIN_PREC:
            continue
        lex[g] = {"label": lab, "cat": cat[g].most_common(1)[0][0], "prec": k / tot, "n": tot, "src": "rut_tu_du_lieu", "ex": ex.get(g, "")}
    # bỏ cụm dài nếu cụm ngắn hơn bên trong đã đủ mạnh (giữ bộ từ gọn, dễ đọc)
    for g in sorted(lex, key=lambda x: -len(x.split())):
        parts = g.split()
        subs = [" ".join(parts[i:j]) for i in range(len(parts)) for j in range(i + 1, len(parts) + 1) if j - i < len(parts)]
        if any(s in lex and lex[s]["label"] == lex[g]["label"] and lex[s]["prec"] >= lex[g]["prec"] for s in subs):
            del lex[g]
    for c, phrases in SEED.items():
        for p in phrases:
            g = E.norm(p)
            c0 = cnt.get(g, Counter())
            tot = sum(c0.values())
            lab = label_of_cat(c)
            prec = (c0[lab] / tot) if tot else 0.0
            if g not in lex:
                lex[g] = {"label": lab, "cat": c, "prec": prec, "n": tot, "src": "hoc_sinh_soan", "ex": "", "show": p}
            else:
                lex[g]["show"] = p
    for g, v in lex.items():
        if "show" not in v:
            v["show"] = surface(v["ex"], g) or g
    return lex


def lex_hits(n, lex):
    s = " " + n + " "
    return [g for g in lex if " " + g + " " in s]


def score_keywords(n, lex):
    sc = {"bat_nat": 0.0, "lua_dao": 0.0}
    for g in lex_hits(n, lex):
        v = lex[g]
        if v["src"] == "hoc_sinh_soan" and v["n"] and v["prec"] < 0.6:
            continue  # cụm tự soạn nhưng dữ liệu cho thấy hay xuất hiện ở tin bình thường
        sc[v["label"]] += math.log(1 + 10 * max(v["prec"], 0.6))
    return sc


def eval_keywords(rows, lex, thr):
    pred, warn, true = [], [], []
    for r in rows:
        sc = score_keywords(E.norm(r["text"]), lex)
        lab = max(sc, key=sc.get)
        w = sc[lab] >= thr
        pred.append(lab if w else "binh_thuong"); warn.append(w); true.append(r["label"])
    return summarize(true, pred, warn)


def summarize(true, pred, warn):
    normal = [w for t, w in zip(true, warn) if t == "binh_thuong"]
    harm = [w for t, w in zip(true, warn) if t != "binh_thuong"]
    return {"macro_f1": round(float(f1_score(true, pred, labels=CLASSES, average="macro")), 3),
            "bao_nham": round(sum(normal) / len(normal), 3), "bat_dung": round(sum(harm) / len(harm), 3)}


def lex_feats_factory(lex):
    def f(text):
        base = E.feats(text)
        n = E.norm(text)
        extra = sorted({"lx_" + lex[g]["cat"] for g in lex_hits(n, lex)})
        return base + extra
    return f


def eval_model(rows, w, b, featf, rule):
    pred, warn, true = [], [], []
    old = dict(E.RULE); E.RULE.update(rule)
    for r in rows:
        z = np.array(b, dtype=float)
        for f in featf(r["text"]):
            if f in w:
                z += w[f]
        e = np.exp(z - z.max()); pr = e / e.sum()
        lab, wa = E.decide(pr, E.norm(r["text"]))
        pred.append(lab); warn.append(wa); true.append(r["label"])
    E.RULE.clear(); E.RULE.update(old)
    return summarize(true, pred, warn)


def train_with(featf, rows):
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.linear_model import LogisticRegression
    vec = CountVectorizer(analyzer=featf, binary=True, min_df=2)
    X = vec.fit_transform([r["text"] for r in rows])
    clf = LogisticRegression(max_iter=3000, C=2.0, class_weight="balanced").fit(X, [r["label"] for r in rows])
    order = [list(clf.classes_).index(c) for c in CLASSES]
    return E.prune(vec, clf.coef_[order]), clf.intercept_[order]


def pick_rule(rows, w, b, featf):
    best = None
    for pw in (0.6, 0.65, 0.7, 0.75, 0.8):
        for ps in (0.4, 0.5, 0.6):
            if ps > pw:
                continue
            m = eval_model(rows, w, b, featf, {"p_warn": pw, "p_warn_with_signal": ps})
            if m["bao_nham"] <= 0.04 and (best is None or m["bat_dung"] > best[0]["bat_dung"]):
                best = (m, {"p_warn": pw, "p_warn_with_signal": ps})
    return best[1] if best else {"p_warn": 0.6, "p_warn_with_signal": 0.4}


def main():
    D = E.load10k()
    SEED_NORM.update(E.norm(p) for ps in SEED.values() for p in ps)
    lex = build_lexicon(D["train"])
    # A. chỉ cụm từ: chọn ngưỡng trên val (báo nhầm <= 4%, bắt đúng cao nhất)
    cand = sorted({round(x, 2) for x in np.arange(0.5, 12, 0.25)})
    bestA = None
    for t in cand:
        m = eval_keywords(D["val"], lex, t)
        if m["bao_nham"] <= 0.04 and (bestA is None or m["bat_dung"] > bestA[0]["bat_dung"]):
            bestA = (m, t)
    if bestA is None:  # không đạt 4%: lấy ngưỡng có báo nhầm thấp nhất
        bestA = min(((eval_keywords(D["val"], lex, t), t) for t in cand), key=lambda x: (x[0]["bao_nham"], -x[0]["bat_dung"]))
    A = eval_keywords(D["test"], lex, bestA[1])
    # A2. chỉ cụm từ do học sinh tự soạn (không rút tự động từ dữ liệu)
    cur = {g: v for g, v in lex.items() if v["src"] == "hoc_sinh_soan" or g in SEED_NORM}
    bestA2 = None
    for t in cand:
        m = eval_keywords(D["val"], cur, t)
        if m["bao_nham"] <= 0.04 and (bestA2 is None or m["bat_dung"] > bestA2[0]["bat_dung"]):
            bestA2 = (m, t)
    A2 = eval_keywords(D["test"], cur, bestA2[1])
    # B. mô hình hiện tại
    wB, bB = train_with(E.feats, D["train"])
    rB = pick_rule(D["val"], wB, bB, E.feats)
    B = eval_model(D["test"], wB, bB, E.feats, rB)
    # C. kết hợp
    fC = lex_feats_factory(lex)
    wC, bC = train_with(fC, D["train"])
    rC = pick_rule(D["val"], wC, bC, fC)
    C = eval_model(D["test"], wC, bC, fC, rC)
    rows = [("A1. Chỉ cụm từ rút tự động từ dữ liệu", A, f"ngưỡng điểm {bestA[1]}"), ("A2. Chỉ cụm từ học sinh tự soạn", A2, f"ngưỡng điểm {bestA2[1]}"), ("B. Mô hình học từ câu (hiện tại)", B, str(rB)), ("C. Kết hợp B + cụm từ", C, str(rC))]
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    with open(os.path.join(ROOT, "results", "tn7_tu_khoa.csv"), "w", encoding="utf-8-sig", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["phuong_an", "macro_f1", "bao_nham", "bat_dung", "nguong_chon_tren_val"])
        for name, m, rule in rows:
            wr.writerow([name, m["macro_f1"], m["bao_nham"], m["bat_dung"], rule])
    with open(os.path.join(ROOT, "data", "bo_tu_khoa.csv"), "w", encoding="utf-8-sig", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["cum_tu", "cum_tu_khong_dau", "nhan", "nhom", "do_chinh_xac_tren_train", "so_lan_xuat_hien", "nguon"])
        for g, v in sorted(lex.items(), key=lambda kv: (kv[1]["label"], kv[1]["cat"], -kv[1]["prec"], kv[0])):
            wr.writerow([v["show"], g, v["label"], v["cat"], round(v["prec"], 3), v["n"], v["src"]])
    by = Counter(v["label"] for v in lex.values())
    print(f"Bộ cụm từ: {len(lex)} cụm ({dict(by)}); tập kiểm tra {len(D['test'])} tin")
    for name, m, rule in rows:
        print(f"  {name:40s} macro-F1 {m['macro_f1']:.3f} | báo nhầm {m['bao_nham']*100:5.1f}% | bắt đúng {m['bat_dung']*100:5.1f}%  ({rule})")
    return lex, rows


if __name__ == "__main__":
    main()

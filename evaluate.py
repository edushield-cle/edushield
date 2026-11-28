"""Đánh giá EduShield AI trên dữ liệu TỔNG HỢP. Chạy:  python evaluate.py

Sinh ra thư mục results/ gồm bảng số liệu (CSV), ma trận nhầm lẫn (PNG) và tóm tắt.
LƯU Ý TRUNG THỰC: đây là kết quả trên dữ liệu mô phỏng. Khi viết báo cáo phải ghi rõ
điều này; độ chính xác trên tin nhắn thật sẽ thấp hơn.
"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import ConfusionMatrixDisplay, classification_report, confusion_matrix

from data_gen import OK_DOMAINS, generate
from fusion import fuse
from graph_module import ReportGraph, evaluate_graph, simulate_reports
from pii import mask_pii
from text_model import LABELS, TextClassifier

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
os.makedirs(OUT, exist_ok=True)


def exp1_text(seeds=(1, 2, 3, 4, 5)):
    """TN1: phân loại văn bản, kiểm thử trên các MẪU CÂU chưa từng thấy, lặp 5 lần."""
    rows, last = [], None
    for s in seeds:
        train, test = generate(seed=s)
        model = TextClassifier().fit(train)
        probs = model.predict_proba([r["text"] for r in test])
        pred = [max(p, key=p.get) for p in probs]
        true = [r["label"] for r in test]
        rep = classification_report(true, pred, labels=LABELS, output_dict=True, zero_division=0)
        for lab in LABELS + ["macro avg"]:
            rows.append({"seed": s, "lop": lab, "precision": rep[lab]["precision"],
                         "recall": rep[lab]["recall"], "f1": rep[lab]["f1-score"]})
        # tỷ lệ báo động giả: tin bình thường bị gán nhãn vi phạm
        normal = [p for t, p in zip(true, pred) if t == "binh_thuong"]
        rows.append({"seed": s, "lop": "bao_dong_gia", "precision": np.nan, "recall": np.nan,
                     "f1": sum(p != "binh_thuong" for p in normal) / len(normal)})
        last = (true, pred, len(train), len(test))
    df = pd.DataFrame(rows)
    agg = df.groupby("lop")[["precision", "recall", "f1"]].agg(["mean", "std"]).round(3)
    df.to_csv(os.path.join(OUT, "tn1_van_ban_chi_tiet.csv"), index=False)
    agg.to_csv(os.path.join(OUT, "tn1_van_ban_tong_hop.csv"))
    true, pred, ntr, nte = last
    cm = confusion_matrix(true, pred, labels=LABELS)
    ConfusionMatrixDisplay(cm, display_labels=["Bình thường", "Bắt nạt", "Lừa đảo"]).plot(cmap="Blues")
    plt.title("Ma trận nhầm lẫn (mẫu câu chưa thấy, dữ liệu tổng hợp)")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "tn1_ma_tran_nham_lan.png"), dpi=150)
    plt.close()
    return agg, ntr, nte


def exp2_ablation(seed=11, n=300):
    """TN2: 'tin nhắn mồi ngắn' chỉ có link. Văn bản giống hệt nhau giữa lừa đảo và bình thường,
    nên chỉ đồ thị (chỉ dấu đã bị báo cáo) mới phân biệt được. So sánh: chỉ văn bản / chỉ đồ thị / kết hợp."""
    rng = random.Random(seed)
    reports, truth = simulate_reports(seed=seed)
    g = ReportGraph().add_reports(reports).build()
    train, _ = generate(seed=seed)
    model = TextClassifier().fit(train)
    known = [d for ds in truth["campaign_domains"].values() for d in ds]
    baits = ["xem cái này đi {l}", "vào đây nè {l}", "{l} coi thử đi", "link nè {l}", "bấm vào {l} nha", "cái này hay nè {l}"]
    items = []
    for _ in range(n):
        r = rng.random()
        if r < 0.4:      # mồi từ chiến dịch đã biết
            dom, y = rng.choice(known), 1
        elif r < 0.5:    # lừa đảo tên miền hoàn toàn mới: đồ thị chưa biết (giới hạn của hệ thống)
            dom, y = f"moi{rng.randint(0, 999)}.top", 1
        else:            # chia sẻ link bình thường
            dom, y = rng.choice(OK_DOMAINS), 0
        items.append((rng.choice(baits).format(l=f"https://{dom}/x"), y))

    def metrics(pred, y):
        tp = sum(p and t for p, t in zip(pred, y)); fp = sum(p and not t for p, t in zip(pred, y))
        fn = sum((not p) and t for p, t in zip(pred, y))
        pr = tp / (tp + fp) if tp + fp else 0.0; rc = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * pr * rc / (pr + rc) if pr + rc else 0.0
        return round(pr, 3), round(rc, 3), round(f1, 3)

    y = [t for _, t in items]
    p_text, p_graph, p_fuse = [], [], []
    for text, _ in items:
        tr = model.analyze(text)
        gr = g.indicator_risk(mask_pii(text)["indicators"])
        p_text.append(fuse(tr)["score"] >= 0.6)
        p_graph.append(gr["risk"] >= 0.6)
        p_fuse.append(fuse(tr, gr)["score"] >= 0.6)
    df = pd.DataFrame([("Chỉ văn bản", *metrics(p_text, y)), ("Chỉ đồ thị", *metrics(p_graph, y)),
                       ("Kết hợp (EduShield)", *metrics(p_fuse, y))],
                      columns=["phuong_an", "precision", "recall", "f1"])
    df.to_csv(os.path.join(OUT, "tn2_doi_chung.csv"), index=False)
    return df


def exp3_pii(seed=3):
    """TN3: tỷ lệ che được PII (số điện thoại, số tài khoản, link) trong dữ liệu tổng hợp."""
    import re
    train, test = generate(seed=seed)
    total = leaked = 0
    for r in train + test:
        raw = r["text"]
        n_pii = len(re.findall(r"\d{8,}", raw)) + len(re.findall(r"https?://", raw))
        if not n_pii:
            continue
        total += n_pii
        m = mask_pii(raw)["masked"]
        leaked += len(re.findall(r"\d{8,}", m)) + len(re.findall(r"https?://", m))
    return {"tong_pii": total, "bi_lot": leaked, "ty_le_che": round(1 - leaked / total, 4)}


if __name__ == "__main__":
    agg, ntr, nte = exp1_text()
    print(f"\n== TN1: Phân loại văn bản (≈{ntr} mẫu huấn luyện, ≈{nte} mẫu kiểm thử, 5 lần lặp) ==")
    print(agg)
    ab = exp2_ablation()
    print("\n== TN2: Đối chứng trên 'tin nhắn mồi ngắn' ==")
    print(ab.to_string(index=False))
    gr = evaluate_graph()
    print("\n== TN3: Graph AI trên đồ thị mô phỏng có đáp án ==")
    print(json.dumps(gr, ensure_ascii=False, indent=1))
    pii = exp3_pii()
    print("\n== TN4: Che thông tin cá nhân ==")
    print(pii)
    with open(os.path.join(OUT, "tom_tat.json"), "w", encoding="utf-8") as f:
        json.dump({"graph": gr, "pii": pii, "ablation": ab.to_dict("records")}, f, ensure_ascii=False, indent=1)
    print(f"\nĐã lưu kết quả vào {OUT}")

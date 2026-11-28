"""So sánh LLM với mô hình cục bộ trên mẫu kiểm thử.  Cần GEMINI_API_KEY.
Chạy:  python eval_llm.py 150      (số mẫu; gói miễn phí giới hạn tốc độ nên có nghỉ giữa các lần gọi)
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

import pandas as pd
from sklearn.metrics import classification_report

from data_gen import generate
from llm_client import analyze_with_llm, llm_available
from text_model import LABELS, TextClassifier

if not llm_available():
    sys.exit("Chưa đặt GEMINI_API_KEY.")
n = int(sys.argv[1]) if len(sys.argv) > 1 else 150
train, test = generate(seed=1)
test = test[:n]
model = TextClassifier().fit(train)
rows = []
for i, r in enumerate(test):
    local = model.analyze(r["text"])["label"]
    try:
        llm = analyze_with_llm(r["text"])["label"]
    except Exception as e:
        llm = "loi"
        print("Lỗi mẫu", i, type(e).__name__, str(e)[:120])
    rows.append({"text": r["text"], "that": r["label"], "cuc_bo": local, "llm": llm})
    time.sleep(4.5)  # tránh vượt giới hạn số lần gọi mỗi phút
df = pd.DataFrame(rows)
os.makedirs("results", exist_ok=True)
df.to_csv("results/tn5_llm_chi_tiet.csv", index=False)
ok = df[df.llm != "loi"]
print(f"\nLLM trả lời hợp lệ {len(ok)}/{len(df)} mẫu")
for name in ("cuc_bo", "llm"):
    print(f"\n== {name} ==")
    print(classification_report(ok.that, ok[name], labels=LABELS, zero_division=0, digits=3))
print("Chi tiết từng mẫu: results/tn5_llm_chi_tiet.csv (xem các dòng LLM và cục bộ bất đồng để phân tích lỗi)")

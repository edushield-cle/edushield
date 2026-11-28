"""Mô hình phân loại văn bản chạy CỤC BỘ (không gửi dữ liệu ra ngoài).

TF-IDF ký tự + từ -> Logistic Regression. Chịu được teencode và viết không dấu
nhờ n-gram ký tự và bước chuẩn hoá. Kèm bộ luật giải thích để học sinh hiểu
VÌ SAO tin nhắn bị cảnh báo (tính minh bạch).
"""
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline

from pii import mask_pii, strip_diacritics
from trust import is_trusted

LABELS = ["binh_thuong", "bat_nat", "lua_dao"]
LABEL_VI = {"binh_thuong": "Bình thường", "bat_nat": "Dấu hiệu bắt nạt", "lua_dao": "Dấu hiệu lừa đảo"}


def normalize(text: str) -> str:
    """Che PII -> viết thường -> bỏ dấu -> rút gọn ký tự lặp."""
    r = mask_pii(text)
    t = r["masked"]
    doms = r["indicators"].get("domains", [])
    if doms and all(is_trusted(d) for d in doms):
        t = t.replace("<LINK>", "<LINKOK>")  # link tới trang tin cậy: giảm báo nhầm
    t = strip_diacritics(t.lower())
    t = re.sub(r"(.)\1{2,}", r"\1\1", t)
    return re.sub(r"\s+", " ", t).strip()


# Dấu hiệu dùng để GIẢI THÍCH và ước lượng mức độ (viết không dấu vì đã chuẩn hoá)
SIGNALS = {
    "lua_dao": [
        (r"\botp\b|ma xac (nhan|minh)|mat khau", "Yêu cầu mã OTP / mật khẩu", 4),
        (r"chuyen (khoan|gap|cho|lai)|\bck\b|\bstk\b|dong phi|coc truoc|nap \S+ nhan", "Yêu cầu chuyển tiền / đặt cọc", 3),
        (r"trung thuong|qua tri an|quay thuong|mien phi|tang .*(kim cuong|skin)", "Hứa thưởng, quà miễn phí", 2),
        (r"viec nhe|luong cao|\bctv\b|tai nha|lai \d+%|gap doi|chac thang", "Lợi nhuận / việc làm phi thực tế", 3),
        (r"bi khoa|dang nhap la|xac minh|cong an|vu an|trong 24h|gap", "Tạo áp lực, gây hoảng sợ", 3),
        (r"<link>", "Có đường link cần kiểm tra", 1),
        (r"cccd|thong tin ca nhan|ho ten", "Đòi thông tin cá nhân", 3),
        (r"the cao", "Nhờ mua thẻ cào", 3),
    ],
    "bat_nat": [
        (r"danh cho|xu may|cho may o|lieu hon|biet tay|dung trach", "Đe doạ", 4),
        (r"dang .*(bi mat|len mang)|chup man hinh|anh dim|cho no nhuc", "Đe doạ phát tán thông tin / hình ảnh", 4),
        (r"dua tien|khong thi mai", "Trấn lột, cưỡng ép", 4),
        (r"\bngu\b|vo dung|dan don|rac ruoi|an hai|\bham\b|xau ho|beo nhu|que mua", "Lăng mạ, miệt thị", 2),
        (r"tay chay|kick|dung choi voi|ra ria|khong ai (ua|noi chuyen)|bien khoi", "Cô lập, tẩy chay", 3),
        (r"nghe noi|loai day", "Tung tin đồn", 2),
    ],
}


def explain(norm_text: str, label: str):
    reasons, sev = [], 1
    for pat, desc, s in SIGNALS.get(label, []):
        if re.search(pat, norm_text):
            reasons.append(desc)
            sev = max(sev, s)
    return reasons, sev


class TextClassifier:
    def __init__(self):
        self.pipe = Pipeline([
            ("feats", FeatureUnion([
                ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True)),
                ("word", TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=1, sublinear_tf=True,
                                         token_pattern=r"(?u)<?\w+>?")),
            ])),
            ("clf", LogisticRegression(max_iter=2000, C=4.0, class_weight="balanced")),
        ])

    def fit(self, rows):
        self.pipe.fit([normalize(r["text"]) for r in rows], [r["label"] for r in rows])
        return self

    def predict_proba(self, texts):
        probs = self.pipe.predict_proba([normalize(t) for t in texts])
        classes = list(self.pipe.classes_)
        return [{c: float(p[classes.index(c)]) for c in LABELS} for p in probs]

    def analyze(self, text: str) -> dict:
        """Kết quả đầy đủ cho một tin nhắn, cùng định dạng với đầu ra của LLM."""
        norm = normalize(text)
        probs = self.predict_proba([text])[0]
        label = max(probs, key=probs.get)
        reasons, sev = explain(norm, label) if label != "binh_thuong" else ([], 0)
        return {
            "label": label,
            "confidence": round(probs[label], 3),
            "probs": {k: round(v, 3) for k, v in probs.items()},
            "severity": sev,
            "reason": "; ".join(reasons) if reasons else ("Không thấy dấu hiệu rõ ràng" if label == "binh_thuong" else "Giống các mẫu đã học"),
            "source": "mo_hinh_cuc_bo",
        }


def load_10k(splits=("train", "val", "test")):
    import csv, os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "bo_huan_luyen_10000.csv")
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = [{"text": r["text"], "label": r["label"], "category": r["category"]} for r in csv.DictReader(f) if r["split"] in splits and r["category"] != "link_nguy_hiem"]  # nhóm này chỉ nhận ra qua uy tín tên miền (đồ thị/blocklist), không qua chữ
    # v1.6: thêm bộ bổ sung từ thủ đoạn do cơ quan chức năng công bố (phần doc_lap chỉ để đo, không huấn luyện)
    sp = os.path.join(os.path.dirname(path), "bo_bo_sung_nguon_tin_cay.csv")
    if os.path.exists(sp):
        with open(sp, encoding="utf-8-sig", newline="") as f:
            rows += [{"text": r["text"], "label": r["label"], "category": r["category"]} for r in csv.DictReader(f) if r["split"] in splits and r["split"] != "doc_lap"]
    # v1.7: bộ phân biệt ngữ cảnh. Máy chủ dùng 3 nhãn nên tin tuyên truyền được tính là bình thường.
    cp = os.path.join(os.path.dirname(path), "bo_phan_biet_ngu_canh.csv")
    if os.path.exists(cp):
        with open(cp, encoding="utf-8-sig", newline="") as f:
            rows += [{"text": r["text"], "label": "binh_thuong" if r["label"] == "tuyen_truyen" else r["label"], "category": r["category"]}
                     for r in csv.DictReader(f) if r["split"] in splits and r["split"] != "doc_lap"]
    return rows


def train_default(seed=42, splits=("train", "val", "test")):
    """Huấn luyện bản chạy thật trên bộ 10.000 mẫu tổng hợp (mặc định dùng cả 3 phần; muốn đánh giá thì chỉ truyền ('train',))."""
    return TextClassifier().fit(load_10k(splits))


if __name__ == "__main__":
    m = train_default()
    for s in ["Chuc mung ban trung thuong iphone, bam vao http://qua-tang.xyz de nhan",
              "mày mà mách cô thì liệu hồn", "tối nay học nhóm toán nhé", "haha thằng điên này"]:
        print(s, "->", m.analyze(s))

"""Xuất mô hình gọn + danh sách tên miền nguy hiểm (đã băm) cho tiện ích trình duyệt.
Chạy:  python export_extension.py      -> ghi extension/model.js và extension/blocklist.js

Mô hình trong trình duyệt phải nhỏ và chạy tức thì, nên dùng từ đơn + cặp từ (nhị phân)
và Logistic Regression. Mọi phép tính diễn ra trên máy học sinh.
"""
import hashlib
import json
import os
import re
import sys
import unicodedata

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "src"))

import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score

import csv
from trust import TRUSTED_DOMAINS, TRUSTED_SUFFIXES, is_trusted
from graph_module import ReportGraph, simulate_reports
from privacy_stats import CAT_CODES, EPSILON
from tu_khoa import SEED

CLASSES = ["binh_thuong", "bat_nat", "lua_dao", "tuyen_truyen"]
HARM = ("bat_nat", "lua_dao")  # chỉ hai nhãn này mới có thể dẫn tới cảnh báo
# v1.7: đặc trưng KHUNG NGỮ CẢNH (dùng chung Python và JavaScript, chạy trên văn bản đã chuẩn hoá).
# Mỗi biểu thức sinh ra một "từ ảo" (vd __canh_bao); mô hình tự học trọng số cho từ ảo đó.
FRAME = [
    ("__canh_bao", r"\b(?:canh bao|khuyen cao|luu y|canh giac|de phong|tuyen truyen|phong chong|phong tranh|nhan dien|dau hieu|thu doan|chieu tro|chieu lua)\b"),
    ("__ngoi_ba", r"\b(?:doi tuong|ke gian|ke xau|ke lua dao|nan nhan|bi hai|nguoi dan|phu huynh|nguoi dung|thanh thieu nien)\b"),
    ("__phu_dinh", r"\b(?:dung|khong nen|tuyet doi khong|khong bao gio|chang ai)(?: [a-z0-9]+){0,3} (?:chuyen|gui|bam|cung cap|doc|nap|tai|cai|tin|lam theo|cho muon|cho thue|chia se|share|dang|quay|tra loi|mo)\b"),
    ("__goi_ten", r"\b(?:lua dao|bat nat|bao luc|xam hai|toi pham|mao danh|gia mao|gia danh)\b"),
    ("__ke_lai", r"\b(?:hom qua|hom truoc|tuan truoc|nam ngoai|tung bi|da bi|suyt|may ma|dua tin|ke lai|tam su)\b"),
    ("__tim_giup", r"\b(?:bao thay co|ke voi|goi 111|goi 113|tong dai|phong tu van|nguoi lon|chup man hinh|bang chung|bao cao tai khoan)\b"),
    ("__dua", r"\b(?:haha+|hihi+|k{3,}|dua thoi|dua day|treu thoi|noi vui|yeu may)\b"),
    ("__nham_toi", r"\b(?:cua ban|cua em|cua may|ban can|em can|em phai|ban phai|may phai|ngay bay gio|ngay lap tuc|neu em|neu ban|neu may|em se bi|ban se bi|em dang bi|em co lien quan)\b"),
    ("__xung_danh", r"\b(?:chung toi la|toi la|day la|anh la|chi la|minh la|co la|thay la)(?: [a-z0-9]+){0,2} (?:cong an|can bo|vien kiem sat|toa an|nhan vien|ngan hang|thay|co|ban|phong|dieu tra)\b"),
]
QUOTE = r"[“”\"«»‘’']"  # có từ 2 dấu ngoặc trở lên: đang TRÍCH LẠI lời người khác -> từ ảo __trich
USE_FRAME = True
C_REG = 2.0  # độ mạnh điều chuẩn của hồi quy logistic (chọn trên tập kiểm định, xem thi_nghiem_ngu_canh.py)
# Biểu thức chính quy dùng CHUNG cho Python và JavaScript (chuỗi được xuất nguyên văn)
RX = {
    "url": r"(?:https?://|www\.)\S+|\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com|net|org|vn|xyz|top|info|club|vip|site|online|shop|cc|me|io|app|link|ly)\b\S*",
    "phone": r"(?<![0-9])(?:\+?84|0)(?:[ .-]?[0-9]){9}(?![0-9])",
    "num": r"(?<![0-9])[0-9](?:[ .-]?[0-9]){7,15}(?![0-9])",
}
# Dấu hiệu để giải thích và ước lượng mức độ (văn bản đã bỏ dấu, chỉ còn a-z0-9)
SIGNALS = [
    ("lua_dao", r"\botp\b|ma xac (nhan|minh)|mat khau", "Yêu cầu mã OTP hoặc mật khẩu", 4, "ld_otp"),
    ("lua_dao", r"chuyen (khoan|gap|cho|lai)|\bck\b|\bstk\b|dong phi|coc truoc|nap \w+ nhan", "Yêu cầu chuyển tiền hoặc đặt cọc", 3, "ld_chuyen_tien"),
    ("lua_dao", r"trung thuong|qua tri an|quay thuong|mien phi|tang \w* ?(kim cuong|skin)", "Hứa thưởng, quà miễn phí", 2, "ld_trung_thuong"),
    ("lua_dao", r"viec nhe|luong cao|\bctv\b|tai nha|lai [0-9]+|gap doi|chac thang", "Lợi nhuận hoặc việc làm phi thực tế", 3, "ld_viec_lam"),
    ("lua_dao", r"bi khoa|dang nhap la|xac minh|cong an|vu an|trong 24h|\bgap\b", "Tạo áp lực, gây hoảng sợ", 3, "ld_de_doa"),
    ("lua_dao", r"vien kiem sat|giu bi mat|khong duoc noi voi bo me|phuc vu dieu tra|khach san|rua tien", "Dấu hiệu “bắt cóc online”: bắt giữ bí mật, cô lập khỏi gia đình", 4, "ld_de_doa"),
    ("lua_dao", r"urltoken", "Có đường link cần kiểm tra", 1, None),
    ("lua_dao", r"cccd|thong tin ca nhan|ho ten", "Đòi thông tin cá nhân", 3, "ld_thong_tin"),
    ("lua_dao", r"the cao", "Nhờ mua thẻ cào", 3, "ld_the_cao"),
    ("lua_dao", r"thue tai khoan|tai khoan ngan hang|ca cuoc|danh de|lay lai tien", "Lôi kéo cho thuê tài khoản, cá cược", 3, "ld_khac"),
    ("bat_nat", r"danh cho|xu may|cho may o|lieu hon|biet tay|dung trach", "Đe doạ", 4, "bn_de_doa"),
    ("bat_nat", r"dang \w* ?(bi mat|len mang)|chup man hinh|anh dim|cho no nhuc|anh ghep|anh rieng tu|tung len", "Đe doạ phát tán thông tin, hình ảnh", 4, "bn_phat_tan"),
    ("bat_nat", r"dua tien|khong thi mai", "Trấn lột, cưỡng ép", 4, "bn_tran_lot"),
    ("bat_nat", r"\bngu\b|vo dung|dan don|rac ruoi|an hai|\bham\b|xau ho|beo nhu|que mua", "Lăng mạ, miệt thị", 2, "bn_lang_ma"),
    ("bat_nat", r"tay chay|\bkick\b|dung choi voi|ra ria|khong ai (ua|noi chuyen)|bien khoi|unfollow|nghi choi", "Cô lập, tẩy chay", 3, "bn_co_lap"),
    ("bat_nat", r"spam chui|report hoi dong|bay mau", "Kêu gọi tấn công tập thể", 3, "bn_khac"),
    ("bat_nat", r"nghe noi|loai day|boc phot|confession|dia chi nha", "Tung tin đồn, bóc phốt", 2, "bn_tin_don"),
]
# Quy tắc ra cảnh báo (giữ thận trọng để ít báo nhầm)
RULE = {"p_warn": 0.6, "p_warn_with_signal": 0.4, "sev_signal": 3}


def strip(s):
    s = s.replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if not ("̀" <= c <= "ͯ"))


def domain_of(u):
    return re.sub(r"[.,;:!)]+$", "", re.split(r"[/?#]", re.sub(r"^www\.", "", re.sub(r"^https?://", "", u.lower())))[0])


def _url_token(t):
    doms = [domain_of(m.group(0)) for m in re.finditer(RX["url"], t)]
    return " linkoktoken " if doms and all(is_trusted(d) for d in doms) else " urltoken "


def norm(t):
    t = strip(t).lower()
    tok = _url_token(t)
    t = re.sub(RX["url"], tok, t)
    t = re.sub(RX["phone"], " phonetoken ", t)
    t = re.sub(RX["num"], " numtoken ", t)
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return " ".join(t.split())


def frame_feats(text, n):
    out = [name for name, rx in FRAME if re.search(rx, n)]
    if len(re.findall(QUOTE, text)) >= 2:
        out.append("__trich")
    return out


def feats(text):
    n = norm(text)
    toks = n.split()
    f = toks + [a + " " + b for a, b in zip(toks, toks[1:])]
    if USE_FRAME:
        f += frame_feats(text, n)
    return list(dict.fromkeys(f))


RX_DIRECT = r"\b(?:urltoken|numtoken|phonetoken)\b"  # link lạ, số tài khoản, số điện thoại trong tin
# Yêu cầu hành động thường gặp trong tin lừa (chuyển tiền, nạp, đọc mã, xác minh, đăng nhập...)
RX_ACT = r"\b(?:chuyen|nap|dong phi|dong tien|gui ma|doc ma|xac minh|xac thuc|dang nhap|nhap mat khau|bam vao|truy cap|lien he ngay|goi lai)\b"


RX_QSPAN = r"[“\"«‘'][^”\"»’']*[”\"»’']"  # đoạn nằm trong ngoặc kép (lời được trích lại)


def harm_override(probs, n, text=None):
    """Luật an toàn v1.7: khung "tuyên truyền" KHÔNG được che một tin vừa có link lạ / số tài khoản / số điện thoại,
    vừa có yêu cầu hành động (chuyển tiền, đọc mã, xác minh, đăng nhập...) mà không có lời phủ định (đừng, không...).
    Kẻ xấu hay giả dạng lời cảnh báo, thông báo chính thức để lừa. Trả về (nhãn, xác suất) hoặc None."""
    if "tuyen_truyen" not in CLASSES or CLASSES[int(np.argmax(probs))] != "tuyen_truyen":
        return None
    if text is not None:  # chỉ xét phần KHÔNG nằm trong ngoặc kép: tin lừa được trích lại để cảnh báo thì không tính
        n = norm(re.sub(RX_QSPAN, " ", text))
    if not re.search(RX_DIRECT, n) or not re.search(RX_ACT, n) or re.search(dict(FRAME)["__phu_dinh"], n):
        return None
    hl = max(HARM, key=lambda c: probs[CLASSES.index(c)])
    return hl, float(probs[CLASSES.index(hl)])


def decide(probs, n, text=None):
    label = CLASSES[int(np.argmax(probs))]
    p = float(max(probs))
    ov = harm_override(probs, n, text)
    if ov:
        return ov[0], True
    sev = 0
    if label in HARM:
        sev = 1
        for lab, pat, _, s, _c in SIGNALS:
            if lab == label and re.search(pat, n):
                sev = max(sev, s)
    warn = label in HARM and (p >= RULE["p_warn"] or (p >= RULE["p_warn_with_signal"] and sev >= RULE["sev_signal"]))
    return label, warn


def train(rows):
    vec = CountVectorizer(analyzer=feats, binary=True, min_df=2)
    X = vec.fit_transform([r["text"] for r in rows])
    clf = LogisticRegression(max_iter=3000, C=C_REG, class_weight="balanced").fit(X, [r["label"] for r in rows])
    assert list(clf.classes_) == sorted(CLASSES), (clf.classes_, CLASSES)
    order = [list(clf.classes_).index(c) for c in CLASSES]
    return vec, clf.coef_[order], clf.intercept_[order]


def prune(vec, coef, thr=0.02):
    w = {}
    for f, j in vec.vocabulary_.items():
        col = coef[:, j]
        if np.abs(col).max() >= thr:
            w[f] = [round(float(x), 4) for x in col]
    return w


def predict_exported(weights, intercept, text):
    z = np.array(intercept, dtype=float)
    for f in feats(text):
        if f in weights:
            z += weights[f]
    e = np.exp(z - z.max())
    return e / e.sum()


def load10k():
    with open(os.path.join(ROOT, "data", "bo_huan_luyen_10000.csv"), encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    # link_nguy_hiem: chữ vô hại, chỉ nhận ra qua uy tín tên miền (blocklist/đồ thị) nên không đưa vào mô hình chữ
    rows = [relabel(r) for r in rows]
    return {sp: [r for r in rows if r["split"] == sp and r["category"] != "link_nguy_hiem"] for sp in ("train", "val", "test")}


def relabel(r):
    """v1.7: tin nhắc nhau cảnh giác (bt_canh_bao_dung) là TUYÊN TRUYỀN, không phải chat thường."""
    if "tuyen_truyen" in CLASSES and r["category"] == "bt_canh_bao_dung":
        r = dict(r, label="tuyen_truyen")
    if "tuyen_truyen" not in CLASSES and r["label"] == "tuyen_truyen":
        r = dict(r, label="binh_thuong")
    return r


FINE = [c for c in CAT_CODES if c not in ("lua_dao_bat_ky", "bat_nat_bat_ky") and not c.startswith("hv_")]


def train_fine(rows):
    """Phân loại nhóm chi tiết (chỉ trên mẫu có hại). Nhãn đã có sẵn trong bộ dữ liệu."""
    rows = [r for r in rows if r["label"] in HARM and r["category"] in FINE]
    vec = CountVectorizer(analyzer=feats, binary=True, min_df=2)
    X = vec.fit_transform([r["text"] for r in rows])
    clf = LogisticRegression(max_iter=3000, C=2.0, class_weight="balanced").fit(X, [r["category"] for r in rows])
    return vec, clf


def prune_fine(vec, clf, thr=0.05):
    w = {}
    for f, j in vec.vocabulary_.items():
        col = clf.coef_[:, j]
        if np.abs(col).max() >= thr:
            w[f] = [round(float(x), 3) for x in col]
    return w


def metrics(rows, w, b, rule=None):
    pred, warn, true = [], [], []
    old = dict(RULE)
    if rule: RULE.update(rule)
    for r in rows:
        pr = predict_exported(w, b, r["text"])
        lab, wa = decide(pr, norm(r["text"]), r["text"])
        pred.append(lab); warn.append(wa); true.append(r["label"])
    RULE.clear(); RULE.update(old)
    m3 = lambda x: "binh_thuong" if x not in HARM else x
    true3, pred3 = [m3(x) for x in true], [m3(x) for x in pred]
    normal = [wa for t, wa in zip(true3, warn) if t == "binh_thuong"]
    harm = [wa for t, wa in zip(true3, warn) if t != "binh_thuong"]
    return {"macro_f1": round(float(f1_score(true3, pred3, labels=["binh_thuong", "bat_nat", "lua_dao"], average="macro")), 3),
            "bao_nham": round(sum(normal) / len(normal), 3), "bat_dung": round(sum(harm) / len(harm), 3)}


def tune_rule(rows, w, b):
    """Chọn ngưỡng trên tập val: báo nhầm <= 4% (chừa biên an toàn) rồi lấy ngưỡng cho tỉ lệ bắt đúng cao nhất."""
    best = None
    for pw in (0.5, 0.6, 0.65, 0.7, 0.75, 0.8):
        for ps in (0.4, 0.5, 0.6):
            if ps > pw: continue
            m = metrics(rows, w, b, {"p_warn": pw, "p_warn_with_signal": ps})
            if m["bao_nham"] <= 0.04 and (best is None or m["bat_dung"] > best[0]["bat_dung"]):
                best = (m, {"p_warn": pw, "p_warn_with_signal": ps})
    return best


def evaluate(seeds=(1, 2, 3, 4, 5)):
    f1s, fps, recs = [], [], []
    for s in seeds:
        tr, te = generate(seed=s)
        vec, coef, b = train(tr)
        w = prune(vec, coef)
        pred, warn, true = [], [], []
        for r in te:
            pr = predict_exported(w, b, r["text"])
            lab, wa = decide(pr, norm(r["text"]))
            pred.append(lab); warn.append(wa); true.append(r["label"])
        f1s.append(f1_score(true, pred, labels=CLASSES, average="macro"))
        normal = [wa for t, wa in zip(true, warn) if t == "binh_thuong"]
        harm = [wa for t, wa in zip(true, warn) if t != "binh_thuong"]
        fps.append(sum(normal) / len(normal)); recs.append(sum(harm) / len(harm))
    return {
        "macro_f1": (round(float(np.mean(f1s)), 3), round(float(np.std(f1s)), 3)),
        "ty_le_bao_nham": (round(float(np.mean(fps)), 3), round(float(np.std(fps)), 3)),
        "ty_le_canh_bao_dung": (round(float(np.mean(recs)), 3), round(float(np.std(recs)), 3)),
    }


def load_supp():
    """Bộ bổ sung v1.6 (thủ đoạn do cơ quan chức năng công bố). Phần doc_lap chỉ dùng để đo, không bao giờ để huấn luyện chọn ngưỡng."""
    p = os.path.join(ROOT, "data", "bo_bo_sung_nguon_tin_cay.csv")
    if not os.path.exists(p):
        return {"train": [], "val": [], "doc_lap": []}
    with open(p, encoding="utf-8-sig", newline="") as f:
        rows = [relabel(r) for r in csv.DictReader(f)]
    return {sp: [r for r in rows if r["split"] == sp] for sp in ("train", "val", "doc_lap")}


def load_ctx():
    """Bộ phân biệt ngữ cảnh v1.7 (tuyên truyền / tin thường khó / nguy cơ giả dạng cảnh báo)."""
    p = os.path.join(ROOT, "data", "bo_phan_biet_ngu_canh.csv")
    if not os.path.exists(p):
        return {"train": [], "val": [], "doc_lap": []}
    with open(p, encoding="utf-8-sig", newline="") as f:
        rows = [relabel(r) for r in csv.DictReader(f)]
    return {sp: [r for r in rows if r["split"] == sp] for sp in ("train", "val", "doc_lap")}


def load_vt():
    """Tập kiểm tra viết tay: CHỈ để đo."""
    with open(os.path.join(ROOT, "data", "kiem_tra_viet_tay.csv"), encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def vt_metrics(rows, w, b):
    out = {}
    for g in ("tuyen_truyen", "thuong_kho", "truc_tiep", "gia_canh_bao"):
        rs = [r for r in rows if r["nhom"] == g]
        wa = [decide(predict_exported(w, b, r["text"]), norm(r["text"]), r["text"])[1] for r in rs]
        out[g] = {"so_tin": len(rs), "ti_le_canh_bao": round(sum(wa) / max(1, len(rs)), 3)}
    return out


def main():
    D = load10k()
    S = load_supp()
    N = load_ctx()
    D["train"] = D["train"] + S["train"] + N["train"]; D["val"] = D["val"] + S["val"] + N["val"]
    print("Huấn luyện trên tập train (%d), chọn ngưỡng trên val (%d), đo trên test (%d)" % tuple(len(D[k]) for k in ("train", "val", "test")))
    vec, coef, b = train(D["train"])
    w = prune(vec, coef)
    before = metrics(D["test"], w, b)  # ngưỡng cũ 0.6/0.4
    tuned = tune_rule(D["val"], w, b)
    # Không hạ ngưỡng dưới 0.6: val và test cách nhau vài chục khuôn câu nên chênh lệch lớn, ưu tiên ít báo nhầm
    if tuned and tuned[1]["p_warn"] >= 0.6:
        RULE.update(tuned[1])
    after = metrics(D["test"], w, b)
    fvec, fclf = train_fine(D["train"])
    fw = prune_fine(fvec, fclf)
    ft = [r for r in D["test"] if r["label"] != "binh_thuong" and r["category"] in FINE]
    fp = fclf.predict(fvec.transform([r["text"] for r in ft]))
    fine_acc = round(float(np.mean([x == r["category"] for x, r in zip(fp, ft)])), 3)
    doc_lap = metrics(S["doc_lap"], w, b) if S["doc_lap"] else None
    ngu_canh = metrics(N["doc_lap"], w, b) if N["doc_lap"] else None
    vt = vt_metrics(load_vt(), w, b)
    ev = {"test_ngưỡng_cũ": before, "test_ngưỡng_mới": after, "kiem_tra_doc_lap": doc_lap, "ngu_canh_doc_lap": ngu_canh, "viet_tay": vt,
          "ngưỡng": dict(RULE), "do_chinh_xac_nhom_chi_tiet": fine_acc,
          "so_mau": {"train": len(D["train"]), "val": len(D["val"]), "test": len(D["test"]), "doc_lap": len(S["doc_lap"]),
                     "ngu_canh_doc_lap": len(N["doc_lap"]), "viet_tay": sum(v["so_tin"] for v in vt.values())}}
    print(json.dumps(ev, ensure_ascii=False))
    # bản chạy thật: huấn luyện lại trên train+val (test giữ làm số liệu độc lập đã báo ở trên)
    full = D["train"] + D["val"]
    vec, coef, b = train(full)
    w = prune(vec, coef)
    fvec, fclf = train_fine(full)
    fw = prune_fine(fvec, fclf)
    model = {
        "version": 1, "classes": CLASSES, "intercept": [round(float(x), 4) for x in b],
        "weights": w, "regex": RX, "frame": [list(x) for x in FRAME], "quote": QUOTE, "direct": RX_DIRECT, "act": RX_ACT, "qspan": RX_QSPAN, "signals": [list(s) for s in SIGNALS], "rule": RULE, "eval": ev, "categories": CAT_CODES, "epsilon": EPSILON,
        "fine": {"classes": list(fclf.classes_), "intercept": [round(float(x), 3) for x in fclf.intercept_], "weights": fw},
        # Cụm từ đáng chú ý (do học sinh soạn) để CHỈ RA trong cảnh báo: [dạng không dấu, dạng hiển thị, nhóm]
        "phrases": [[norm(p), p, c] for c, ps in SEED.items() for p in ps],
    }
    ext = os.path.join(ROOT, "extension")
    os.makedirs(ext, exist_ok=True)
    with open(os.path.join(ext, "model.js"), "w", encoding="utf-8") as f:
        f.write("// Tự sinh bởi export_extension.py, không sửa tay.\nglobalThis.EDUSHIELD_MODEL = ")
        json.dump(model, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    # Danh sách tên miền nguy hiểm từ đồ thị (cùng dữ liệu mô phỏng với server.py), chỉ lưu mã băm SHA-256
    reports, _ = simulate_reports(seed=7)
    g = ReportGraph().add_reports(reports).build()
    hashes = sorted(hashlib.sha256(d.encode()).hexdigest() for d in g.risky_domains())
    with open(os.path.join(ext, "blocklist.js"), "w", encoding="utf-8") as f:
        f.write("// Mã băm SHA-256 của tên miền bị báo cáo lừa đảo. Tự sinh, không sửa tay.\n")
        f.write("globalThis.EDUSHIELD_BLOCKLIST = " + json.dumps(hashes) + ";\n")
        f.write("// Tên miền tin cậy: không bao giờ bị chặn (chống bị đầu độc danh sách).\n")
        f.write("globalThis.EDUSHIELD_ALLOWLIST = " + json.dumps({"domains": sorted(TRUSTED_DOMAINS), "suffixes": list(TRUSTED_SUFFIXES)}) + ";\n")
    # Bản dùng cho app điện thoại (PWA) nằm trong thư mục riêng để tự chứa, chạy ngoại tuyến được
    import shutil
    mob = os.path.join(ROOT, "mobile")
    os.makedirs(mob, exist_ok=True)
    for fn in ("model.js", "blocklist.js", "detector.js"):
        shutil.copy(os.path.join(ext, fn), os.path.join(mob, fn))
    print(f"Đã xuất {len(w)} đặc trưng, {len(hashes)} tên miền nguy hiểm (đã băm) vào {ext} và {mob}")
    # Mẫu để kiểm tra bản JavaScript cho ra kết quả giống hệt Python
    te = D["test"][:200] + N["doc_lap"][:150] + [dict(r) for r in load_vt()]
    samples = [{"text": r["text"], "probs": [round(float(x), 6) for x in predict_exported(w, b, r["text"])],
                "norm": norm(r["text"])} for r in te]
    os.makedirs(os.path.join(ROOT, "tests"), exist_ok=True)
    with open(os.path.join(ROOT, "tests", "extension_samples.json"), "w", encoding="utf-8") as f:
        json.dump(samples, f, ensure_ascii=False)


if __name__ == "__main__":
    main()

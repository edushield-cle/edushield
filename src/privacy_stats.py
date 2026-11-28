"""Thống kê ẩn danh cho nhà trường bằng Randomized Response (quyền riêng tư vi phân cục bộ).

Ý tưởng:
  1. Mỗi ngày, tiện ích trên máy học sinh tạo MỘT gói gồm các bit có/không:
     "hôm nay em có gặp loại nguy cơ X không?" (không có nội dung, không thời điểm, không định danh).
  2. TRƯỚC KHI GỬI, mỗi bit được "tung đồng xu": giữ đúng với xác suất p = e^ε/(1+e^ε),
     ngược lại thì đảo. Vì vậy một gói đơn lẻ không chứng minh được em đó đã gặp gì.
  3. Máy chủ chỉ CỘNG DỒN theo (trường, khối, ngày) rồi bỏ gói. Không lưu gói lẻ.
  4. Khi cộng nhiều học sinh, nhiễu triệt tiêu nhau nên ước lượng được tỷ lệ chung.
  5. Nhóm có ít hơn K_MIN gói bị ẩn để tránh suy ra cá nhân.
"""
import json
import math
import os
import random
import re
import tempfile
import threading
from collections import defaultdict
from datetime import date, timedelta

EPSILON = 2.0          # mức riêng tư mặc định: p giữ đúng ≈ 0,88
K_MIN = 20             # số gói tối thiểu để hiển thị một nhóm
ALLOWED_EPS = (0.5, 1.0, 2.0, 3.0)
GRADES = ("10", "11", "12", "")

# (mã, nhóm, tên hiển thị, gợi ý chủ đề tuyên truyền)
CATEGORIES = [
    ("lua_dao_bat_ky", "lua_dao", "Gặp ít nhất một dấu hiệu lừa đảo", None),
    ("bat_nat_bat_ky", "bat_nat", "Gặp ít nhất một dấu hiệu bắt nạt", None),
    ("ld_otp", "lua_dao", "Bị xin mã OTP, mật khẩu", "Không bao giờ đưa mã OTP, mật khẩu cho bất kỳ ai, kể cả người tự nhận là ngân hàng hay bạn bè."),
    ("ld_chuyen_tien", "lua_dao", "Bị đòi chuyển tiền, đặt cọc", "Giả danh thầy cô, người thân xin chuyển tiền: luôn gọi điện trực tiếp để xác minh; trường chỉ thu qua kênh chính thức."),
    ("ld_trung_thuong", "lua_dao", "Báo trúng thưởng, tặng quà", "Không có quà miễn phí thật sự: trúng thưởng bất ngờ kèm link hay phí nhận quà là lừa đảo."),
    ("ld_viec_lam", "lua_dao", "Việc nhẹ lương cao, CTV, đầu tư", "Việc nhẹ lương cao, làm nhiệm vụ, đầu tư lãi khủng: nhận biết bẫy 'nạp tiền nhận gấp đôi'."),
    ("ld_de_doa", "lua_dao", "Giả danh công an, 'bắt cóc online'", "Công an không làm việc qua mạng, không bắt giữ bí mật với gia đình hay ở một mình trong khách sạn: nhận diện thủ đoạn 'bắt cóc online'."),
    ("ld_thong_tin", "lua_dao", "Bị đòi thông tin cá nhân, CCCD", "Bảo vệ thông tin cá nhân: không gửi ảnh CCCD, họ tên, địa chỉ cho người lạ trên mạng."),
    ("ld_the_cao", "lua_dao", "Bị nhờ mua thẻ cào", "Nhờ mua thẻ cào rồi gửi mã: chiêu chiếm tài khoản quen thuộc, hãy gọi điện hỏi lại người nhờ."),
    ("ld_khac", "lua_dao", "Lôi kéo thuê tài khoản, cá cược", "Không mở, cho thuê tài khoản ngân hàng đứng tên mình; tránh app cá cược, 'lấy lại tiền bị lừa'."),
    ("link_nguy_hiem", "lua_dao", "Gặp link lừa đảo đã bị báo cáo", "Kiểm tra link trước khi bấm; không đăng nhập qua link nhận trong tin nhắn."),
    ("bn_de_doa", "bat_nat", "Bị đe doạ", "Bị đe doạ trên mạng: lưu bằng chứng, không đáp trả, báo ngay thầy cô; trường luôn bảo vệ người báo."),
    ("bn_phat_tan", "bat_nat", "Bị doạ phát tán ảnh, thông tin", "Không chia sẻ ảnh, tin nhắn riêng của bạn khác; phát tán là vi phạm pháp luật."),
    ("bn_tran_lot", "bat_nat", "Bị ép đưa tiền, đồ", "Trấn lột qua mạng: không sợ hãi, báo ngay thầy cô hoặc gọi 111."),
    ("bn_lang_ma", "bat_nat", "Bị lăng mạ, miệt thị", "Lời nói trên mạng cũng làm tổn thương: văn hoá ứng xử, không body-shaming, không miệt thị."),
    ("bn_co_lap", "bat_nat", "Bị cô lập, tẩy chay", "Không ai bị bỏ lại: phòng chống tẩy chay, cô lập trong nhóm lớp."),
    ("bn_tin_don", "bat_nat", "Bị tung tin đồn", "Không lan truyền tin đồn; kiểm chứng trước khi chia sẻ."),
    ("bn_khac", "bat_nat", "Bị kêu gọi tấn công tập thể", "Không hùa theo 'report hội đồng', spam chửi một bạn: văn hoá bình luận trên mạng xã hội."),
    # v1.9: hành vi của chính học sinh (chỉ là ô có/không đã trộn nhiễu, không biết là ai)
    ("hv_nhac_gui", "hanh_vi", "Được nhắc trước khi gửi tin có thể gây tổn thương, lừa đảo", "Dừng lại trước khi gửi: một câu nói lúc nóng giận có thể là bắt nạt; không gửi mã OTP, tiền theo yêu cầu qua mạng."),
    ("hv_bao_luc", "hanh_vi", "Gặp ảnh, video có dấu hiệu bạo lực (đã làm mờ)", "Không xem, không chia sẻ clip bạo lực: mỗi lượt chia sẻ làm người bị hại tổn thương thêm; báo thầy cô để gỡ bỏ."),
]
CAT_CODES = [c[0] for c in CATEGORIES]
CAT_INFO = {c[0]: {"group": c[1], "name": c[2], "topic": c[3]} for c in CATEGORIES}


def p_keep(eps: float) -> float:
    return math.exp(eps) / (1 + math.exp(eps))


def randomize(bits: dict, eps: float = EPSILON, rng=random) -> dict:
    """Mô phỏng phía tiện ích (bản JS làm y hệt)."""
    p = p_keep(eps)
    return {k: (b if rng.random() < p else 1 - b) for k, b in bits.items()}


def estimate(n: int, s: int, eps: float) -> dict:
    """Ước lượng không chệch số gói có bit = 1 thật sự, kèm khoảng tin cậy 95%."""
    p = p_keep(eps)
    est = (s - n * (1 - p)) / (2 * p - 1)
    sd = math.sqrt(n * p * (1 - p)) / (2 * p - 1)
    lo, hi = est - 1.96 * sd, est + 1.96 * sd
    clip = lambda x: max(0.0, min(float(n), x))
    return {"est": clip(est), "lo": clip(lo), "hi": clip(hi),
            "pct": clip(est) / n if n else 0.0, "pct_lo": clip(lo) / n if n else 0.0, "pct_hi": clip(hi) / n if n else 0.0}


_SCHOOL_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")


def validate_packet(pk: dict, today: date | None = None) -> dict:
    """Kiểm tra gói từ tiện ích. Chỉ chấp nhận đúng các trường cho phép, còn lại bỏ qua."""
    today = today or date.today()
    school = str(pk.get("school", ""))
    if not _SCHOOL_RE.match(school):
        raise ValueError("Mã trường không hợp lệ")
    grade = str(pk.get("grade", ""))
    if grade not in GRADES:
        raise ValueError("Khối không hợp lệ")
    try:
        day = date.fromisoformat(str(pk.get("day", "")))
    except ValueError:
        raise ValueError("Ngày không hợp lệ")
    if day > today or day < today - timedelta(days=14):
        raise ValueError("Ngày ngoài khoảng cho phép")
    eps = float(pk.get("eps", -1))
    if eps not in ALLOWED_EPS:
        raise ValueError("Mức riêng tư không hợp lệ")
    bits = pk.get("bits", {})
    if set(bits) != set(CAT_CODES) or any(v not in (0, 1) for v in bits.values()):
        raise ValueError("Danh sách bit không hợp lệ")
    return {"school": school, "grade": grade, "day": day.isoformat(), "eps": eps, "bits": bits}


class Aggregator:
    """Chỉ lưu tổng: {trường|khối|ngày|eps: {"n": số gói, "s": {mã: tổng bit}}}. Không lưu gói lẻ."""

    def __init__(self, path: str | None = None):
        self.path = path
        self.lock = threading.Lock()
        self.cells = defaultdict(lambda: {"n": 0, "s": {c: 0 for c in CAT_CODES}})
        if path and os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                for k, v in json.load(f).items():
                    self.cells[k] = v

    def add(self, pk: dict, save=True):
        key = f'{pk["school"]}|{pk["grade"]}|{pk["day"]}|{pk["eps"]}'
        with self.lock:
            cell = self.cells[key]
            cell["n"] += 1
            for c in CAT_CODES:
                cell["s"][c] = cell["s"].get(c, 0) + int(pk["bits"][c])
            if save:
                self.save()

    def save(self):
        if not self.path:
            return
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(self.path), suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(self.cells, f, ensure_ascii=False)
        os.replace(tmp, self.path)

    def schools(self):
        return sorted({k.split("|")[0] for k in self.cells})

    def report(self, school: str, group: str = "week", grade: str | None = None) -> list:
        """Trả về danh sách kỳ (ngày hoặc tuần) với ước lượng cho từng loại nguy cơ.
        grade=None: gộp mọi khối."""
        buckets = defaultdict(lambda: defaultdict(lambda: {"n": 0, "s": defaultdict(int)}))
        for key, cell in self.cells.items():
            sch, gr, day, eps = key.split("|")
            if sch != school or (grade is not None and gr != grade):
                continue
            d = date.fromisoformat(day)
            period = d.isoformat() if group == "day" else (d - timedelta(days=d.weekday())).isoformat()
            b = buckets[period][float(eps)]
            b["n"] += cell["n"]
            for c in CAT_CODES:
                b["s"][c] += cell["s"].get(c, 0)
        out = []
        for period in sorted(buckets):
            n_total = sum(b["n"] for b in buckets[period].values())
            row = {"period": period, "n": n_total, "hidden": n_total < K_MIN, "cats": {}}
            if not row["hidden"]:
                for c in CAT_CODES:
                    # Cộng ước lượng của từng mức eps (mỗi phần là không chệch)
                    est = 0.0
                    var = 0.0
                    for eps, b in buckets[period].items():
                        p = p_keep(eps)
                        est += (b["s"][c] - b["n"] * (1 - p)) / (2 * p - 1)
                        var += b["n"] * p * (1 - p) / (2 * p - 1) ** 2
                    sd = math.sqrt(var)
                    clip = lambda x: max(0.0, min(float(n_total), x))
                    row["cats"][c] = {"est": round(clip(est), 1), "pct": clip(est) / n_total,
                                      "pct_lo": clip(est - 1.96 * sd) / n_total, "pct_hi": clip(est + 1.96 * sd) / n_total}
            out.append(row)
        return out

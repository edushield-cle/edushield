"""Che thông tin cá nhân (PII) TRƯỚC KHI văn bản đi vào bất kỳ mô hình nào.

Nguyên tắc: mô hình và cơ sở dữ liệu chỉ nhìn thấy văn bản đã che.
Các "chỉ dấu" (tên miền, số điện thoại, số tài khoản) được giữ lại dưới dạng
tên miền công khai hoặc mã băm một chiều để phục vụ Graph AI, không thể dịch ngược.
"""
import hashlib
import os
import re
import unicodedata

# Muối băm: đặt biến môi trường EDUSHIELD_SALT khi triển khai thật.
_SALT = os.environ.get("EDUSHIELD_SALT", "doi-muoi-nay-khi-trien-khai")

URL_RE = re.compile(
    r"(?:https?://|www\.)[^\s<>\"']+|\b[a-z0-9][a-z0-9-]*(?:\.[a-z0-9-]+)*\.(?:com|net|org|vn|xyz|top|info|club|vip|site|online|shop|cc|me|io|app|link|ly)\b(?:/[^\s<>\"']*)?",
    re.IGNORECASE,
)
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
# Số điện thoại VN: 0xxxxxxxxx hoặc +84xxxxxxxxx, cho phép dấu cách/chấm/gạch
PHONE_RE = re.compile(r"(?<!\d)(?:\+?84|0)(?:[\s.-]?\d){9}(?!\d)")
# Chuỗi số dài (số tài khoản, CCCD): 8-16 chữ số
LONGNUM_RE = re.compile(r"(?<!\d)\d(?:[\s.-]?\d){7,15}(?!\d)")
MENTION_RE = re.compile(r"@[\w.]+")
# Tên riêng viết hoa đứng sau từ xưng hô (heuristic, không hoàn hảo)
_UP = "A-ZÀ-ỸĐ"
_LOW = "a-zà-ỹđ"
NAME_RE = re.compile(
    rf"\b(bạn|em|anh|chị|cô|thầy|thằng|con|đứa|nhỏ|bé)\s+([{_UP}][{_LOW}]+(?:\s[{_UP}][{_LOW}]+){{0,2}})"
)


def hash_id(value: str, prefix: str = "") -> str:
    """Băm một chiều có muối, rút gọn 12 ký tự. Không dịch ngược được."""
    digest = hashlib.sha256((_SALT + "|" + value).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}{digest}"


def domain_of(url: str) -> str:
    u = re.sub(r"^https?://", "", url.strip().lower())
    u = re.sub(r"^www\.", "", u)
    return u.split("/")[0].split("?")[0].rstrip(".,;:!)")


def _digits(s: str) -> str:
    return re.sub(r"\D", "", s)


def mask_pii(text: str) -> dict:
    """Trả về {'masked': văn bản đã che, 'indicators': {...}, 'counts': {...}}."""
    text = unicodedata.normalize("NFC", text)
    indicators = {"domains": [], "phones": [], "accounts": []}
    counts = {"url": 0, "email": 0, "phone": 0, "number": 0, "mention": 0, "name": 0}

    def _url(m):
        counts["url"] += 1
        indicators["domains"].append(domain_of(m.group(0)))
        return "<LINK>"

    def _email(m):
        counts["email"] += 1
        return "<EMAIL>"

    def _phone(m):
        counts["phone"] += 1
        d = _digits(m.group(0))
        if d.startswith("84"):
            d = "0" + d[2:]
        indicators["phones"].append(hash_id(d, "ph_"))
        return "<SĐT>"

    def _num(m):
        counts["number"] += 1
        indicators["accounts"].append(hash_id(_digits(m.group(0)), "stk_"))
        return "<SỐ>"

    def _mention(m):
        counts["mention"] += 1
        return "<NGƯỜI>"

    def _name(m):
        counts["name"] += 1
        return f"{m.group(1)} <TÊN>"

    out = EMAIL_RE.sub(_email, text)
    out = URL_RE.sub(_url, out)
    out = PHONE_RE.sub(_phone, out)
    out = LONGNUM_RE.sub(_num, out)
    out = MENTION_RE.sub(_mention, out)
    out = NAME_RE.sub(_name, out)
    for k in indicators:
        indicators[k] = sorted(set(indicators[k]))
    return {"masked": out, "indicators": indicators, "counts": counts}


def strip_diacritics(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return unicodedata.normalize("NFC", s.replace("đ", "d").replace("Đ", "D"))


if __name__ == "__main__":
    demo = "Em Lan chuyển 500k vào stk 1903 5566 7788 rồi gọi cô số 0912.345.678, xem https://truong-gia.xyz/hocphi nhé @minh"
    r = mask_pii(demo)
    print(r["masked"])
    print(r["indicators"])

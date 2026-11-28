"""Danh sách tên miền TIN CẬY (dùng chung cho đồ thị, mô hình văn bản và tiện ích).
Tin cậy ở đây chỉ nghĩa là "không tự động coi link là đáng ngờ", KHÔNG bảo đảm nội dung an toàn
(ví dụ một tài liệu độc hại vẫn có thể được đăng lên drive.google.com)."""
TRUSTED_SUFFIXES = (".edu.vn", ".gov.vn")
TRUSTED_DOMAINS = {
    "vnedu.vn", "olm.vn", "hoc10.vn", "google.com", "youtube.com", "facebook.com", "messenger.com", "zalo.me",
    "tiktok.com", "instagram.com", "microsoft.com", "wikipedia.org",
}


def is_trusted(domain: str) -> bool:
    d = domain.lower().strip(".")
    if d.endswith(TRUSTED_SUFFIXES):
        return True
    parts = d.split(".")
    return any(".".join(parts[i:]) in TRUSTED_DOMAINS for i in range(len(parts) - 1))

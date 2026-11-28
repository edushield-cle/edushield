"""Yêu cầu hỗ trợ CÓ DANH TÍNH (v1.6): chỉ khi học sinh TỰ CHỌN chế độ "Có tên - lớp để nhận hỗ trợ".

Mỗi yêu cầu chỉ gồm: mã trường, họ tên, lớp, LOẠI nguy cơ, mức độ, ngày giờ nhận.
KHÔNG có nội dung tin nhắn, link, tên trang web hay ảnh.
Lưu trong data/ho_tro.json, tự xoá sau 30 ngày; chỉ giáo viên có khoá xem mới đọc được.
"""
import json
import os
import re
import tempfile
import threading
import time
import uuid
from datetime import datetime, timedelta

from privacy_stats import CAT_INFO

KEEP_DAYS = 30
LEVELS = {"khan_cap": "Khẩn cấp", "canh_bao": "Cảnh báo"}
_SCHOOL_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")
_NAME_RE = re.compile(r"^[^\W\d_](?:[^\W\d_]|[ .'-]){1,59}$")
_CLS_RE = re.compile(r"^[0-9A-Za-zÀ-ỹ/._ -]{1,12}$")


class SupportBox:
    def __init__(self, path):
        self.path = path
        self.lock = threading.Lock()
        self.items = []
        self.hits = {}  # chống gửi dồn dập: địa chỉ -> các mốc thời gian
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    self.items = json.load(f)
            except (OSError, ValueError):
                self.items = []
        self._purge()

    def _purge(self):
        cut = (datetime.now() - timedelta(days=KEEP_DAYS)).isoformat(timespec="minutes")
        self.items = [x for x in self.items if x.get("nhan_luc", "") >= cut]

    def _save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(self.path), suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(self.items, f, ensure_ascii=False)
        os.replace(tmp, self.path)

    def limited(self, who, per_hour=20):
        now = time.time()
        q = [t for t in self.hits.get(who, []) if now - t < 3600]
        self.hits[who] = q + [now]
        return len(q) >= per_hour

    @staticmethod
    def validate(d):
        school = str(d.get("school", ""))
        name = " ".join(str(d.get("name", "")).split())
        cls = " ".join(str(d.get("lop", "")).split())
        cat = str(d.get("cat", ""))
        level = str(d.get("level", ""))
        if not _SCHOOL_RE.match(school):
            raise ValueError("Mã trường không hợp lệ")
        if not _NAME_RE.match(name):
            raise ValueError("Họ tên không hợp lệ")
        if not _CLS_RE.match(cls):
            raise ValueError("Lớp không hợp lệ")
        if cat not in CAT_INFO:
            raise ValueError("Loại nguy cơ không hợp lệ")
        if level not in LEVELS:
            raise ValueError("Mức độ không hợp lệ")
        # Chỉ giữ đúng các trường được phép; mọi trường khác (nếu có) bị bỏ
        return {"school": school, "name": name, "lop": cls, "cat": cat, "level": level}

    def add(self, d):
        x = self.validate(d)
        x.update({"id": uuid.uuid4().hex[:10], "nhan_luc": datetime.now().isoformat(timespec="minutes"), "trang_thai": "moi"})
        with self.lock:
            self._purge()
            self.items.append(x)
            self._save()
        return x["id"]

    def mark(self, school, rid, status="da_lien_he"):
        with self.lock:
            for x in self.items:
                if x["id"] == rid and x["school"] == school:
                    x["trang_thai"] = status
            self._save()

    def list(self, school):
        with self.lock:
            self._purge()
            return sorted([x for x in self.items if x["school"] == school], key=lambda x: x["nhan_luc"], reverse=True)


def render(box, school, key=""):
    from html import escape
    from urllib.parse import quote
    kq = ("&key=" + quote(key)) if key else ""
    rows = box.list(school) if school else []
    css = ("body{font:15px system-ui,sans-serif;max-width:980px;margin:20px auto;padding:0 14px;color:#1f2328}"
           "table{width:100%;border-collapse:collapse}td,th{border-bottom:1px solid #e1e4e8;padding:8px;text-align:left;vertical-align:top}"
           ".kc{color:#cf222e;font-weight:700}.cb{color:#bc4c00;font-weight:600}.moi{background:#fff5f5}.done{color:#57606a}"
           "button{border:1px solid #d0d7de;background:#fff;border-radius:8px;padding:5px 10px;cursor:pointer}.note{background:#f6f8fa;border-radius:10px;padding:10px 12px;font-size:14px}")
    head = f"<!doctype html><meta charset=utf-8><title>EduShield - Yêu cầu hỗ trợ</title><style>{css}</style>"
    if not school:
        return head + "<h2>Thiếu mã trường</h2><p>Thêm <code>?school=MA_TRUONG</code> vào địa chỉ.</p>"
    new = sum(x["trang_thai"] == "moi" for x in rows)
    tr = []
    for x in rows:
        lv = "kc" if x["level"] == "khan_cap" else "cb"
        btn = "" if x["trang_thai"] != "moi" else (
            f"<form method=post action='/hotro/xong?school={quote(school)}{kq}' style='margin:0'><input type=hidden name=id value='{escape(x['id'])}'>"
            "<button>✅ Đã liên hệ</button></form>")
        tr.append(f"<tr class='{'moi' if x['trang_thai'] == 'moi' else 'done'}'><td>{escape(x['nhan_luc'].replace('T', ' '))}</td>"
                  f"<td><b>{escape(x['name'])}</b></td><td>{escape(x['lop'])}</td><td>{escape(CAT_INFO[x['cat']]['name'])}</td>"
                  f"<td class='{lv}'>{LEVELS[x['level']]}</td><td>{'Mới' if x['trang_thai'] == 'moi' else 'Đã liên hệ'}</td><td>{btn}</td></tr>")
    body = "".join(tr) or "<tr><td colspan=7>Chưa có yêu cầu nào.</td></tr>"
    return (head + f"<h2>📨 Yêu cầu hỗ trợ · {escape(school)} <small style='color:#57606a'>({new} mới)</small></h2>"
            "<p class=note>Học sinh <b>tự chọn</b> gửi tên, lớp để được hỗ trợ khi gặp cảnh báo. Hệ thống <b>không</b> gửi nội dung tin nhắn, link hay ảnh. "
            f"Dữ liệu tự xoá sau {KEEP_DAYS} ngày. Hãy liên hệ học sinh một cách kín đáo, AI có thể cảnh báo nhầm.</p>"
            "<table><tr><th>Thời gian</th><th>Học sinh</th><th>Lớp</th><th>Loại nguy cơ</th><th>Mức</th><th>Trạng thái</th><th></th></tr>"
            + body + "</table>")

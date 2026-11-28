"""Máy chủ EduShield chạy trên CHÍNH MÁY của bạn (127.0.0.1), phục vụ tiện ích trình duyệt.
Chạy:  python server.py        rồi mở  http://127.0.0.1:8765/demo  để xem trang chat mô phỏng.

Chỉ dùng thư viện chuẩn của Python cho phần web, không cần cài thêm.
Máy chủ chỉ nhận văn bản ĐÃ CHE thông tin cá nhân từ tiện ích.
"""
import hashlib
import hmac
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "src"))

from llm_client import llm_available
from dashboard import render as render_dashboard
from pipeline import EduShield
from privacy_stats import Aggregator, validate_packet
from ho_tro import SupportBox, render as render_support

HOST, PORT = "127.0.0.1", 8765
if "--lan" in sys.argv:  # cho điện thoại cùng Wi-Fi truy cập (chỉ dùng khi thử nghiệm với dữ liệu mô phỏng)
    HOST = "0.0.0.0"
MIME = {".css": "text/css; charset=utf-8", ".html": "text/html; charset=utf-8", ".js": "application/javascript; charset=utf-8", ".png": "image/png",
        ".webmanifest": "application/manifest+json", ".json": "application/json"}
CORS_PATHS = ("/thongke", "/blocklist", "/health", "/hotro")  # chỉ các đường này nhận yêu cầu từ trang web khác (app đặt ở nơi khác)
OVERRIDES_FILE = os.path.join(ROOT, "data", "blocklist_overrides.json")
# Khoá xem thống kê: đặt biến môi trường EDUSHIELD_VIEW_KEY thì /truong và /api/thongke phải kèm ?key=...
VIEW_KEY = os.environ.get("EDUSHIELD_VIEW_KEY", "")
# Chỉ cho các trang web này gửi dữ liệu về (vd https://tenban.github.io). Bỏ trống = cho mọi nơi (chỉ dùng khi thử).
ALLOW_ORIGIN = os.environ.get("EDUSHIELD_ALLOW_ORIGIN", "*")


def load_overrides():
    """Người kiểm duyệt (giáo viên/quản trị) có thể cho phép hoặc chặn tay một tên miền."""
    try:
        with open(OVERRIDES_FILE, encoding="utf-8") as f:
            o = json.load(f)
        return {"allow": [str(x).lower() for x in o.get("allow", [])], "deny": [str(x).lower() for x in o.get("deny", [])]}
    except (OSError, ValueError):
        return {"allow": [], "deny": []}
MAX_BODY = 20_000

print("Đang khởi động EduShield (huấn luyện mô hình, nạp đồ thị mô phỏng)...")
SYSTEM = EduShield(demo_graph=True)
DEMO_DOMAIN = SYSTEM.demo_truth["campaign_domains"][0][0]
# Thống kê ẩn danh: chỉ lưu TỔNG theo trường/khối/ngày
STATS = Aggregator(os.path.join(ROOT, "data", "thongke.json"))
# Yêu cầu hỗ trợ có tên - lớp (chỉ khi học sinh tự chọn); tự xoá sau 30 ngày
SUPPORT = SupportBox(os.path.join(ROOT, "data", "ho_tro.json"))


def demo_page():
    with open(os.path.join(ROOT, "extension", "demo_chat.html"), encoding="utf-8") as f:
        return f.read().replace("{{DEMO_DOMAIN}}", DEMO_DOMAIN)


def moderation_page():
    """Trang CHỈ ĐỌC cho người kiểm duyệt: vì sao một tên miền bị chặn, để con người xem lại (AI chỉ đề xuất)."""
    from html import escape
    ov = load_overrides()
    rows = []
    for d in sorted(SYSTEM.graph.risky_domains(overrides=ov)):
        ev = SYSTEM.graph.domain_evidence(d)
        rows.append(f"<tr><td>{escape(d)}</td><td>{ev['accounts']}</td><td>{ev['scam_reports']}</td></tr>")
    return ("<!doctype html><meta charset=utf-8><title>Kiểm duyệt danh sách chặn</title>"
            "<style>body{font:15px system-ui;max-width:760px;margin:20px auto;padding:0 12px}td,th{border-bottom:1px solid #ddd;padding:6px;text-align:left}</style>"
            "<h2>Danh sách tên miền đang bị cảnh báo</h2>"
            "<p>AI chỉ <b>đề xuất</b>. Người kiểm duyệt quyết định bằng cách sửa tệp <code>data/blocklist_overrides.json</code> "
            '(<code>{"allow":["ten-mien-an-toan.vn"],"deny":[]}</code>). Một tên miền chỉ bị cảnh báo khi có ít nhất '
            f"{3} tài khoản khác nhau báo cáo.</p><table><tr><th>Tên miền</th><th>Số tài khoản liên quan</th><th>Số báo cáo lừa đảo</th></tr>"
            + "".join(rows) + "</table>")


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, data, ctype="application/json; charset=utf-8"):
        body = data if isinstance(data, bytes) else (json.dumps(data, ensure_ascii=False).encode() if not isinstance(data, str) else data.encode())
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if self.path.split("?")[0] in CORS_PATHS:
            self.send_header("Access-Control-Allow-Origin", ALLOW_ORIGIN)
        self.end_headers()
        self.wfile.write(body)

    def _json(self):
        n = int(self.headers.get("Content-Length", 0))
        if n <= 0 or n > MAX_BODY:
            raise ValueError("Kích thước dữ liệu không hợp lệ")
        return json.loads(self.rfile.read(n).decode("utf-8"))

    def log_message(self, fmt, *args):  # không ghi nội dung vào nhật ký, chỉ ghi đường dẫn
        sys.stderr.write(f"[EduShield] {self.command} {self.path.split('?')[0]}\n")

    def _can_view(self, q):
        """Có khoá xem thì phải đúng khoá; chưa đặt khoá thì chỉ xem được trên chính máy chủ (127.0.0.1)."""
        if VIEW_KEY:
            return hmac.compare_digest(q.get("key", ""), VIEW_KEY)
        return self.client_address[0] in ("127.0.0.1", "::1")

    def do_OPTIONS(self):
        self.send_response(204)
        if self.path.split("?")[0] in CORS_PATHS:
            self.send_header("Access-Control-Allow-Origin", ALLOW_ORIGIN)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _static(self, p):
        rel = p[len("/app/"):] or "index.html"
        full = os.path.normpath(os.path.join(ROOT, "mobile", rel))
        if not full.startswith(os.path.join(ROOT, "mobile")) or not os.path.isfile(full):
            self._send(404, {"error": "không tìm thấy"})
            return
        with open(full, "rb") as f:
            self._send(200, f.read(), MIME.get(os.path.splitext(full)[1], "application/octet-stream"))

    def do_GET(self):
        from urllib.parse import parse_qs, urlparse
        u = urlparse(self.path)
        p, q = u.path, {k: v[0] for k, v in parse_qs(u.query).items()}
        if p == "/health":
            self._send(200, {"ok": True, "llm": llm_available()})
        elif p == "/blocklist":
            hashes = sorted(hashlib.sha256(d.encode()).hexdigest() for d in SYSTEM.graph.risky_domains(overrides=load_overrides()))
            self._send(200, {"hashes": hashes})
        elif p == "/app" or p.startswith("/app/"):
            self._static(p if p != "/app" else "/app/")
        elif p == "/kiemduyet":
            self._send(200, moderation_page(), "text/html; charset=utf-8")
        elif p in ("/truong", "/api/thongke") and VIEW_KEY and not hmac.compare_digest(q.get("key", ""), VIEW_KEY):
            self._send(403, "<meta charset=utf-8><p>Cần khoá xem: thêm <code>?key=...</code> vào địa chỉ.</p>" if p == "/truong"
                       else {"error": "cần khoá xem"}, "text/html; charset=utf-8" if p == "/truong" else "application/json; charset=utf-8")
        elif p == "/hotro":
            if not self._can_view(q):
                self._send(403, "<meta charset=utf-8><p>Cần khoá xem: thêm <code>&key=...</code> vào địa chỉ.</p>", "text/html; charset=utf-8")
            else:
                self._send(200, render_support(SUPPORT, q.get("school", ""), q.get("key", "") if VIEW_KEY else ""), "text/html; charset=utf-8")
        elif p == "/truong":
            grade = q.get("grade", "all")
            self._send(200, render_dashboard(STATS, q.get("school"), q.get("group", "week") if q.get("group") in ("day", "week") else "week",
                                             None, key=q.get("key", "") if VIEW_KEY else ""), "text/html; charset=utf-8")
        elif p == "/api/thongke":
            grade = q.get("grade", "all")
            self._send(200, STATS.report(q.get("school", ""), q.get("group", "week"), None))  # chỉ số liệu toàn trường
        elif p in ("/", "/demo"):
            self._send(200, demo_page(), "text/html; charset=utf-8")
        else:
            self._send(404, {"error": "không tìm thấy"})

    def do_POST(self):
        p = self.path.split("?")[0]
        if p == "/hotro/xong":  # giáo viên đánh dấu đã liên hệ (form trên trang /hotro)
            from urllib.parse import parse_qs, urlparse, quote
            q = {k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()}
            n = int(self.headers.get("Content-Length", 0) or 0)
            form = {k: v[0] for k, v in parse_qs(self.rfile.read(min(n, 2000)).decode("utf-8", "ignore")).items()}
            if not self._can_view(q):
                self._send(403, {"error": "cần khoá xem"})
                return
            SUPPORT.mark(q.get("school", ""), form.get("id", ""))
            self.send_response(303)
            self.send_header("Location", "/hotro?school=" + quote(q.get("school", "")) + ("&key=" + quote(q.get("key", "")) if VIEW_KEY else ""))
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        try:
            data = self._json()
            if p == "/thongke":
                STATS.add(validate_packet(data))  # cộng dồn rồi bỏ gói
                self._send(200, {"ok": True})
                return
            if p == "/hotro":
                if SUPPORT.limited(self.client_address[0]):
                    self._send(429, {"error": "Gửi quá nhiều, thử lại sau"})
                    return
                self._send(200, {"ok": True, "id": SUPPORT.add(data)})
                return
            masked = str(data.get("masked", ""))[:2000]
            domains = [str(d)[:253] for d in data.get("domains", [])][:20]
            if not masked.strip():
                raise ValueError("Thiếu nội dung")
            if p == "/analyze":
                self._send(200, SYSTEM.check_masked(masked, domains))
            elif p == "/report":
                SYSTEM.report_masked(masked, domains, str(data.get("label", "")))
                self._send(200, {"ok": True, "so_bao_cao": len(SYSTEM.graph.reports)})
            else:
                self._send(404, {"error": "không tìm thấy"})
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            self._send(400, {"error": str(e)})


if __name__ == "__main__":
    if HOST != "127.0.0.1":
        print("CẢNH BÁO: đang mở cho cả mạng Wi-Fi (--lan). Chỉ dùng khi thử nghiệm với dữ liệu mô phỏng, không dùng với dữ liệu học sinh thật.")
    print(f"EduShield đang chạy tại http://{HOST}:{PORT}")
    print(f"  Ứng dụng điện thoại (PWA): http://127.0.0.1:{PORT}/app/")
    print(f"  Kiểm duyệt danh sách chặn: http://127.0.0.1:{PORT}/kiemduyet")
    print(f"  Trang chat mô phỏng: http://{HOST}:{PORT}/demo")
    print(f"  Thống kê nhà trường: http://{HOST}:{PORT}/truong")
    print(f"  Yêu cầu hỗ trợ có tên - lớp: http://{HOST}:{PORT}/hotro?school=MA_TRUONG")
    print("Khoá xem thống kê:", "ĐANG BẬT (thêm ?key=... vào /truong)" if VIEW_KEY else "chưa đặt (EDUSHIELD_VIEW_KEY) - chỉ dùng khi thử trên máy mình")
    print("LLM:", "đang bật" if llm_available() else "chưa có GEMINI_API_KEY, dùng mô hình cục bộ")
    print("Bấm Ctrl + C để dừng.")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

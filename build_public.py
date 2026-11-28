"""Tạo BẢN CÔNG KHAI KHÔNG THU THẬP trong thư mục public_app/ để đưa lên GitHub Pages.
Bản này: không gửi dữ liệu đi đâu (collect=false) và bị trình duyệt khoá bằng CSP connect-src 'none'.
Chạy:  python build_public.py
Bản CÓ THU THẬP (chỉ khi đã được nhà trường + phụ huynh đồng ý, máy chủ có HTTPS):
       python build_public.py --collect --server https://may-chu.example.com --school THPT_DEMO
"""
import argparse
import json
import os
import re
import shutil

ap = argparse.ArgumentParser()
ap.add_argument("--collect", action="store_true")
ap.add_argument("--server", default="")
ap.add_argument("--school", default="")
A = ap.parse_args()
if A.collect and not (A.server.startswith("https://") and A.school):
    raise SystemExit("Bản thu thập cần --server https://... (bắt buộc HTTPS) và --school MA_TRUONG")
ROOT = os.path.dirname(os.path.abspath(__file__))
SRC, DST = os.path.join(ROOT, "mobile"), os.path.join(ROOT, "public_app")
if os.path.isdir(DST):
    shutil.rmtree(DST)
shutil.copytree(SRC, DST)
with open(os.path.join(DST, "config.js"), "w", encoding="utf-8") as f:
    if A.collect:
        f.write('globalThis.EDUSHIELD_CONFIG = { collect: true, school: %s, server: %s };\n' % (json.dumps(A.school), json.dumps(A.server.rstrip("/"))))
    else:
        f.write("globalThis.EDUSHIELD_CONFIG = { collect: false };\n")
conn = ("'self' " + A.server.rstrip("/")) if A.collect else "'none'"
csp = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
       f"connect-src {conn}; form-action 'none'; base-uri 'self'")
p = os.path.join(DST, "index.html")
html = open(p, encoding="utf-8").read()
html = html.replace('<meta charset="utf-8">', f'<meta charset="utf-8">\n<meta http-equiv="Content-Security-Policy" content="{csp}">', 1)
open(p, "w", encoding="utf-8").write(html)
# Trang hướng dẫn cài đặt cũng được khoá CSP như trang chính
gp = os.path.join(DST, "cai-dat.html")
g = open(gp, encoding="utf-8").read().replace('<meta charset="utf-8">', f'<meta charset="utf-8">\n<meta http-equiv="Content-Security-Policy" content="{csp.replace("form-action \'none\'", "form-action \'none\'")}">', 1)
open(gp, "w", encoding="utf-8").write(g)
# Gói tiện ích cho máy tính (giải nén rồi "Tải tiện ích đã giải nén"). Dùng extension/config.js do người triển khai đặt.
import zipfile
EXT = os.path.join(ROOT, "extension")
with zipfile.ZipFile(os.path.join(DST, "EduShield_Extension.zip"), "w", zipfile.ZIP_DEFLATED) as z:
    for fn in sorted(os.listdir(EXT)):
        if fn in ("demo_chat.html",) or fn.startswith("."):
            continue
        if fn == "config.js" and A.collect:  # bản thu thập: tự ghi cùng mã trường + máy chủ với app, khỏi sửa tay
            z.writestr("EduShield_Extension/config.js", "globalThis.EDUSHIELD_DEPLOY = { school: %s, server: %s };\n" % (json.dumps(A.school), json.dumps(A.server.rstrip("/"))))
            continue
        if fn == "manifest.json" and A.collect:  # cấp sẵn quyền kết nối tới máy chủ của trường, khỏi phải bấm "Cho phép"
            from urllib.parse import urlparse
            man = json.load(open(os.path.join(EXT, fn), encoding="utf-8"))
            u = urlparse(A.server)
            origin = f"{u.scheme}://{u.netloc}/*"
            if origin not in man["host_permissions"]:
                man["host_permissions"].append(origin)
            z.writestr("EduShield_Extension/manifest.json", json.dumps(man, ensure_ascii=False, indent=2))
            continue
        z.write(os.path.join(EXT, fn), "EduShield_Extension/" + fn)
print("Đã đóng gói tiện ích: public_app/EduShield_Extension.zip")
if A.collect:
    # Ghi cả vào thư mục extension/ gốc, để ai nạp tiện ích từ thư mục này cũng gửi đúng máy chủ
    with open(os.path.join(EXT, "config.js"), "w", encoding="utf-8") as f:
        f.write("// Do build_public.py --collect ghi. Muốn quay lại máy chủ trên máy mình: server: \"http://127.0.0.1:8765\"\n")
        f.write("globalThis.EDUSHIELD_DEPLOY = { school: %s, server: %s };\n" % (json.dumps(A.school), json.dumps(A.server.rstrip("/"))))
    print("Đã cập nhật extension/config.js ->", A.server.rstrip("/"), "| Nhớ bấm ⟳ Tải lại tiện ích trong chrome://extensions")
print("Đã tạo", DST, f"(collect={A.collect}, CSP connect-src {conn}). Tải NỘI DUNG thư mục này lên GitHub Pages.")
if A.collect:
    print("Gói tiện ích đã được ghi sẵn cùng mã trường và máy chủ. Chạy server với EDUSHIELD_ALLOW_ORIGIN=https://TEN.github.io và EDUSHIELD_VIEW_KEY=...")

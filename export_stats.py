"""Xuất THỐNG KÊ TỔNG HỢP (đã ẩn danh) thành trang tĩnh để đưa lên GitHub.

Chạy:  python export_stats.py                      -> thư mục thongke_github/
       python export_stats.py --school THPT_DEMO    -> chỉ một trường
       python export_stats.py --push               -> xuất xong tự git add/commit/push (thư mục là kho git riêng, hoặc nằm trong kho dự án, ví dụ trên Codespaces)

Chỉ xuất những gì trang /truong đã hiển thị: số ƯỚC LƯỢNG theo tuần/ngày, đã trộn nhiễu,
kỳ nào dưới K_MIN gói thì bị ẩn. KHÔNG xuất tệp data/thongke.json gốc (có ô nhỏ theo ngày, theo khối).
Trang GitHub Pages là CÔNG KHAI: chỉ đưa lên khi nhà trường đồng ý, hoặc khi dữ liệu là mô phỏng.
"""
import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from urllib.parse import quote

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "src"))
from dashboard import render  # noqa: E402
from privacy_stats import CAT_CODES, CAT_INFO, K_MIN, Aggregator  # noqa: E402

SAFE = re.compile(r"^[A-Za-z0-9_]{2,30}$")


def static_links(page, school):
    """Đổi đường dẫn động /truong?... thành tệp tĩnh; bỏ bộ lọc theo khối (bản này không thu khối)."""
    s = quote(school)
    page = re.sub(r"(?: &nbsp; )?<a class='[^']*' href='/truong\?[^']*'>(?:Toàn trường|Khối \d+)</a>", "", page)
    page = page.replace(f"href='/truong?school={s}&group=day'", "href='ngay.html'")
    page = page.replace(f"href='/truong?school={s}&group=week'", "href='index.html'")
    return page


def banner(when, school=None):
    back = "<a href='../index.html'>← Danh sách trường</a> · " if school else ""
    return (f"<div class='card' style='background:#fff8e1'>{back}📸 <b>Bản chụp tĩnh</b> lúc {html.escape(when)}. "
            f"Chỉ gồm số ước lượng đã trộn nhiễu, kỳ dưới {K_MIN} gói bị ẩn. Không có nội dung tin nhắn hay danh tính học sinh.</div>")


def clean_rows(rows):
    out = []
    for r in rows:
        if r["hidden"]:
            out.append({"period": r["period"], "hidden": True, "n": f"<{K_MIN}"})
        else:
            out.append({"period": r["period"], "n": r["n"],
                        "cats": {c: {k: round(v, 4) for k, v in r["cats"][c].items()} for c in CAT_CODES}})
    return out


def markdown(school, week, when):
    """README.md để xem ngay trên github.com (kể cả kho riêng tư, không cần GitHub Pages)."""
    top = [c for c in CAT_CODES if c in CAT_INFO][:8]
    L = [f"# 🛡️ EduShield · Thống kê {school}", "",
         f"Bản chụp lúc {when}. Số liệu là **ước lượng** (% số lượt-ngày có loại nguy cơ), đã trộn nhiễu; kỳ dưới {K_MIN} gói bị ẩn.", "",
         "| Tuần bắt đầu | Số gói | " + " | ".join(CAT_INFO[c]["name"] for c in top) + " |",
         "|---|---|" + "---|" * len(top)]
    for r in week:
        if r.get("hidden"):
            L.append(f"| {r['period']} | {r['n']} | " + " | ".join("ẩn" for _ in top) + " |")
        else:
            L.append(f"| {r['period']} | {r['n']} | " + " | ".join(f"{r['cats'][c]['pct'] * 100:.1f}%" for c in top) + " |")
    L += ["", "Bảng đầy đủ: mở `index.html` (theo tuần) hoặc `ngay.html` (theo ngày), số liệu máy đọc: `thongke.json`."]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(ROOT, "data", "thongke.json"))
    ap.add_argument("--out", default=os.path.join(ROOT, "thongke_github"))
    ap.add_argument("--school", default="")
    ap.add_argument("--push", action="store_true", help="git add/commit/push trong thư mục --out")
    a = ap.parse_args()
    agg = Aggregator(a.data)
    schools = [a.school] if a.school else agg.schools()
    schools = [s for s in schools if SAFE.match(s)]
    if not schools:
        raise SystemExit("Chưa có dữ liệu. Chạy server.py rồi để học sinh gửi, hoặc chạy python simulate_school.py để có dữ liệu mô phỏng.")
    when = datetime.now().strftime("%d/%m/%Y %H:%M")
    os.makedirs(a.out, exist_ok=True)
    for s in schools:  # chỉ xoá thư mục trường do script này tạo, giữ nguyên .git
        d = os.path.join(a.out, s)
        if os.path.isdir(d):
            shutil.rmtree(d)
        os.makedirs(d)
        for group, fn in (("week", "index.html"), ("day", "ngay.html")):
            page = static_links(render(agg, s, group, None), s)
            page = page.replace("</h1>", "</h1>" + banner(when, s), 1)
            open(os.path.join(d, fn), "w", encoding="utf-8").write(page)
        week, day = clean_rows(agg.report(s, "week")), clean_rows(agg.report(s, "day"))
        json.dump({"school": s, "exported": when, "k_min": K_MIN, "week": week, "day": day},
                  open(os.path.join(d, "thongke.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        open(os.path.join(d, "README.md"), "w", encoding="utf-8").write(markdown(s, week, when))
        print(f"  {s}: {len(week)} tuần, {sum(1 for r in week if r.get('hidden'))} tuần bị ẩn")
    idx = render(agg, None).replace("href='/truong?school=", "href='")
    for s in agg.schools():
        idx = idx.replace(f"href='{quote(s)}'", f"href='{quote(s)}/index.html'")
    idx = idx.replace("</h1>", "</h1>" + banner(when), 1)
    open(os.path.join(a.out, "index.html"), "w", encoding="utf-8").write(idx)
    open(os.path.join(a.out, ".nojekyll"), "w").close()
    print("Đã xuất vào", a.out, "- tải NỘI DUNG thư mục này lên GitHub (kho riêng hoặc GitHub Pages).")
    if a.push:
        # Thư mục có thể là kho git riêng, hoặc nằm trong kho dự án (ví dụ khi chạy trong GitHub Codespaces)
        inside = subprocess.run(["git", "-C", a.out, "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True)
        if inside.returncode != 0:
            raise SystemExit("Thư mục chưa nằm trong kho git. Làm một lần: cd thongke_github, git init, git remote add origin <link kho>.")
        git = lambda *x: subprocess.run(["git", "-C", a.out, *x], check=False)
        git("add", "-A", ".")
        git("commit", "-m", f"Cập nhật thống kê {when}")
        git("push")


if __name__ == "__main__":
    main()

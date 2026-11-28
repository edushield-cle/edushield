"""Tạo mã QR và áp phích A4 để học sinh quét cài EduShield.

Chạy:   python build_qr.py https://TEN-BAN.github.io/TEN-KHO/
Kết quả (thư mục qr/):
  - qr_cai_dat.png     mã QR trỏ tới trang hướng dẫn cài (cai-dat.html), nên in/ chiếu cho học sinh
  - qr_app.png         mã QR mở thẳng app
  - ap_phich_A4.png    áp phích A4 có QR, cách cài, cách dùng, việc cần làm khi gặp nguy cơ (in dán ở lớp)

Chỉ cần đường link HTTPS của thư mục public_app sau khi đã đưa lên GitHub Pages.
Không cần cài thêm thư viện để tạo mã QR. Áp phích A4 cần Pillow (thường đã có sẵn cùng matplotlib);
nếu thiếu Pillow, chương trình vẫn tạo hai mã QR và bỏ qua áp phích.
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "qr")


def make_qr(url: str, path: str, box: int = 14):
    """Ghi mã QR (mức sửa lỗi M) ra tệp PNG. Dùng bộ mã hoá có sẵn trong dự án, KHÔNG cần cài thêm thư viện."""
    sys.path.insert(0, os.path.join(ROOT, "src"))
    import qr_mini
    qr_mini.save_png(qr_mini.encode(url), path, box=box, border=4)
    return "qr_mini (có sẵn, không cần cài thêm)"


def find_font(bold=False):
    names = (["segoeuib.ttf", "arialbd.ttf", "Arial Bold.ttf", "Inter-Bold.otf", "DejaVuSans-Bold.ttf"] if bold
             else ["segoeui.ttf", "arial.ttf", "Arial.ttf", "Inter-Regular.otf", "DejaVuSans.ttf"])
    dirs = ["C:/Windows/Fonts", "/Library/Fonts", "/System/Library/Fonts/Supplemental", "/usr/share/fonts/opentype/inter",
            "/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/truetype/liberation"]
    for n in names:
        for d in dirs:
            p = os.path.join(d, n)
            if os.path.exists(p):
                return p
    return None


def poster(guide_url: str, qr_path: str, out_path: str):
    """Áp phích A4 (300 dpi): mã QR, cách cài, cách dùng, việc cần làm khi gặp nguy cơ, cam kết riêng tư.
    Chỉ vẽ bằng hình và chữ (không dùng emoji) để chạy giống nhau trên Windows, macOS, Linux."""
    from PIL import Image, ImageDraw, ImageFont
    W, H = 2480, 3508
    BLUE, INDIGO, INK, MUTED = (31, 111, 235), (88, 64, 214), (31, 35, 40), (89, 99, 110)
    GREEN, GREEN_BG, RED, RED_BG, ORANGE, ORANGE_BG = (17, 99, 41), (232, 246, 236), (209, 36, 47), (253, 236, 236), (191, 87, 0), (255, 241, 220)
    fb, fr = find_font(True), find_font(False)
    F = lambda p, s: ImageFont.truetype(p, s) if p else ImageFont.load_default()
    img = Image.new("RGB", (W, H), (246, 248, 252))
    d = ImageDraw.Draw(img)

    def wrap(text, font, width):
        out, line = [], ""
        for w in text.split():
            t = (line + " " + w).strip()
            if d.textlength(t, font=font) <= width:
                line = t
            else:
                out.append(line); line = w
        out.append(line)
        return out

    def para(x, y, text, font, width, fill, gap=1.32):
        for ln in wrap(text, font, width):
            d.text((x, y), ln, font=font, fill=fill); y += int(font.size * gap)
        return y

    def shield(cx, cy, r, fill, inner=None):
        pts = [(cx, cy - r), (cx + r * 0.85, cy - r * 0.62), (cx + r * 0.78, cy + r * 0.18), (cx, cy + r),
               (cx - r * 0.78, cy + r * 0.18), (cx - r * 0.85, cy - r * 0.62)]
        d.polygon(pts, fill=fill)
        if inner:  # dấu tích
            d.line([(cx - r * 0.38, cy + r * 0.02), (cx - r * 0.08, cy + r * 0.32), (cx + r * 0.42, cy - r * 0.3)], fill=inner, width=int(r * 0.16), joint="curve")

    def badge(cx, cy, n, color):
        d.ellipse([cx - 62, cy - 62, cx + 62, cy + 62], fill=color)
        d.text((cx, cy + 2), str(n), font=F(fb, 78), fill="white", anchor="mm")

    # ---- đầu trang: nền chuyển màu ----
    top = 560
    for yy in range(top):
        t = yy / top
        d.line([(0, yy), (W, yy)], fill=tuple(int(BLUE[k] * (1 - t) + INDIGO[k] * t) for k in range(3)))
    for cx, cy, r in ((2330, 90, 230),):  # bong bóng trang trí
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255), width=6)
    shield(320, 270, 160, (255, 255, 255), BLUE)
    d.text((540, 150), "EduShield AI", font=F(fb, 180), fill="white")
    d.text((546, 370), "Phòng vệ chủ động trước bắt nạt mạng và lừa đảo", font=F(fr, 66), fill=(230, 237, 255))
    d.text((546, 460), "Cảnh báo sớm  ·  Phân tích ngay trên máy  ·  Bạn là người quyết định", font=F(fr, 52), fill=(200, 214, 255))

    def card(x0, y0, x1, y1, fill="white", outline=(222, 227, 235)):
        d.rounded_rectangle([x0 + 8, y0 + 12, x1 + 8, y1 + 12], radius=48, fill=(226, 231, 240))
        d.rounded_rectangle([x0, y0, x1, y1], radius=48, fill=fill, outline=outline, width=3)

    # ---- khối QR + cách cài ----
    y0, QH = 640, 1020
    card(120, y0, 1250, y0 + QH)
    d.rounded_rectangle([340, y0 + 40, 1030, y0 + 140], radius=50, fill=BLUE)
    d.text((685, y0 + 92), "QUÉT ĐỂ CÀI", font=F(fb, 64), fill="white", anchor="mm")
    qr = Image.open(qr_path).convert("RGB").resize((740, 740), Image.NEAREST)
    img.paste(qr, (315, y0 + 160))
    d.text((685, y0 + 935), "Dùng camera điện thoại", font=F(fb, 54), fill=INK, anchor="mm")
    us = 40  # thu nhỏ chữ cho vừa khung để in ĐỦ đường link (học sinh gõ tay được nếu không quét)
    while us > 24 and d.textlength(guide_url, font=F(fr, us)) > 1040:
        us -= 2
    u = guide_url if d.textlength(guide_url, font=F(fr, us)) <= 1040 else guide_url[:60] + "…"
    d.text((685, y0 + 985), u, font=F(fr, us), fill=BLUE, anchor="mm")

    card(1330, y0, 2360, y0 + QH)
    d.text((1400, y0 + 50), "Cài trong 1 phút", font=F(fb, 80), fill=INK)
    yy = y0 + 165
    for col, head, lines in ((BLUE, "Điện thoại (app)", ["Quét mã, chọn “Cài app”.", "Android: bấm “Cài app”.", "iPhone: Safari → Chia sẻ → Thêm vào MH chính."]),
                             (INDIGO, "Máy tính (tiện ích)", ["Tải tiện ích từ link, giải nén.", "Bật Chế độ nhà phát triển.", "Bấm “Tải tiện ích đã giải nén”."])):
        d.rounded_rectangle([1400, yy, 1426, yy + 80], radius=12, fill=col)
        d.text((1455, yy + 4), head, font=F(fb, 58), fill=col)
        yy += 100
        for ln in lines:
            d.ellipse([1462, yy + 20, 1480, yy + 38], fill=col)
            yy = para(1505, yy, ln, F(fr, 42), 820, INK, 1.25) + 10
        yy += 40
    d.rounded_rectangle([1400, y0 + QH - 135, 2290, y0 + QH - 40], radius=30, fill=ORANGE_BG)
    d.text((1845, y0 + QH - 88), "Chỉ cài từ mã QR / link do thầy cô chia sẻ", font=F(fb, 44), fill=ORANGE, anchor="mm")

    # ---- cách dùng: 4 bước ----
    y1 = y0 + QH + 60
    d.text((120, y1), "Dùng thế nào?", font=F(fb, 84), fill=INK)
    steps = [(BLUE, "Tự nguyện bắt đầu", "Đọc giới thiệu, tích “Mình tự nguyện dùng”, bấm Bắt đầu."),
             (INDIGO, "Dùng như thường", "Máy tính tự quét Zalo Web, Messenger. Điện thoại: dán hoặc chia sẻ tin vào app."),
             (ORANGE, "Xem cảnh báo", "Bấm “Xem ngay” ở pop-up để biết lý do và việc nên làm."),
             (GREEN, "Góp thống kê", "Tuỳ chọn. Chỉ gửi số ẩn danh đã trộn nhiễu cho trường.")]
    bw, gx = 530, 30
    for k, (col, head, body) in enumerate(steps):
        x = 120 + k * (bw + gx)
        card(x, y1 + 120, x + bw, y1 + 590)
        badge(x + 100, y1 + 210, k + 1, col)
        d.text((x + 45, y1 + 290), head, font=F(fb, 46), fill=col)
        para(x + 45, y1 + 360, body, F(fr, 40), bw - 80, INK, 1.3)

    # ---- khi gặp nguy cơ ----
    y2 = y1 + 650
    d.text((120, y2), "Khi gặp nguy cơ, hãy:", font=F(fb, 84), fill=INK)
    for k, (col, bg, head, items) in enumerate(((RED, RED_BG, "Bị bắt nạt", ["Đừng đáp trả lúc đang bực", "Chụp màn hình làm bằng chứng", "Chặn và báo cáo tài khoản", "Nói với người lớn bạn tin"]),
                                                  (ORANGE, ORANGE_BG, "Nghi lừa đảo", ["Không bấm link lạ", "Không chuyển tiền, đặt cọc", "Không gửi mã OTP, mật khẩu", "Gọi trực tiếp để xác minh"]))):
        x = 120 + k * 1135
        card(x, y2 + 120, x + 1105, y2 + 560, fill=bg, outline=bg)
        d.rounded_rectangle([x, y2 + 120, x + 36, y2 + 560], radius=18, fill=col)
        d.text((x + 90, y2 + 150), head, font=F(fb, 60), fill=col)
        for i, t in enumerate(items):
            cy = y2 + 260 + i * 72
            d.ellipse([x + 95, cy, x + 135, cy + 40], fill=col)
            d.line([(x + 104, cy + 21), (x + 114, cy + 31), (x + 128, cy + 11)], fill="white", width=7)
            d.text((x + 165, cy - 6), t, font=F(fr, 48), fill=INK)

    # ---- riêng tư + đường dây nóng ----
    y3 = y2 + 620
    card(120, y3, 1640, y3 + 400, fill=GREEN_BG, outline=GREEN_BG)
    shield(230, y3 + 100, 60, GREEN, GREEN_BG)
    d.text((320, y3 + 62), "Riêng tư của bạn", font=F(fb, 60), fill=GREEN)
    for i, t in enumerate(["Phân tích ngay trên máy, không lưu và không gửi tin nhắn.", "Nhà trường không thấy nội dung, không biết ai là ai.", "AI có thể sai: EduShield chỉ cảnh báo, bạn quyết định."]):
        d.text((190, y3 + 185 + i * 66), "•  " + t, font=F(fr, 44), fill=GREEN)
    card(1700, y3, 2360, y3 + 400, fill=RED, outline=RED)
    d.text((2030, y3 + 85), "Cần giúp ngay?", font=F(fb, 56), fill="white", anchor="mm")
    d.text((2030, y3 + 215), "111", font=F(fb, 160), fill="white", anchor="mm")
    d.text((2030, y3 + 335), "Miễn phí · 24/7", font=F(fr, 46), fill=(255, 225, 228), anchor="mm")

    d.text((W // 2, H - 70), "EduShield AI · Nguyên mẫu nghiên cứu Khoa học kỹ thuật · Tự nguyện sử dụng", font=F(fr, 40), fill=MUTED, anchor="mm")
    img.save(out_path)


def main():
    if len(sys.argv) < 2:
        sys.exit("Cách dùng:  python build_qr.py https://TEN-BAN.github.io/TEN-KHO/")
    base = sys.argv[1].strip()
    if not base.lower().startswith("https://"):
        sys.exit("Đường link phải bắt đầu bằng https:// (điện thoại chỉ cài được app qua HTTPS).")
    if not base.endswith("/"):
        base += "/"
    os.makedirs(OUT, exist_ok=True)
    guide, app = base + "cai-dat.html", base
    lib = make_qr(guide, os.path.join(OUT, "qr_cai_dat.png"))
    make_qr(app, os.path.join(OUT, "qr_app.png"))
    try:
        poster(guide, os.path.join(OUT, "qr_cai_dat.png"), os.path.join(OUT, "ap_phich_A4.png"))
        made_poster = True
    except ImportError:
        made_poster = False
        print("(Chưa có Pillow nên chưa tạo áp phích. Chạy: py -3.15 -m pip install pillow)")
    print(f"Đã tạo (thư viện: {lib}) trong {OUT}:")
    print("  qr_cai_dat.png  ->", guide, "(khuyên dùng: học sinh chọn app hoặc tiện ích)")
    print("  qr_app.png      ->", app)
    if made_poster:
        print("  ap_phich_A4.png  (in dán ở lớp)")


if __name__ == "__main__":
    main()

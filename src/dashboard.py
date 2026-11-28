"""Trang thống kê cho nhà trường (HTML thuần, không cần Internet hay thư viện ngoài)."""
import html
from urllib.parse import quote

from privacy_stats import CAT_CODES, CAT_INFO, EPSILON, K_MIN, p_keep

CSS = """
*{box-sizing:border-box}body{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;background:#f6f8fa;color:#1f2328}
.wrap{max-width:1050px;margin:0 auto;padding:18px}
h1{margin:0 0 4px;font-size:22px}h2{font-size:17px;margin:0 0 10px}
.sub{color:#57606a;font-size:13px}
.card{background:#fff;border-radius:12px;padding:16px;margin:14px 0;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.row{display:flex;gap:12px;flex-wrap:wrap}.kpi{flex:1;min-width:180px;background:#fff;border-radius:12px;padding:14px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.kpi b{font-size:26px;display:block}.kpi span{font-size:13px;color:#57606a}
.filters a{display:inline-block;padding:5px 11px;border-radius:16px;border:1px solid #d0d7de;margin:2px;text-decoration:none;color:#1f2328;font-size:13px;background:#fff}
.filters a.on{background:#1f6feb;color:#fff;border-color:#1f6feb}
.bar{display:grid;grid-template-columns:240px 1fr 120px;gap:10px;align-items:center;font-size:13.5px;margin:6px 0}
.track{position:relative;height:16px;background:#eef1f4;border-radius:4px}
.fill{position:absolute;left:0;top:0;bottom:0;border-radius:4px}
.ci{position:absolute;top:-3px;bottom:-3px;border-left:2px solid #333;border-right:2px solid #333;opacity:.45}
.ld{background:#e85d04}.bn{background:#8250df}.hv{background:#0e7490}
table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:6px 8px;border-bottom:1px solid #eee;text-align:right}th:first-child,td:first-child{text-align:left}
.topic{border-left:4px solid #1a7f37;padding:8px 12px;margin:8px 0;background:#f0fff4;border-radius:6px;font-size:14px}
.priv{font-size:13px;color:#57606a;line-height:1.55}
.muted{color:#8c959f}
"""


def _pct(x):
    return f"{100 * x:.1f}%"


def _period_label(p, group):
    y, m, d = p.split("-")
    return f"{d}/{m}" if group == "day" else f"Tuần từ {d}/{m}"


def _line_chart(rows, group):
    vis = [r for r in rows if not r["hidden"]]
    if len(vis) < 2:
        return "<p class='muted'>Cần ít nhất 2 kỳ đủ dữ liệu để vẽ xu hướng.</p>"
    W, H, L, B = 900, 230, 46, 34
    ymax = max(max(r["cats"][c]["pct_hi"] for c in ("lua_dao_bat_ky", "bat_nat_bat_ky")) for r in vis)
    ymax = max(0.05, round(ymax * 1.15 + 0.005, 2))
    xs = lambda i: L + i * (W - L - 10) / (len(vis) - 1)
    ys = lambda v: H - B - v / ymax * (H - B - 10)
    parts = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Xu hướng tỷ lệ học sinh gặp nguy cơ">']
    for k in range(5):
        v = ymax * k / 4
        parts.append(f'<line x1="{L}" x2="{W-10}" y1="{ys(v):.1f}" y2="{ys(v):.1f}" stroke="#eee"/>'
                     f'<text x="{L-6}" y="{ys(v)+4:.1f}" font-size="11" text-anchor="end" fill="#57606a">{100*v:.0f}%</text>')
    step = max(1, len(vis) // 10)
    for i, r in enumerate(vis):
        if i % step == 0 or i == len(vis) - 1:
            parts.append(f'<text x="{xs(i):.1f}" y="{H-12}" font-size="11" text-anchor="middle" fill="#57606a">{_period_label(r["period"], "day").split()[-1]}</text>')
    for code, color, name in (("lua_dao_bat_ky", "#e85d04", "Lừa đảo"), ("bat_nat_bat_ky", "#8250df", "Bắt nạt")):
        band = " ".join(f"{xs(i):.1f},{ys(r['cats'][code]['pct_hi']):.1f}" for i, r in enumerate(vis))
        band += " " + " ".join(f"{xs(i):.1f},{ys(r['cats'][code]['pct_lo']):.1f}" for i, r in reversed(list(enumerate(vis))))
        parts.append(f'<polygon points="{band}" fill="{color}" opacity=".12"/>')
        line = " ".join(f"{xs(i):.1f},{ys(r['cats'][code]['pct']):.1f}" for i, r in enumerate(vis))
        parts.append(f'<polyline points="{line}" fill="none" stroke="{color}" stroke-width="2.5"/>')
        for i, r in enumerate(vis):
            parts.append(f'<circle cx="{xs(i):.1f}" cy="{ys(r["cats"][code]["pct"]):.1f}" r="3" fill="{color}"><title>{name} {_period_label(r["period"], group)}: {_pct(r["cats"][code]["pct"])}</title></circle>')
    parts.append(f'<text x="{L+8}" y="16" font-size="12" fill="#e85d04">● Lừa đảo</text><text x="{L+90}" y="16" font-size="12" fill="#8250df">● Bắt nạt</text>'
                 f'<text x="{L+170}" y="16" font-size="11" fill="#8c959f">Vùng mờ: khoảng tin cậy 95%</text></svg>')
    return "".join(parts)


def _bars(row):
    subs = [c for c in CAT_CODES if not c.endswith("bat_ky")]
    subs.sort(key=lambda c: -row["cats"][c]["pct"])
    mx = max(0.02, max(row["cats"][c]["pct_hi"] for c in subs))
    out = []
    for c in subs:
        e = row["cats"][c]
        cls = {"lua_dao": "ld", "bat_nat": "bn"}.get(CAT_INFO[c]["group"], "hv")
        out.append(
            f'<div class="bar"><div>{html.escape(CAT_INFO[c]["name"])}</div><div class="track">'
            f'<div class="fill {cls}" style="width:{100*e["pct"]/mx:.1f}%"></div>'
            f'<div class="ci" style="left:{100*e["pct_lo"]/mx:.1f}%;width:{100*(e["pct_hi"]-e["pct_lo"])/mx:.1f}%"></div></div>'
            f'<div>{_pct(e["pct"])} <span class="muted">(±{50*(e["pct_hi"]-e["pct_lo"]):.1f})</span></div></div>')
    return "".join(out)


def _topics(rows):
    vis = [r for r in rows if not r["hidden"]]
    if not vis:
        return ""
    cur = vis[-1]
    prev = vis[-2] if len(vis) > 1 else None
    subs = [c for c in CAT_CODES if not c.endswith("bat_ky") and not c.endswith("khac")]
    top = sorted(subs, key=lambda c: -cur["cats"][c]["est"])[:3]
    rising = []
    if prev:
        for c in subs:
            a, b = prev["cats"][c], cur["cats"][c]
            if b["pct_lo"] > a["pct_hi"]:  # tăng rõ rệt: hai khoảng tin cậy không chồng nhau
                rising.append(c)
    out = []
    for c in rising:
        out.append(f'<div class="topic">📈 <b>Tăng rõ rệt so với kỳ trước:</b> {html.escape(CAT_INFO[c]["name"])} '
                   f'({_pct(prev["cats"][c]["pct"])} → {_pct(cur["cats"][c]["pct"])}).<br>Gợi ý: {html.escape(CAT_INFO[c]["topic"])}</div>')
    for c in top:
        if c in rising or cur["cats"][c]["est"] <= 0:
            continue
        out.append(f'<div class="topic">🔝 <b>{html.escape(CAT_INFO[c]["name"])}</b> ({_pct(cur["cats"][c]["pct"])}).<br>Gợi ý: {html.escape(CAT_INFO[c]["topic"])}</div>')
    return "".join(out) or "<p class='muted'>Chưa có nguy cơ nổi bật.</p>"


def render(agg, school=None, group="week", grade=None, key=""):
    kq = ("&key=" + quote(key)) if key else ""  # giữ khoá xem trong mọi đường link của trang
    schools = agg.schools()
    head = f"<!DOCTYPE html><html lang='vi'><head><meta charset='utf-8'><title>EduShield - Thống kê nhà trường</title><style>{CSS}</style></head><body><div class='wrap'>"
    if not school:
        items = "".join(f"<li><a href='/truong?school={quote(s)}{kq}'>{html.escape(s)}</a></li>" for s in schools) or "<li>Chưa có dữ liệu. Chạy <code>python simulate_school.py</code> để tạo dữ liệu mô phỏng.</li>"
        return head + f"<h1>🛡️ EduShield · Thống kê nhà trường</h1><div class='card'><h2>Chọn trường</h2><ul>{items}</ul></div></div></body></html>"
    grade = None  # chỉ hiển thị số liệu toàn trường, không chia theo khối
    rows = agg.report(school, group, None)
    q = lambda **kw: "/truong?" + "&".join(f"{k}={quote(str(v))}" for k, v in {"school": school, "group": group, **kw}.items()) + kq
    filt = "<div class='filters'>" + "".join(
        f"<a class='{'on' if group == g else ''}' href='{q(group=g)}'>{n}</a>" for g, n in (("day", "Theo ngày"), ("week", "Theo tuần"))) + " &nbsp; <a class='on'>Toàn trường</a></div>"
    vis = [r for r in rows if not r["hidden"]]
    hidden = len(rows) - len(vis)
    body = [head, f"<h1>🛡️ Thống kê nguy cơ trên mạng · {html.escape(school)}</h1>",
            "<div class='sub'>Số liệu là <b>ước lượng</b> từ các gói ẩn danh đã được xáo trộn. Không có nội dung tin nhắn, không có danh tính học sinh.</div>", filt]
    if not vis:
        body.append(f"<div class='card'>Chưa có kỳ nào đủ {K_MIN} gói dữ liệu. Để bảo vệ học sinh, nhóm nhỏ hơn {K_MIN} gói sẽ không được hiển thị.</div>")
    else:
        cur = vis[-1]
        lbl = _period_label(cur["period"], group)
        body.append("<div class='row'>"
                    f"<div class='kpi'><span>Kỳ gần nhất</span><b>{lbl}</b><span>{cur['n']} lượt học sinh-ngày tham gia</span></div>"
                    f"<div class='kpi'><span>Gặp dấu hiệu lừa đảo</span><b style='color:#e85d04'>{_pct(cur['cats']['lua_dao_bat_ky']['pct'])}</b><span>khoảng {_pct(cur['cats']['lua_dao_bat_ky']['pct_lo'])} – {_pct(cur['cats']['lua_dao_bat_ky']['pct_hi'])}</span></div>"
                    f"<div class='kpi'><span>Gặp dấu hiệu bắt nạt</span><b style='color:#8250df'>{_pct(cur['cats']['bat_nat_bat_ky']['pct'])}</b><span>khoảng {_pct(cur['cats']['bat_nat_bat_ky']['pct_lo'])} – {_pct(cur['cats']['bat_nat_bat_ky']['pct_hi'])}</span></div>"
                    "</div>")
        body.append(f"<div class='card'><h2>Gợi ý chủ đề tuyên truyền ({lbl})</h2>{_topics(rows)}</div>")
        body.append(f"<div class='card'><h2>Xu hướng: tỷ lệ lượt học sinh-ngày gặp nguy cơ</h2>{_line_chart(rows, group)}</div>")
        body.append(f"<div class='card'><h2>Theo loại nguy cơ ({lbl})</h2>{_bars(cur)}<p class='muted' style='font-size:12px'>Vạch mờ: khoảng tin cậy 95%.</p></div>")
        tbl = ["<table><tr><th>Kỳ</th><th>Số lượt</th><th>Lừa đảo</th><th>Bắt nạt</th><th>Ước tính lượt gặp lừa đảo</th><th>Ước tính lượt gặp bắt nạt</th></tr>"]
        for r in reversed(rows):
            if r["hidden"]:
                tbl.append(f"<tr><td>{_period_label(r['period'], group)}</td><td colspan='5' class='muted'>Ẩn: chưa đủ {K_MIN} gói</td></tr>")
            else:
                a, b = r["cats"]["lua_dao_bat_ky"], r["cats"]["bat_nat_bat_ky"]
                tbl.append(f"<tr><td>{_period_label(r['period'], group)}</td><td>{r['n']}</td><td>{_pct(a['pct'])}</td><td>{_pct(b['pct'])}</td><td>≈ {a['est']:.0f}</td><td>≈ {b['est']:.0f}</td></tr>")
        tbl.append("</table>")
        body.append("<div class='card'><h2>Bảng số liệu</h2>" + "".join(tbl) + "</div>")
    p = p_keep(EPSILON)
    body.append(f"""<div class='card priv'><h2>Nhà trường nhận được gì, và không nhận được gì</h2>
    <b>Nhận được:</b> mỗi ngày, mỗi học sinh <i>tự nguyện tham gia</i> gửi một gói gồm 20 ô có/không ("hôm nay có gặp loại nguy cơ này không", "có được nhắc trước khi gửi không"), kèm mã trường và ngày (không có khối, lớp).<br>
    <b>Không nhận được:</b> nội dung tin nhắn, người gửi, link, giờ phút, tên, lớp, mã máy của học sinh.<br>
    <b>Xáo trộn ngẫu nhiên (randomized response, ε = {EPSILON}):</b> trước khi gửi, mỗi ô được giữ đúng với xác suất {p:.0%} và bị đảo với xác suất {1-p:.0%}.
    Vì vậy kể cả khi thấy một gói ghi "có", nhà trường cũng không thể khẳng định học sinh đó thật sự đã gặp. Khi cộng hàng trăm gói, nhiễu triệt tiêu nhau và cho ra tỷ lệ chung.<br>
    <b>Chỉ lưu tổng:</b> máy chủ cộng dồn rồi bỏ gói, không lưu gói lẻ. Nhóm dưới {K_MIN} gói bị ẩn{f" (đang ẩn {hidden} kỳ)" if hidden else ""}.<br>
    <b>Đơn vị:</b> "lượt học sinh-ngày" là một học sinh trong một ngày. Tỷ lệ 5% nghĩa là trung bình mỗi ngày khoảng 5% học sinh tham gia gặp loại nguy cơ đó.<br>
    <b>Mục đích duy nhất:</b> chọn chủ đề tuyên truyền, sinh hoạt dưới cờ, tiết kỹ năng. Số liệu này không dùng để tìm, đánh giá hay xử lý bất kỳ học sinh nào.</div>""")
    body.append("</div></body></html>")
    return "".join(body)

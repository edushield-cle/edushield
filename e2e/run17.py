# Kiểm thử v1.7: phân biệt TUYÊN TRUYỀN với ĐANG GẶP NGUY CƠ (app + tiện ích trên một bài tuyên truyền có bình luận)
import asyncio, tempfile, subprocess, sys, time, os, urllib.request
from playwright.async_api import async_playwright
EXT="/home/claude/edushield/extension"; OUT="/home/claude/e2e"; B="http://127.0.0.1:8765"
SR="document.getElementById('edushield-root').shadowRoot"
POST = [
  "Công an tỉnh cảnh báo thủ đoạn giả danh cán bộ công an gọi điện cho học sinh, nói em liên quan vụ án rửa tiền, yêu cầu giữ bí mật với gia đình rồi chuyển tiền. Tuyệt đối không làm theo, hãy báo ngay cho bố mẹ hoặc gọi 113.",
  "Dấu hiệu nhận biết: giục gấp, đòi mã OTP, gửi đường link lạ, bắt giữ bí mật. Ngân hàng và công an không bao giờ làm việc qua tin nhắn.",
]
CMTS = [
  ("Phụ huynh lớp 10A", "Cảm ơn công an đã cảnh báo, hôm trước nhà tôi cũng nhận được cuộc gọi giả danh như vậy."),
  ("Minh Anh", "Mình sẽ gửi bài này vào nhóm lớp để các bạn đề phòng chiêu bắt cóc online."),
  ("Tài khoản lạ", "Ai cần việc làm thêm tại nhà 500k/ngày, nạp trước 200k kích hoạt nhiệm vụ, inbox mình ngay."),
  ("Hoàng", "Đừng để ý mấy đứa chê bai trên mạng nhé bạn, bạn không có lỗi gì cả."),
  ("Tài khoản ẩn danh", "Đứa nào share bài này là đồ ngu, tao biết mặt hết rồi, liệu hồn."),
]
HTML = ("<!doctype html><meta charset=utf-8><title>Bài tuyên truyền</title><body style='font:16px system-ui;max-width:640px;margin:20px auto'>"
        "<h2>Cảnh giác thủ đoạn giả danh công an nhắm vào học sinh</h2>" + "".join(f"<p>{x}</p>" for x in POST)
        + "<h3>Bình luận</h3>" + "".join(f"<div style='border-top:1px solid #ddd;padding:8px 0'><b>{a}</b><div>{t}</div></div>" for a, t in CMTS) + "</body>")
async def main():
  srv=subprocess.Popen([sys.executable,"server.py"],cwd="/home/claude/edushield",stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  try:
    for _ in range(40):
      try: urllib.request.urlopen(B+"/health"); break
      except Exception: time.sleep(0.5)
    async with async_playwright() as p:
      # 1. App điện thoại: tin mẫu "Tin tuyên truyền"
      b=await p.chromium.launch(args=["--no-proxy-server"])
      m=await (await b.new_context(viewport={"width":400,"height":760},device_scale_factor=2)).new_page(); errs=[]; m.on("pageerror",lambda e:errs.append(str(e)))
      await m.goto(B+"/app/"); await m.wait_for_timeout(500)
      await m.click("[data-go='2']"); await m.click("[data-go='3']"); await m.check("#agree"); await m.click("#startBtn")
      await m.click("button.chip[data-s='3']"); await m.wait_for_timeout(500)
      r1=(await m.inner_text("#result")).replace("\n"," ")
      print("1. App - tin tuyên truyền:", r1[:80]); assert "tuyên truyền" in r1
      await m.click("button.chip[data-s='0']"); await m.wait_for_timeout(500)
      r2=(await m.inner_text("#result")).replace("\n"," ")
      print("   App - mạo danh cô giáo:", r2[:60]); assert "Cảnh báo" in r2 or "Khẩn cấp" in r2
      await m.click("button.chip[data-s='3']"); await m.wait_for_timeout(400)
      await (await m.query_selector("#result")).screenshot(path=f"{OUT}/v17_app_tt.png")
      print("   lỗi JS app:", errs); await b.close()
      # 2. Tiện ích trên bài tuyên truyền có bình luận
      ctx=await p.chromium.launch_persistent_context(tempfile.mkdtemp(),headless=True,channel="chromium",viewport={"width":1100,"height":900},device_scale_factor=2,
            args=[f"--disable-extensions-except={EXT}",f"--load-extension={EXT}","--no-proxy-server"])
      await ctx.route("http://127.0.0.1:8765/bai-tuyen-truyen", lambda r: r.fulfill(body=HTML, content_type="text/html; charset=utf-8"))
      sw=ctx.service_workers[0] if ctx.service_workers else await ctx.wait_for_event("serviceworker",timeout=15000); eid=sw.url.split("/")[2]
      await asyncio.sleep(1)
      ob=await ctx.new_page(); await ob.goto(f"chrome-extension://{eid}/onboarding.html"); await ob.click("#n1"); await ob.click("#n2"); await ob.click("#n3"); await ob.check("#a"); await ob.click("#go"); await ob.wait_for_timeout(400)
      pg=await ctx.new_page(); e2=[]; pg.on("pageerror",lambda e:e2.append(str(e))); await pg.goto(B+"/bai-tuyen-truyen"); await pg.wait_for_timeout(3000)
      st=await pg.evaluate(f"(()=>{{const s={SR};return {{stat:s.getElementById('statline').textContent,cards:[...s.querySelectorAll('.msg.canh_bao .ttl,.msg.khan_cap .ttl,.msg.luu_y .ttl')].map(x=>x.textContent)}}}})()")
      print("2. Bài tuyên truyền + 5 bình luận:", st)
      # một bình luận có thể được quét ở cả khối ngoài (tên + nội dung) lẫn khối trong: tính theo loại cảnh báo
      kinds={c.split("Cảnh báo")[0].split("Khẩn cấp")[0][2:].strip() for c in st["cards"]}
      print("   Loại cảnh báo:", kinds); assert kinds == {"Việc nhẹ lương cao", "Đe doạ"}, kinds
      assert "tuyên truyền" in st["stat"]
      await pg.evaluate(f"{SR}.getElementById('fab').click()"); await pg.wait_for_timeout(600)
      await pg.screenshot(path=f"{OUT}/v17_web_tt.png")
      print("   lỗi JS trang:", e2)
      await ctx.close()
  finally: srv.terminate()
  print("OK: tin tuyên truyền không bị cảnh báo, bình luận lừa đảo và bắt nạt vẫn bị cảnh báo")
asyncio.run(main())

# Kiểm thử v1.6: quét mọi trang web, bỏ qua trang nhạy cảm, báo người thân, gửi về trường (ẩn danh / tên - lớp), giao diện gọn
import asyncio, tempfile, json, subprocess, sys, time, os, urllib.request
from playwright.async_api import async_playwright
EXT="/home/claude/edushield/extension"; OUT="/home/claude/e2e"; B="http://127.0.0.1:8765"
SR="document.getElementById('edushield-root').shadowRoot"
NEWS = """<!doctype html><meta charset=utf-8><title>Báo mô phỏng</title><body style='font:16px system-ui;max-width:700px;margin:auto'>
<h2>Video: Tiết mục văn nghệ của lớp 10A1</h2><video width=480 height=270></video>
<h3>Bình luận</h3>
<p>Video hay quá, cảm ơn bạn đã chia sẻ</p>
<p>béo như vậy mà cũng mặc váy lên sân khấu, tự nhìn lại mình đi</p>
<p>Giọng hát ổn, phần âm thanh hơi nhỏ thôi</p>
<p>anh em vào trang của nó spam chửi cho nó khoá nick luôn</p>
<p>Tuyển CTV làm nhiệm vụ thả tim video kiếm 500k mỗi ngày, nạp trước để mở khoá nhiệm vụ cao</p>
</body>"""
BANK = "<!doctype html><meta charset=utf-8><title>Ngân hàng</title><p>Nhập mã OTP để chuyển khoản 5 triệu cho số tài khoản 1234567890</p>"
async def main():
  srv=subprocess.Popen([sys.executable,"server.py"],cwd="/home/claude/edushield",env={**os.environ,"EDUSHIELD_VIEW_KEY":"k123"},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  try:
    for _ in range(40):
      try: urllib.request.urlopen(B+"/health"); break
      except Exception: time.sleep(0.5)
    async with async_playwright() as p:
      ctx=await p.chromium.launch_persistent_context(tempfile.mkdtemp(),headless=True,channel="chromium",viewport={"width":1100,"height":800},args=[f"--disable-extensions-except={EXT}",f"--load-extension={EXT}","--no-proxy-server"])
      await ctx.route("https://tin-tuc-mo-phong.example/**", lambda r: r.fulfill(status=200, content_type="text/html; charset=utf-8", body=NEWS))
      await ctx.route("https://ebank.vietcombank.com.vn/**", lambda r: r.fulfill(status=200, content_type="text/html; charset=utf-8", body=BANK))
      await ctx.route("https://zalo.me/**", lambda r: r.fulfill(status=200, content_type="text/html", body="<p>zalo</p>"))
      sw=ctx.service_workers[0] if ctx.service_workers else await ctx.wait_for_event("serviceworker",timeout=15000); eid=sw.url.split("/")[2]
      await asyncio.sleep(1)
      ob=[x for x in ctx.pages if "onboarding" in x.url]; ob=ob[0] if ob else await ctx.new_page()
      await ob.goto(f"chrome-extension://{eid}/onboarding.html"); await ob.click("#n1"); await ob.click("#n2"); await ob.click("#n3"); await ob.check("#a"); await ob.click("#go"); await ob.wait_for_timeout(300)
      errs=[]
      # 1. Cửa sổ tiện ích: thêm người thân + chọn "Tên - lớp"
      pop=await ctx.new_page(); pop.on("pageerror",lambda e:errs.append("popup:"+str(e)))
      await pop.set_viewport_size({"width":360,"height":1300}); await pop.goto(f"chrome-extension://{eid}/popup.html"); await pop.wait_for_timeout(600)
      await pop.click("#ctAddBtn"); await pop.fill("#ctName","Mẹ"); await pop.fill("#ctPhone","0912345678"); await pop.click("#ctSave"); await pop.wait_for_timeout(300)
      print("1. Người thân:", await pop.inner_text("#ctList"))
      await pop.click("label[data-m='danh_tinh']"); await pop.fill("#stName","Nguyễn Văn An"); await pop.fill("#stCls","10A1"); await pop.check("#parental"); await pop.click("#shareSave")
      await pop.wait_for_selector("#shareMsg",state="visible",timeout=15000); await pop.wait_for_timeout(300)
      print("   Gửi về trường:", await pop.inner_text("#pill"), "|", await pop.inner_text("#shareMsg"))
      await pop.screenshot(path=f"{OUT}/v16_popup.png",full_page=True)
      # 2. Trang thử nghiệm: tin "bắt cóc online" -> khẩn cấp -> đếm ngược 10 giây -> báo thầy cô
      t=await ctx.new_page(); t.on("pageerror",lambda e:errs.append("page:"+str(e)))
      await t.goto(f"chrome-extension://{eid}/thu-nghiem.html"); await t.wait_for_timeout(1500)
      el=t.locator(".bubble",has_text="khách sạn"); await el.scroll_into_view_if_needed(); await t.wait_for_timeout(2500)
      ev=lambda js: t.evaluate(f"(()=>{{const R={SR};{js}}})()")
      await ev("R.getElementById('fab').click()"); await t.wait_for_timeout(300)
      card=await ev("const c=[...R.querySelectorAll('.msg.khan_cap')].find(x=>x.textContent.includes('khách sạn')||x.textContent.includes('công an'));return c?{ttl:c.querySelector('.ttl').textContent,sup:c.querySelector('.sup')?.textContent,btns:[...c.querySelectorAll('button')].map(b=>b.textContent)}:null")
      print("2. Thẻ khẩn cấp:", json.dumps(card,ensure_ascii=False))
      await t.screenshot(path=f"{OUT}/v16_khan_cap.png")
      await t.wait_for_timeout(11500)
      sup=await ev("const c=[...R.querySelectorAll('.msg.khan_cap')].find(x=>x.querySelector('.sup'));return c&&c.querySelector('.sup').textContent")
      print("   Sau 11 giây:", sup)
      html=urllib.request.urlopen(B+"/hotro?school=THPT_DEMO&key=k123").read().decode()
      print("   Trang thầy cô có tên học sinh:", "Nguyễn Văn An" in html, "| có nội dung tin nhắn:", "khách sạn" in html or "rửa tiền" in html)
      try: urllib.request.urlopen(B+"/hotro?school=THPT_DEMO"); print("   LỖI: xem được không cần khoá")
      except Exception as e: print("   Không có khoá -> chặn:", e)
      al=await sw.evaluate("chrome.alarms.get('edushield-emg').then(a=>a?Math.round((a.scheduledTime-Date.now())/60000*10)/10:null)")
      print("   Gói ẩn danh hẹn gửi sau (phút):", al)
      # 3. Báo người thân: không có số điện thoại trong trang web
      await ev("const c=[...R.querySelectorAll('.msg.khan_cap')].find(x=>x.querySelector('.sup'));[...c.querySelectorAll('button')].find(b=>b.textContent.includes('Báo người thân')).click()"); await t.wait_for_timeout(300)
      sos=await ev("return R.querySelector('.sos').innerText")
      print("3. Hộp báo người thân:", sos.replace("\n"," | "), "| lộ số trong trang:", "0912345678" in (await ev("return R.innerHTML")))
      n0=len(ctx.pages)
      await ev("[...R.querySelector('.sos').querySelectorAll('button')].find(b=>b.textContent=='Zalo').click()"); await t.wait_for_timeout(1500)
      print("   Bấm Zalo mở:", [pg.url for pg in ctx.pages[n0:]])
      await t.screenshot(path=f"{OUT}/v16_sos.png")
      # 4. Trang web bất kỳ (bình luận dưới video)
      w=await ctx.new_page(); await w.goto("https://tin-tuc-mo-phong.example/video"); await w.wait_for_timeout(2500)
      r=await w.evaluate(f"(()=>{{const R={SR};return [...R.querySelectorAll('.msg .ttl')].map(x=>x.textContent)}})()")
      print("4. Trang web thường - cảnh báo:", r)
      await w.evaluate(f"{SR}.getElementById('fab').click()"); await w.wait_for_timeout(300); await w.screenshot(path=f"{OUT}/v16_web.png")
      # 5. Trang ngân hàng: không quét, không hiện nút
      bk=await ctx.new_page(); await bk.goto("https://ebank.vietcombank.com.vn/login"); await bk.wait_for_timeout(2000)
      print("5. Trang ngân hàng - nút EduShield:", await bk.evaluate("(()=>{const h=document.getElementById('edushield-root');return h?getComputedStyle(h).display:'không có'})()"),
            "| số cảnh báo:", await bk.evaluate(f"(()=>{{const R={SR};return R?R.querySelectorAll('.msg.khan_cap,.msg.canh_bao,.msg.luu_y').length:0}})()"))
      print("Lỗi JS:", errs)
      await ctx.close()
  finally: srv.terminate()
asyncio.run(main())

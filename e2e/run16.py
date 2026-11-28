# Kiểm thử v1.6 trên app điện thoại + chụp ảnh minh chứng
import asyncio, tempfile, json, subprocess, sys, time, os, urllib.request
from urllib.parse import quote
from playwright.async_api import async_playwright
EXT="/home/claude/edushield/extension"; OUT="/home/claude/e2e"; B="http://127.0.0.1:8765"
SR="document.getElementById('edushield-root').shadowRoot"
CFG='globalThis.EDUSHIELD_CONFIG = { collect: true, school: "THPT_DEMO", server: "http://127.0.0.1:8765" };'
async def main():
  srv=subprocess.Popen([sys.executable,"server.py"],cwd="/home/claude/edushield",env={**os.environ,"EDUSHIELD_VIEW_KEY":"k123"},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  try:
    for _ in range(40):
      try: urllib.request.urlopen(B+"/health"); break
      except Exception: time.sleep(0.5)
    async with async_playwright() as p:
      b=await p.chromium.launch(args=["--no-proxy-server"])
      ctx=await b.new_context(viewport={"width":400,"height":860},device_scale_factor=2)
      await ctx.route("**/app/config.js", lambda r: r.fulfill(status=200, content_type="application/javascript", body=CFG))
      await ctx.grant_permissions(["clipboard-read","clipboard-write"],origin=B)
      m=await ctx.new_page(); errs=[]; m.on("pageerror",lambda e:errs.append(str(e)))
      await m.goto(B+"/app/"); await m.wait_for_timeout(500)
      await m.click("[data-go='2']"); await m.click("[data-go='3']"); await m.check("#agree"); await m.click("#startBtn")
      # cài đặt: chế độ tên - lớp
      await m.click("nav button[data-t='stats']"); await m.click("#modeSeg button[data-m='danh_tinh']")
      await m.fill("#stName","Trần Thị Bình"); await m.fill("#stCls","11A2"); await m.check("#parental"); await m.click("#shSave"); await m.wait_for_timeout(800)
      print("1. App - gửi về trường:", await m.inner_text("#shPill"), "|", await m.inner_text("#shMsg"))
      await m.screenshot(path=f"{OUT}/v16_app_truong.png")
      # người hỗ trợ
      await m.click("nav button[data-t='help']"); await m.click("#ctAddBtn"); await m.fill("#ctName","Bố"); await m.fill("#ctPhone","0987654321"); await m.click("#ctSave")
      print("2. App - người thân:", (await m.inner_text("#ctList")).replace("\n"," "))
      await m.screenshot(path=f"{OUT}/v16_app_sos.png")
      # Chia sẻ từ ứng dụng khác (Web Share Target) -> tự kiểm tra
      txt="Đây là cán bộ công an, em liên quan vụ án rửa tiền, không được nói với bố mẹ, phải thuê phòng khách sạn ở một mình"
      await m.goto(B+"/app/?text="+quote(txt)); await m.wait_for_timeout(1500)
      print("3. Chia sẻ vào app -> tự kiểm tra:", (await m.inner_text("#result"))[:90].replace("\n"," "))
      await m.click("#sosBtn"); await m.wait_for_timeout(200)
      links=await m.evaluate("[...document.querySelectorAll('#sosBox a')].map(a=>a.getAttribute('href').slice(0,40))")
      print("   Báo người thân:", links)
      await m.screenshot(path=f"{OUT}/v16_app_share.png")
      await m.wait_for_timeout(11000)
      print("   Sau 11 giây:", await m.evaluate("(document.querySelector('.sup')||{}).textContent"))
      # Dán từ bộ nhớ tạm
      await m.evaluate("navigator.clipboard.writeText('béo như vậy mà cũng mặc váy, tự nhìn lại mình đi')")
      await m.click("#pasteBtn"); await m.wait_for_timeout(600)
      print("4. Dán và kiểm tra:", (await m.inner_text("#result"))[:60].replace("\n"," "))
      print("   Lỗi JS:", errs)
      # Trang thầy cô
      t=await b.new_page(viewport={"width":1100,"height":520}); await t.goto(B+"/hotro?school=THPT_DEMO&key=k123")
      print("5. Trang thầy cô:", (await t.inner_text("table"))[:200].replace("\n"," | ").replace("\t"," "))
      await t.screenshot(path=f"{OUT}/v16_hotro.png")
      await t.click("button:has-text('Đã liên hệ')"); await t.wait_for_timeout(500)
      print("   Sau khi bấm Đã liên hệ:", "(0 mới)" in await t.content())
      await b.close()
      # Tiện ích: ảnh có khung cảnh báo mở
      ctx2=await p.chromium.launch_persistent_context(tempfile.mkdtemp(),headless=True,channel="chromium",viewport={"width":1100,"height":800},args=[f"--disable-extensions-except={EXT}",f"--load-extension={EXT}","--no-proxy-server"])
      NEWS=open("/home/claude/edushield/e2e/run15.py",encoding="utf-8").read().split('NEWS = """')[1].split('"""')[0]
      await ctx2.route("https://tin-tuc-mo-phong.example/**", lambda r: r.fulfill(status=200, content_type="text/html; charset=utf-8", body=NEWS))
      sw=ctx2.service_workers[0] if ctx2.service_workers else await ctx2.wait_for_event("serviceworker",timeout=15000); eid=sw.url.split("/")[2]
      await asyncio.sleep(1)
      ob=[x for x in ctx2.pages if "onboarding" in x.url]; ob=ob[0] if ob else await ctx2.new_page()
      await ob.goto(f"chrome-extension://{eid}/onboarding.html"); await ob.click("#n1"); await ob.click("#n2"); await ob.click("#n3"); await ob.check("#a"); await ob.click("#go"); await ob.wait_for_timeout(300)
      await sw.evaluate("chrome.storage.local.set({contacts:[{name:'Mẹ',phone:'0912345678'},{name:'Cô chủ nhiệm',phone:'0901234567'}],share:{enabled:true,parental:true,mode:'danh_tinh',name:'Nguyễn Văn An',lop:'10A1'}})")
      t2=await ctx2.new_page(); await t2.goto(f"chrome-extension://{eid}/thu-nghiem.html"); await t2.wait_for_timeout(1200)
      await t2.locator(".bubble",has_text="khách sạn").scroll_into_view_if_needed(); await t2.wait_for_timeout(2200)
      await t2.evaluate(f"(()=>{{const R={SR};if(!R.getElementById('panel').classList.contains('open'))R.getElementById('fab').click();const b=R.getElementById('body');b.scrollTop=b.scrollHeight}})()")
      await t2.wait_for_timeout(400); await t2.screenshot(path=f"{OUT}/v16_panel_khan_cap.png")
      await t2.evaluate(f"(()=>{{const R={SR};const c=[...R.querySelectorAll('.msg.khan_cap')].pop();[...c.querySelectorAll('button')].find(b=>b.textContent.includes('Báo người thân')).click();const b=R.getElementById('body');b.scrollTop=b.scrollHeight}})()")
      await t2.wait_for_timeout(400); await t2.screenshot(path=f"{OUT}/v16_panel_sos.png")
      w=await ctx2.new_page(); await w.goto("https://tin-tuc-mo-phong.example/video"); await w.wait_for_timeout(2500)
      await w.evaluate(f"(()=>{{const R={SR};if(!R.getElementById('panel').classList.contains('open'))R.getElementById('fab').click()}})()"); await w.wait_for_timeout(300)
      await w.screenshot(path=f"{OUT}/v16_web_binh_luan.png")
      await ctx2.close()
  finally: srv.terminate()
asyncio.run(main())

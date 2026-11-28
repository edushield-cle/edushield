# Kiểm thử v1.8.1: nút "← Màn hình chính" trong Thực chiến giả lập (app web và tiện ích)
import asyncio, tempfile, subprocess, sys, time, urllib.request
from playwright.async_api import async_playwright
EXT="/home/claude/edushield/extension"; OUT="/home/claude/e2e"; B="http://127.0.0.1:8765"
async def main():
  srv=subprocess.Popen([sys.executable,"server.py"],cwd="/home/claude/edushield",stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  try:
    for _ in range(40):
      try: urllib.request.urlopen(B+"/health"); break
      except Exception: time.sleep(0.5)
    async with async_playwright() as p:
      b=await p.chromium.launch(args=["--no-proxy-server"])
      pg=await (await b.new_context(viewport={"width":400,"height":820},device_scale_factor=2)).new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
      # App web: đi từ màn hình chính vào diễn tập rồi quay lại
      await pg.goto(B+"/app/"); await pg.wait_for_timeout(600)
      await pg.click("[data-go='2']"); await pg.click("[data-go='3']"); await pg.check("#agree"); await pg.click("#startBtn"); await pg.wait_for_timeout(500)
      await pg.click("#drillCard"); await pg.wait_for_selector("#dBack")
      await pg.screenshot(path=f"{OUT}/v181_app_drill.png")
      await pg.click("#dStart"); await pg.wait_for_selector("[data-a]")
      # nút vẫn thấy khi đang làm bài (thanh dính trên cùng)
      vis=await pg.is_visible("#dBack"); print("1. App: đang làm bài, nút quay lại hiển thị:", vis); assert vis
      await pg.click("#dBack"); await pg.wait_for_selector("#drillCard", timeout=8000)
      print("   Sau khi bấm: về", pg.url.replace(B,""), "| thấy ô kiểm tra tin:", await pg.is_visible("#txt"), "| lỗi JS:", errs)
      assert pg.url.endswith("/app/index.html") and await pg.is_visible("#txt")
      await b.close()
      # Tiện ích: mở diễn tập như từ cửa sổ tiện ích, bấm quay lại -> thấy giao diện tiện ích trong tab
      ctx=await p.chromium.launch_persistent_context(tempfile.mkdtemp(),headless=True,channel="chromium",viewport={"width":900,"height":820},
            args=[f"--disable-extensions-except={EXT}",f"--load-extension={EXT}","--no-proxy-server"])
      sw=ctx.service_workers[0] if ctx.service_workers else await ctx.wait_for_event("serviceworker",timeout=15000); eid=sw.url.split("/")[2]
      e2=[]; d=await ctx.new_page(); d.on("pageerror",lambda e:e2.append(str(e)))
      await d.goto(f"chrome-extension://{eid}/drill.html"); await d.wait_for_selector("#dBack")
      await d.click("#dBack"); await d.wait_for_selector("#drillBtn", timeout=8000)
      full=await d.evaluate("document.documentElement.classList.contains('full')")
      print("2. Tiện ích: về", d.url.split(eid)[1], "| chế độ toàn trang:", full, "| ô 'Trên trang này' ẩn:", not await d.is_visible("#pageCard"))
      print("   Thấy:", (await d.inner_text("header")).replace("\n"," "), "|", await d.inner_text("#drillState"))
      assert "popup.html" in d.url and full and not await d.is_visible("#pageCard")
      await d.screenshot(path=f"{OUT}/v181_ext_home.png")
      n=len(ctx.pages); await d.click("#drillBtn"); await d.wait_for_selector("#dStart")
      print("3. Bấm 'Diễn tập' lại: mở trong cùng tab:", len(ctx.pages)==n, "| lỗi JS:", e2)
      assert len(ctx.pages)==n and not e2
      await ctx.close()
  finally: srv.terminate()
  print("OK: nút Màn hình chính đưa học sinh về giao diện chính của app web và tiện ích")
asyncio.run(main())

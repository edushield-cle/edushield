# Kiểm thử v1.8: Thực chiến giả lập trên app web và tiện ích; chụp ảnh minh chứng
import asyncio, tempfile, subprocess, sys, time, urllib.request
from playwright.async_api import async_playwright
EXT="/home/claude/edushield/extension"; OUT="/home/claude/e2e"; B="http://127.0.0.1:8765"
async def play(pg, choose_best=True):
    await pg.wait_for_selector("[data-a]", timeout=8000)
    i = await pg.evaluate("(()=>{const id=new URLSearchParams(location.search).get('id');return 0})()")
    btns = await pg.query_selector_all("[data-a]")
    # chọn phương án an toàn nhất theo kho tình huống (để kiểm tra chấm điểm), hoặc phương án đầu
    best = await pg.evaluate("(()=>{const t=document.querySelector('.ph-top').textContent.slice(3);const s=EduShieldDrill.SCENARIOS.find(x=>x.from===t);return s.act.reduce((b,x,i)=>x[1]>s.act[b][1]?i:b,0)})()")
    await btns[best if choose_best else 0].click()
    await pg.wait_for_selector("[data-s]")
    for c in await pg.query_selector_all("[data-s]"):
        await c.click()
    await pg.click("#dDone"); await pg.wait_for_selector(".reveal")
    return await pg.inner_text(".reveal")
async def main():
  srv=subprocess.Popen([sys.executable,"server.py"],cwd="/home/claude/edushield",stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  try:
    for _ in range(40):
      try: urllib.request.urlopen(B+"/health"); break
      except Exception: time.sleep(0.5)
    async with async_playwright() as p:
      b=await p.chromium.launch(args=["--no-proxy-server"])
      pg=await (await b.new_context(viewport={"width":400,"height":820},device_scale_factor=2)).new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
      await pg.goto(B+"/app/drill.html"); await pg.wait_for_selector("#dStart")
      print("1. Trang diễn tập:", (await pg.inner_text(".hero")).replace("\n"," "))
      await pg.check("#dConsent"); await pg.select_option("#dFreq","tuan"); await pg.click("#dSave")
      print("   Lưu:", await pg.inner_text("#dMsg"))
      await pg.screenshot(path=f"{OUT}/v18_drill_home0.png")
      await pg.click("#dStart"); await pg.wait_for_timeout(1500); await pg.screenshot(path=f"{OUT}/v18_drill_msg.png")
      r1=await play(pg, True); print("2. Lần 1 (an toàn):", r1.replace("\n"," ")[:160])
      assert "DIỄN TẬP" in r1
      await pg.screenshot(path=f"{OUT}/v18_drill_reveal.png", full_page=True)
      for k in range(5):
        await pg.click("#dAgain"); await pg.wait_for_timeout(300); await play(pg, k % 2 == 0)
      await pg.click("#dHome"); await pg.wait_for_selector(".hero")
      st=await pg.evaluate("JSON.parse(localStorage.getItem('edushield_drill'))")
      print("3. Sau 6 lần: chỉ số", (await pg.inner_text(".hero .big")).replace("\n",""), "| lịch sử", len(st["history"]), "| hẹn lần sau", "có" if st["next"] else "không")
      assert len(st["history"])==6 and st["next"]>0
      await pg.screenshot(path=f"{OUT}/v18_drill_home.png", full_page=True)
      # App: thẻ diễn tập ở tab Kiểm tra, khi tới giờ hiện "tin nhắn mới"
      await pg.evaluate("(()=>{const s=JSON.parse(localStorage.getItem('edushield_drill'));s.next=Date.now()-1000;localStorage.setItem('edushield_drill',JSON.stringify(s))})()")
      await pg.goto(B+"/app/"); await pg.wait_for_timeout(600)
      await pg.click("[data-go='2']"); await pg.click("[data-go='3']"); await pg.check("#agree"); await pg.click("#startBtn"); await pg.wait_for_timeout(500)
      print("4. App - thẻ diễn tập:", (await pg.inner_text("#drillCard")).replace("\n"," "), "| lỗi JS:", errs)
      assert "Tin nhắn mới" in await pg.inner_text("#drillCard")
      await b.close()
      # Tiện ích
      ctx=await p.chromium.launch_persistent_context(tempfile.mkdtemp(),headless=True,channel="chromium",viewport={"width":420,"height":820},
            args=[f"--disable-extensions-except={EXT}",f"--load-extension={EXT}","--no-proxy-server"])
      sw=ctx.service_workers[0] if ctx.service_workers else await ctx.wait_for_event("serviceworker",timeout=15000); eid=sw.url.split("/")[2]
      e2=[]; d=await ctx.new_page(); d.on("pageerror",lambda e:e2.append(str(e)))
      await d.goto(f"chrome-extension://{eid}/drill.html"); await d.wait_for_selector("#dStart")
      await d.check("#dConsent"); await d.select_option("#dFreq","thuong"); await d.click("#dSave"); await d.wait_for_timeout(600)
      al=await sw.evaluate("new Promise(r=>chrome.alarms.get('edushield-drill',a=>r(a?Math.round((a.scheduledTime-Date.now())/36e5):null)))")
      print("5. Tiện ích: hẹn diễn tập sau khoảng", al, "giờ")
      assert al is not None and al > 0
      await sw.evaluate("drillFire()"); await d.wait_for_timeout(500)
      pend=await sw.evaluate("new Promise(r=>chrome.storage.local.get('edushield_drill',o=>r(o.edushield_drill.pending)))")
      print("   Khi tới giờ: tạo tình huống", pend)
      pop=await ctx.new_page(); await pop.goto(f"chrome-extension://{eid}/popup.html"); await pop.wait_for_timeout(800)
      print("6. Cửa sổ tiện ích:", await pop.inner_text("#drillState"), "| lỗi JS:", e2)
      await pop.screenshot(path=f"{OUT}/v18_popup.png")
      await ctx.close()
  finally: srv.terminate()
  print("OK: diễn tập chạy trên app web và tiện ích; chỉ số được cập nhật và lên lịch lần sau")
asyncio.run(main())

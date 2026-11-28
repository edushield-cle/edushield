import asyncio, tempfile
from playwright.async_api import async_playwright
EXT="/home/claude/edushield/extension"; OUT="/home/claude/e2e"; BASE="http://127.0.0.1:8765"
SR="document.getElementById('edushield-root').shadowRoot"
async def main():
  async with async_playwright() as p:
    ctx=await p.chromium.launch_persistent_context(tempfile.mkdtemp(),headless=True,channel="chromium",viewport={"width":900,"height":800},args=[f"--disable-extensions-except={EXT}",f"--load-extension={EXT}","--no-proxy-server"])
    sw=ctx.service_workers[0] if ctx.service_workers else await ctx.wait_for_event("serviceworker",timeout=15000); eid=sw.url.split("/")[2]; errs=[]
    ob=[x for x in ctx.pages if "onboarding" in x.url]; ob=ob[0] if ob else await ctx.new_page()
    await ob.goto(f"chrome-extension://{eid}/onboarding.html"); await ob.click("#n1"); await ob.click("#n2"); await ob.click("#n3"); await ob.check("#a"); await ob.click("#go"); await ob.wait_for_timeout(300)
    pg=await ctx.new_page(); pg.on("pageerror",lambda e:errs.append(str(e))); await pg.goto(BASE+"/demo"); await pg.wait_for_timeout(1200)
    st=lambda: pg.evaluate(f"({{open:{SR}.getElementById('panel').classList.contains('open'),toast:{SR}.getElementById('toast').classList.contains('show'),cards:{SR}.querySelectorAll('.msg.canh_bao,.msg.khan_cap,.msg.luu_y').length}})")
    first=None
    for i in range(12):
      await pg.click("#next"); await pg.wait_for_timeout(700)
      s=await st()
      if s["cards"]>0 and first is None: first=s; print("Cảnh báo đầu tiên (bước",i,"):",s); await pg.screenshot(path=f"{OUT}/w1_autoopen.png"); break
    await pg.evaluate(f"{SR}.getElementById('close').click()")
    before=(await st())["cards"]; seen=None
    for i in range(12):
      await pg.click("#next"); await pg.wait_for_timeout(700)
      s=await st()
      if s["cards"]>before: seen=s; break
    print("Cảnh báo sau khi đã đóng:",seen)
    await pg.screenshot(path=f"{OUT}/w2_toast.png")
    notes=await sw.evaluate("new Promise(r=>chrome.notifications.getAll(n=>r(Object.keys(n).length)))")
    print("Số thông báo hệ thống:",notes)
    await pg.evaluate(f"{SR}.getElementById('toastOpen').click()"); await pg.wait_for_timeout(200); print("Sau khi bấm Xem ngay:",await st())
    badge=await sw.evaluate("chrome.action.getBadgeText({})"); print("Huy hiệu:",badge)
    pop=await ctx.new_page(); await pop.set_viewport_size({"width":340,"height":1100}); await pop.goto(f"chrome-extension://{eid}/popup.html"); await pop.wait_for_timeout(700)
    await pop.screenshot(path=f"{OUT}/w3_popup.png",full_page=True)
    print("Mục cảnh báo popup:",await pop.locator("#alList .al").count(), "| lỗi:",errs); await ctx.close()
    b=await p.chromium.launch(channel="chromium",args=["--no-proxy-server"]); c=await b.new_context(**p.devices["Pixel 7"]); await c.grant_permissions(["notifications"],origin=BASE)
    m=await c.new_page(); errs=[]; m.on("pageerror",lambda e:errs.append(str(e)))
    await m.goto(BASE+"/app/"); await m.wait_for_timeout(900); await m.click('[data-go="2"]'); await m.click('#c2 [data-go="3"]'); await m.check("#agree"); await m.click("#startBtn")
    await m.click('nav button[data-t=alerts]'); await m.click("#ntBtn"); await m.wait_for_timeout(500); print("Thông báo:",await m.text_content("#ntPill"))
    await m.click('nav button[data-t=check]'); await m.click('[data-s="0"]'); await m.wait_for_timeout(500); await m.screenshot(path=f"{OUT}/w4_app_pop.png")
    await m.click('[data-s="1"]'); await m.wait_for_timeout(400)
    print("Huy hiệu tab:",await m.text_content("#alCnt"))
    n=await m.evaluate("navigator.serviceWorker.getRegistration().then(r=>r?r.getNotifications().then(x=>x.map(y=>y.title+' | '+y.body)):'no-sw')"); print("Thông báo SW:",n)
    await m.click('nav button[data-t=alerts]'); await m.wait_for_timeout(300); await m.screenshot(path=f"{OUT}/w5_app_alerts.png",full_page=True)
    print("[APP] lỗi:",errs); await b.close()
asyncio.run(main())

import asyncio, tempfile, datetime
from playwright.async_api import async_playwright
EXT="/home/claude/edushield/extension"; OUT="/home/claude/e2e"; BASE="http://127.0.0.1:8765"; PUB="http://127.0.0.1:8899"
today=datetime.date.today().isoformat()
async def main():
  async with async_playwright() as p:
    ctx=await p.chromium.launch_persistent_context(tempfile.mkdtemp(),headless=True,channel="chromium",viewport={"width":900,"height":900},args=[f"--disable-extensions-except={EXT}",f"--load-extension={EXT}","--no-proxy-server"])
    sw=ctx.service_workers[0] if ctx.service_workers else await ctx.wait_for_event("serviceworker",timeout=15000); eid=sw.url.split("/")[2]; errs=[]
    ob=[x for x in ctx.pages if "onboarding" in x.url]; ob=ob[0] if ob else await ctx.new_page(); ob.on("pageerror",lambda e:errs.append(str(e)))
    await ob.goto(f"chrome-extension://{eid}/onboarding.html"); await ob.screenshot(path=f"{OUT}/u_ob1.png"); await ob.click("#n1"); await ob.screenshot(path=f"{OUT}/u_ob2.png"); await ob.click("#n2"); await ob.click("#n3"); await ob.check("#a"); await ob.click("#go"); await ob.wait_for_timeout(300)
    pg=await ctx.new_page(); pg.on("pageerror",lambda e:errs.append(str(e))); await pg.goto(BASE+"/demo"); await pg.wait_for_timeout(1200)
    for _ in range(9): await pg.click("#next"); await pg.wait_for_timeout(350)
    await pg.wait_for_timeout(1500); await pg.evaluate("document.getElementById('edushield-root').shadowRoot.getElementById('fab').click()"); await pg.wait_for_timeout(300); await pg.screenshot(path=f"{OUT}/u_panel.png")
    pop=await ctx.new_page(); await pop.set_viewport_size({"width":340,"height":950}); await pop.goto(f"chrome-extension://{eid}/popup.html"); await pop.wait_for_timeout(600)
    await pop.evaluate("(d)=>new Promise(r=>chrome.storage.local.set({daily:{[d]:{active:true,ev:{lua_dao_bat_ky:['h']}}}},r))",today)
    await pop.click("#shareStart"); await pop.click("#shareYes"); await pop.wait_for_selector("#shareMsg",state="visible"); await pop.wait_for_timeout(400); await pop.screenshot(path=f"{OUT}/u_popup.png",full_page=True)
    md=await ctx.new_page(); await md.goto(f"chrome-extension://{eid}/mydata.html"); await md.wait_for_timeout(500); await md.screenshot(path=f"{OUT}/u_mydata.png")
    print("[EXT] lỗi:",errs); await ctx.close()
    b=await p.chromium.launch(channel="chromium",args=["--no-proxy-server"]); c=await b.new_context(**p.devices["Pixel 7"]); m=await c.new_page(); errs=[]; m.on("pageerror",lambda e:errs.append(str(e)))
    await m.goto(BASE+"/app/"); await m.wait_for_timeout(800); await m.screenshot(path=f"{OUT}/u_m1.png"); await m.click('[data-go="2"]'); await m.click('#c2 [data-go="3"]'); await m.check("#agree"); await m.click("#startBtn")
    await m.click('[data-s="0"]'); await m.wait_for_timeout(400); await m.click("#todoBtn"); await m.wait_for_timeout(300); await m.screenshot(path=f"{OUT}/u_m2.png")
    await m.click('nav button[data-t=stats]'); await m.wait_for_timeout(300); await m.screenshot(path=f"{OUT}/u_m3.png",full_page=True)
    g=await c.new_page(); await g.goto(PUB+"/cai-dat.html"); await g.wait_for_timeout(400); await g.screenshot(path=f"{OUT}/u_g.png")
    print("[APP] lỗi:",errs); await b.close()
asyncio.run(main())

import asyncio, tempfile, zipfile, io, urllib.request
from playwright.async_api import async_playwright
PUB="http://127.0.0.1:8899"; EXT="/home/claude/edushield/extension"; OUT="/home/claude/e2e"
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(channel="chromium",args=["--no-proxy-server"])
    for name,dev in (("Android",p.devices["Pixel 7"]),("iPhone",p.devices["iPhone 13"]),("PC",{"viewport":{"width":1000,"height":900}})):
      ctx=await b.new_context(**dev); pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
      await pg.goto(PUB+"/cai-dat.html"); await pg.wait_for_timeout(500)
      op={i:await pg.evaluate(f"document.getElementById('{i}').open") for i in ("d-android","d-ios")}
      print(f"[{name}] mở sẵn:",op,"| lỗi:",errs); await pg.screenshot(path=f"{OUT}/g_{name}.png",full_page=True)
    z=urllib.request.urlopen(PUB+"/EduShield_Extension.zip").read(); zf=zipfile.ZipFile(io.BytesIO(z)); print("[ZIP] tải được, số tệp:",len(zf.namelist()),"| có manifest:", "EduShield_Extension/manifest.json" in zf.namelist(), "| có config.js:", "EduShield_Extension/config.js" in zf.namelist())
    # app công khai: thẻ cài app/chia sẻ
    ctx=await b.new_context(**p.devices["Pixel 7"]); pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
    await pg.goto(PUB+"/"); await pg.wait_for_timeout(800); await pg.click('[data-go="2"]'); await pg.click('#c2 [data-go="3"]'); await pg.check("#agree"); await pg.click("#startBtn")
    await pg.click('nav button[data-t=stats]'); await pg.wait_for_timeout(300)
    print("[APP] thẻ cài app hiện:", await pg.is_visible("#installCard"), "| link hướng dẫn:", await pg.get_attribute("#installCard a","href"))
    await ctx.grant_permissions(["clipboard-read","clipboard-write"]); await pg.click("#shareApp"); await pg.wait_for_timeout(500); print("[APP] Chia sẻ (không có Web Share trên máy tính):", await pg.inner_text("#installMsg"))
    await pg.screenshot(path=f"{OUT}/g_app_cai.png",full_page=True); print("[APP] lỗi:",errs)
    await b.close()
    # trang chào hỏi tiện ích 4 bước
    ctx=await p.chromium.launch_persistent_context(tempfile.mkdtemp(),headless=True,channel="chromium",viewport={"width":900,"height":900},args=[f"--disable-extensions-except={EXT}",f"--load-extension={EXT}","--no-proxy-server"])
    sw=ctx.service_workers[0] if ctx.service_workers else await ctx.wait_for_event("serviceworker",timeout=15000); eid=sw.url.split("/")[2]
    ob=[x for x in ctx.pages if "onboarding" in x.url]; ob=ob[0] if ob else await ctx.new_page(); errs=[]; ob.on("pageerror",lambda e:errs.append(str(e)))
    await ob.goto(f"chrome-extension://{eid}/onboarding.html"); await ob.click("#n1"); await ob.click("#n2"); await ob.screenshot(path=f"{OUT}/g_onb3.png")
    await ob.click("#b3a"); await ob.click("#n2"); await ob.click("#n3"); print("[OB] Bắt đầu khoá:", await ob.is_disabled("#go")); await ob.check("#a"); await ob.click("#go"); await ob.wait_for_timeout(400)
    print("[OB]", await ob.inner_text("#ok"), "| lỗi:", errs); await ctx.close()
asyncio.run(main())

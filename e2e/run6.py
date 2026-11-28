import asyncio, json, tempfile, datetime
from playwright.async_api import async_playwright
EXT="/home/claude/edushield/extension"; OUT="/home/claude/e2e"; BASE="http://127.0.0.1:8765"
today=datetime.date.today().isoformat()
async def main():
  async with async_playwright() as p:
    ctx = await p.chromium.launch_persistent_context(tempfile.mkdtemp(), headless=True, channel="chromium", viewport={"width":1000,"height":900}, args=[f"--disable-extensions-except={EXT}", f"--load-extension={EXT}", "--no-proxy-server"])
    sw = ctx.service_workers[0] if ctx.service_workers else await ctx.wait_for_event("serviceworker", timeout=15000)
    eid = sw.url.split("/")[2]; errs=[]
    ob = [pg for pg in ctx.pages if "onboarding" in pg.url]; ob = ob[0] if ob else await ctx.new_page()
    ob.on("pageerror", lambda e: errs.append(str(e)))
    await ob.goto(f"chrome-extension://{eid}/onboarding.html"); await ob.click("#n1"); await ob.click("#b2"); await ob.click("#n1"); await ob.click("#n2"); await ob.click("#n3")
    print("[OB] Bắt đầu khoá khi chưa tích:", await ob.is_disabled("#go")); await ob.check("#a"); await ob.click("#go"); await ob.wait_for_timeout(300)
    await ob.screenshot(path=f"{OUT}/p_onboarding.png")
    pop = await ctx.new_page(); pop.on("pageerror", lambda e: errs.append(str(e))); await pop.set_viewport_size({"width":340,"height":900})
    await pop.goto(f"chrome-extension://{eid}/popup.html"); await pop.wait_for_timeout(800)
    # nạp ghi nhận mẫu của hôm nay (chỉ mã loại)
    await pop.evaluate("(d)=>new Promise(r=>chrome.storage.local.set({daily:{[d]:{active:true,ev:{lua_dao_bat_ky:['h1'],ld_otp:['h1']}}}},r))", today)
    await pop.screenshot(path=f"{OUT}/p_popup_tat.png", full_page=True)
    print("[PP] có ô Mã trường/Khối/Máy chủ?", [await pop.locator(x).count() for x in ("#school","#grade","#server")])
    await pop.click("#shareStart"); print("[PP] hiện xác nhận:", await pop.is_visible("#shareConfirm"))
    await pop.screenshot(path=f"{OUT}/p_popup_xacnhan.png", full_page=True)
    await pop.click("#shareNo"); print("[PP] Huỷ -> nút Gửi hiện lại:", await pop.is_visible("#shareStart"), "| xác nhận ẩn:", not await pop.is_visible("#shareConfirm"))
    await pop.click("#shareStart"); await pop.click("#shareYes"); await pop.wait_for_selector("#shareMsg", state="visible", timeout=15000); await pop.wait_for_timeout(500)
    print("[PP] sau Gửi:", await pop.inner_text("#shareMsg"), "| nhãn:", await pop.inner_text("#pill"))
    await pop.screenshot(path=f"{OUT}/p_popup_da_gui.png", full_page=True)
    await pop.click("#sharePreview"); print("[PP] xem gói:", (await pop.inner_text("#previewOut"))[:110].replace("\n"," "))
    await pop.click("#shareNow"); await pop.wait_for_timeout(1200); print("[PP] Gửi ngay lần 2:", await pop.inner_text("#shareMsg"))
    await pop.click("#shareOff"); await pop.wait_for_timeout(600); print("[PP] Ngừng gửi:", await pop.inner_text("#shareMsg"), "|", await pop.inner_text("#pill"))
    for ctl in ("#enabled","#siteOn","#large"): await pop.click(ctl+" + i") if await pop.locator(ctl+" + i").count() else None
    await pop.select_option("#sens","nhay")
    async with ctx.expect_page() as np_: await pop.click("#mydata")
    md = await np_.value; await md.wait_for_load_state(); print("[PP] mở Dữ liệu của tôi:", md.url.endswith("mydata.html")); await md.screenshot(path=f"{OUT}/p_mydata.png", full_page=True)
    await pop.click("#clear"); await pop.wait_for_timeout(400); print("[PP] Xoá dữ liệu: đã quét =", await pop.inner_text("#scanned"))
    print("[LỖI]", errs); await ctx.close()
asyncio.run(main())

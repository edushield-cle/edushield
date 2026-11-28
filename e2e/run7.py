import asyncio, json
from playwright.async_api import async_playwright
BASE="http://127.0.0.1:8765"; OUT="/home/claude/e2e"
async def main():
  async with async_playwright() as p:
    b = await p.chromium.launch(channel="chromium", args=["--no-proxy-server"])
    ctx = await b.new_context(**p.devices["Pixel 7"]); errs=[]; posts=[]
    pg = await ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("request", lambda r: posts.append(r.post_data) if r.method=="POST" else None)
    await pg.goto(BASE+"/app/"); await pg.wait_for_timeout(1000)
    await pg.click('[data-go="2"]'); await pg.click('#c2 [data-go="3"]'); await pg.check("#agree"); await pg.click("#startBtn")
    await pg.click('[data-s="0"]'); await pg.wait_for_timeout(500)
    await pg.click('nav button[data-t=stats]'); await pg.wait_for_timeout(300)
    print("[DT] có ô mã trường/khối/máy chủ:", [await pg.locator(x).count() for x in ("#shSchool","#shGrade","#shServer")])
    await pg.click("#shStart"); print("[DT] hiện xác nhận:", await pg.is_visible("#shConfirm"))
    await pg.screenshot(path=f"{OUT}/q_xacnhan.png", full_page=True)
    await pg.click("#shYes"); await pg.wait_for_timeout(1200); print("[DT] sau Gửi:", await pg.inner_text("#shMsg"), "|", await pg.inner_text("#shPill"))
    await pg.screenshot(path=f"{OUT}/q_dagui.png", full_page=True)
    await pg.click("#shPrev"); print("[DT] xem gói:", (await pg.inner_text("#shOut"))[:60].replace("\n"," "))
    await pg.click("#shSend"); await pg.wait_for_timeout(800); print("[DT] Gửi ngay lần 2:", await pg.inner_text("#shMsg"))
    await pg.click("#shOff"); print("[DT] Ngừng:", await pg.inner_text("#shPill"))
    print("[DT] số yêu cầu POST tới máy chủ:", len(posts), "| nội dung gói:", (posts[0] or "")[:90] if posts else None)
    print("[LỖI]", errs); await b.close()
asyncio.run(main())

import asyncio, tempfile
from playwright.async_api import async_playwright
EXT="/home/claude/edushield/extension"; URL="http://127.0.0.1:8765/demo?viewport-test"
SCAM="Cô chủ nhiệm đây, em chuyển gấp 500k tiền học phí vào stk 9999123456 nhé"
def page():
    rows=[]
    for i in range(1,41):
        t = SCAM+f" (tin số {i})" if i in (2,30) else f"tối nay học nhóm môn số {i} nhé các bạn ơi"
        rows.append(f'<div class="m" id="m{i}" style="height:90px;border-bottom:1px solid #ddd">{t}</div>')
    rows.append(f'<div id="hid1" style="display:none">{SCAM} (ẩn display none)</div>')
    rows.append(f'<div id="hid2" style="visibility:hidden;height:20px">{SCAM} (ẩn visibility)</div>')
    return "<!doctype html><meta charset=utf-8><body style='margin:0'>"+"".join(rows)+"</body>"
async def main():
  async with async_playwright() as p:
    ctx = await p.chromium.launch_persistent_context(tempfile.mkdtemp(), headless=True, channel="chromium", viewport={"width":900,"height":600}, args=[f"--disable-extensions-except={EXT}", f"--load-extension={EXT}", "--no-proxy-server"])
    sw = ctx.service_workers[0] if ctx.service_workers else await ctx.wait_for_event("serviceworker", timeout=15000); eid=sw.url.split("/")[2]; errs=[]
    ob = [x for x in ctx.pages if "onboarding" in x.url]; ob = ob[0] if ob else await ctx.new_page()
    await ob.goto(f"chrome-extension://{eid}/onboarding.html"); await ob.click("#n1"); await ob.click("#n2"); await ob.click("#n3"); await ob.check("#a"); await ob.click("#go"); await ob.wait_for_timeout(400)
    await ctx.route("http://127.0.0.1:8765/demo**", lambda r: r.fulfill(status=200, content_type="text/html; charset=utf-8", body=page()))
    pg = await ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.goto(URL); await pg.wait_for_timeout(2500)
    cards = lambda: pg.evaluate("()=>[...document.getElementById('edushield-root').shadowRoot.querySelectorAll('.msg .quote')].map(q=>q.innerText)")
    scanned = lambda: pg.evaluate("()=>new Promise(r=>chrome.storage.local.get('stats',r))") 
    c=await cards(); print("[1] Ban đầu (chỉ thấy tin 1-6): thẻ cảnh báo =", [x[-14:] for x in c])
    await pg.wait_for_timeout(5500)
    # chuyển popup đọc số đã quét
    pop=await ctx.new_page(); await pop.goto(f"chrome-extension://{eid}/popup.html"); await pop.wait_for_timeout(500)
    print("[1] số đoạn đã quét ban đầu:", await pop.inner_text("#scanned"), "(40 tin, chỉ ~7 hiện)")
    await pg.bring_to_front(); await pg.evaluate("window.scrollTo(0, document.getElementById('m30').offsetTop-100)"); await pg.wait_for_timeout(2000)
    c=await cards(); print("[2] Sau khi cuộn tới tin 30: thẻ =", [x[-14:] for x in c])
    await pg.wait_for_timeout(5500); await pop.reload(); await pop.wait_for_timeout(500); print("[2] số đoạn đã quét:", await pop.inner_text("#scanned"))
    print("[3] Tin ẩn (display none / visibility hidden) có bị quét?", any("ẩn" in x for x in c))
    await pg.screenshot(path="/home/claude/e2e/v_view.png")
    print("[LỖI]", errs); await ctx.close()
asyncio.run(main())

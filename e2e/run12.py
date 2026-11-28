import asyncio, tempfile
from playwright.async_api import async_playwright
EXT="/home/claude/edushield/extension"; OUT="/home/claude/e2e"; BASE="http://127.0.0.1:8765"
SR="document.getElementById('edushield-root').shadowRoot"
BIG="<!doctype html><meta charset=utf-8><body><div id=side style='height:200px;overflow:auto'>"+"".join(f"<div>Mục điều hướng số {i} của trang</div>" for i in range(6000))+"</div><div style='padding:20px'><div dir=auto>Cô chủ nhiệm đây, em chuyển gấp 500k tiền học phí vào stk 190355667788 nhé, không là bị khoá tài khoản</div></div></body>"
async def state(pg):
    return await pg.evaluate(f"(()=>{{const r=document.querySelectorAll('#edushield-root');if(!r.length)return {{roots:0}};const s=r[r.length-1].shadowRoot;return {{roots:r.length,shown:r[r.length-1].style.display,fabOff:s.getElementById('fab').classList.contains('off'),stat:s.getElementById('statline').textContent,stateCard:!!s.querySelector('.state'),cards:s.querySelectorAll('.msg.canh_bao,.msg.khan_cap').length}}}})()")
async def popup_state(ctx,eid,tab):
    await tab.bring_to_front()
    pop=await ctx.new_page(); await pop.goto(f"chrome-extension://{eid}/popup.html")
    # popup mở trong tab riêng nên "tab đang mở" là chính nó; kiểm tra bằng cách gửi ping trực tiếp
    await pop.close()
async def main():
  async with async_playwright() as p:
    ctx=await p.chromium.launch_persistent_context(tempfile.mkdtemp(),headless=True,channel="chromium",viewport={"width":1000,"height":800},args=[f"--disable-extensions-except={EXT}",f"--load-extension={EXT}","--no-proxy-server"])
    await ctx.route("http://127.0.0.1:8765/demo-lon", lambda r: r.fulfill(body=BIG, content_type="text/html; charset=utf-8"))
    sw=ctx.service_workers[0] if ctx.service_workers else await ctx.wait_for_event("serviceworker",timeout=15000); eid=sw.url.split("/")[2]; errs=[]
    await asyncio.sleep(1)
    for x in list(ctx.pages):
        if "onboarding" in x.url: await x.close()   # học sinh đóng màn hình đồng ý mà CHƯA tích
    pg=await ctx.new_page(); pg.on("pageerror",lambda e:errs.append(str(e))); await pg.goto(BASE+"/demo"); await pg.wait_for_timeout(1500)
    print("A. Chưa đồng ý:",await state(pg))
    ping=await sw.evaluate("(async()=>{const [t]=await chrome.tabs.query({url:'http://127.0.0.1:8765/demo*'});return await chrome.tabs.sendMessage(t.id,{type:'ping'})})()")
    print("   ping:",ping)
    await pg.evaluate(f"{SR}.getElementById('fab').click()"); await pg.wait_for_timeout(300); await pg.screenshot(path=f"{OUT}/x1_chua_bat.png")
    # B. đồng ý ở màn hình chào hỏi -> tab đang mở tự bắt đầu quét
    ob=await ctx.new_page(); await ob.goto(f"chrome-extension://{eid}/onboarding.html"); await ob.click("#n1"); await ob.click("#n2"); await ob.click("#n3"); await ob.check("#a"); await ob.click("#go"); await ob.wait_for_timeout(400)
    await pg.bring_to_front()
    for _ in range(4): await pg.click("#next"); await pg.wait_for_timeout(500)
    await pg.wait_for_timeout(800); print("B. Sau khi đồng ý:",await state(pg))
    # C. trang lớn (6000 nút chữ trước tin nhắn)
    big=await ctx.new_page(); big.on("pageerror",lambda e:errs.append(str(e))); await big.goto(BASE+"/demo-lon"); await big.wait_for_timeout(2500)
    print("C. Trang 6000 nút chữ:",await state(big))
    # D. tiện ích được nạp lại vào tab đang mở (như sau khi cài lại/tải lại)
    await sw.evaluate("injectIntoOpenTabs()"); await big.wait_for_timeout(2500)
    print("D. Sau khi nạp lại:",await state(big))
    # E. trang thử nghiệm có sẵn trong tiện ích
    t=await ctx.new_page(); t.on("pageerror",lambda e:errs.append(str(e))); await t.goto(f"chrome-extension://{eid}/thu-nghiem.html"); await t.wait_for_timeout(1500)
    s1=await state(t); await t.mouse.wheel(0,3000); await t.wait_for_timeout(1500); s2=await state(t)
    await t.fill("#txt","Tuyển CTV việc nhẹ lương cao 500k/ngày, chỉ cần đặt cọc 200k là nhận việc"); await t.click("#send"); await t.wait_for_timeout(1500); s3=await state(t)
    print("E. Trang thử nghiệm:",s1["stat"],"| sau cuộn:",s2["stat"],"| sau gửi tin:",s3["stat"])
    await t.screenshot(path=f"{OUT}/x2_thu_nghiem.png")
    # F. popup: thẻ "Trên trang này" (mở popup như một trang, trỏ tab đang hoạt động là trang thử nghiệm)
    pop=await ctx.new_page(); await pop.set_viewport_size({"width":340,"height":700})
    await pop.goto(f"chrome-extension://{eid}/popup.html"); await pop.wait_for_timeout(800)
    print("F. Popup (tab hiện tại là chính popup):",await pop.text_content("#pageState"))
    await pop.screenshot(path=f"{OUT}/x3_popup.png")
    print("Lỗi trang:",errs); await ctx.close()
asyncio.run(main())

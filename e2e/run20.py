# Kiểm thử v1.9: nhắc trước khi gửi tin có thể gây tổn thương / lừa đảo, và làm mờ ảnh bạo lực
import asyncio, tempfile, subprocess, sys, time, urllib.request
from playwright.async_api import async_playwright
EXT="/home/claude/edushield/extension"; OUT="/home/claude/e2e"; B="http://127.0.0.1:8765"
NR="document.getElementById('edushield-nudge').shadowRoot"
def mine(): return "[...document.querySelectorAll('.bubble')].map(b=>b.textContent)"
async def main():

  async with async_playwright() as p:
    ctx=await p.chromium.launch_persistent_context(tempfile.mkdtemp(),headless=True,channel="chromium",viewport={"width":1000,"height":820},
          args=[f"--disable-extensions-except={EXT}",f"--load-extension={EXT}","--no-proxy-server"])
    sw=ctx.service_workers[0] if ctx.service_workers else await ctx.wait_for_event("serviceworker",timeout=15000); eid=sw.url.split("/")[2]
    await asyncio.sleep(1)
    ob=[x for x in ctx.pages if "onboarding" in x.url]; ob=ob[0] if ob else await ctx.new_page()
    await ob.goto(f"chrome-extension://{eid}/onboarding.html"); await ob.click("#n1"); await ob.click("#n2"); await ob.click("#n3"); await ob.check("#a"); await ob.click("#go"); await ob.wait_for_timeout(300)
    t=await ctx.new_page(); errs=[]; t.on("pageerror",lambda e:errs.append(str(e)))
    await t.goto(f"chrome-extension://{eid}/thu-nghiem.html"); await t.wait_for_timeout(1500)
    shown=lambda: t.evaluate("(()=>{const h=document.getElementById('edushield-nudge');return !!h&&h.style.display==='block'})()")
    title=lambda: t.evaluate(f"{NR}.getElementById('t').textContent")
    async def nb(label): await t.evaluate(f"[...{NR}.querySelectorAll('button')].find(b=>b.textContent.includes({label!r})).click()")
    async def count(s): return await t.evaluate(f"{mine()}.filter(x=>x.includes({s!r})).length")

    # 1. Ảnh có chữ đi kèm mô tả đánh hội đồng -> bị làm mờ, chọn Vẫn xem thì rõ lại
    img=t.locator("img[alt*='hội đồng']"); await img.scroll_into_view_if_needed(); await t.wait_for_timeout(1800)
    f7=await img.evaluate("e=>e.style.filter"); s7=await shown()
    print("1. Ảnh bạo lực: filter =", f7, "| hiện thẻ:", s7, "|", await title())
    assert "blur" in f7 and s7
    await t.screenshot(path=f"{OUT}/v19_lam_mo.png")
    await nb("Vẫn xem"); f7b=await img.evaluate("e=>e.style.filter")
    print("   'Vẫn xem' -> filter =", repr(f7b)); assert "blur" not in f7b
    other=await t.evaluate("[...document.querySelectorAll('img')].filter(i=>!i.alt.includes('hội đồng')&&i.style.filter.includes('blur(26')).length")
    print("   Ảnh khác bị mờ nhầm:", other); assert other==0
    # 2. Tin bắt nạt + Enter -> hiện lời nhắc, tin CHƯA được gửi
    bad="mày béo như con lợn, cả lớp ghét mày, đừng đến trường nữa"
    await t.fill("#txt",bad); await t.press("#txt","Enter"); await t.wait_for_timeout(400)
    s1=await shown(); c1=await count("béo như con lợn")
    print("2. Bắt nạt + Enter: hiện nhắc:", s1, "|", await title(), "| đã gửi:", c1)
    assert s1 and c1==0
    await t.screenshot(path=f"{OUT}/v19_nhac_bat_nat.png")
    # 3. Bấm gợi ý viết lại -> ô nhập đổi sang câu nhẹ nhàng; gửi đi được ngay
    await t.evaluate(f"{NR}.querySelector('.rw button').click()"); v=await t.input_value("#txt")
    await t.press("#txt","Enter"); await t.wait_for_timeout(300)
    print("3. Chọn câu gợi ý:", v, "| gửi được:", await count(v)==1, "| nhắc đóng:", not await shown(), "|", await title())
    assert await count(v)==1 and not await shown()
    # 4. Mã OTP qua nút Gửi -> nhắc; Vẫn gửi -> tin đi
    await t.fill("#txt","Mã OTP của mình là 482913 nè"); await t.click("#send"); await t.wait_for_timeout(300)
    s3=await shown(); print("4. OTP + nút Gửi: hiện nhắc:", s3, "|", await title())
    assert s3 and await count("482913")==0
    await t.screenshot(path=f"{OUT}/v19_nhac_otp.png")
    await nb("Vẫn gửi"); await t.wait_for_timeout(300)
    print("   Bấm 'Vẫn gửi' -> đã gửi:", await count("482913")==1); assert await count("482913")==1
    # 5. Bấm Enter lần nữa với đúng tin đó khi lời nhắc đang mở = vẫn gửi (không chặn học sinh)
    await t.fill("#txt",bad); await t.press("#txt","Enter"); await t.wait_for_timeout(300); assert await shown()
    await t.press("#txt","Enter"); await t.wait_for_timeout(300)
    print("5. Enter lần 2 khi đang nhắc -> đã gửi:", await count("béo như con lợn")==1, "| nhắc đóng:", not await shown())
    assert await count("béo như con lợn")==1 and not await shown()
    # 6. Tin bình thường -> không nhắc
    await t.fill("#txt","Tối nay mấy giờ học nhóm vậy?"); await t.press("#txt","Enter"); await t.wait_for_timeout(300)
    print("6. Tin bình thường: không nhắc:", not await shown(), "| đã gửi:", await count("học nhóm vậy")==1)
    assert not await shown() and await count("học nhóm vậy")==1
    # 7. "Không gửi nữa" xoá tin
    await t.fill("#txt","đồ ngu, câm mồm đi, không ai muốn chơi với mày đâu"); await t.press("#txt","Enter"); await t.wait_for_timeout(300)
    await nb("Không gửi nữa"); print("7. 'Không gửi nữa': ô nhập trống:", await t.input_value("#txt")=="", "| không gửi:", await count("câm mồm")==0)
    assert await t.input_value("#txt")=="" and await count("câm mồm")==0
    # 8. Cửa sổ tiện ích: đếm số lần (chỉ con số, không lưu nội dung tin)
    pp=await ctx.new_page(); await pp.goto(f"chrome-extension://{eid}/popup.html"); await pp.wait_for_timeout(600)
    line=await pp.inner_text("#nudgeLine"); stats=await sw.evaluate("new Promise(r=>chrome.storage.local.get('nudgeStats',x=>r(x.nudgeStats)))")
    print("8. Popup:", line, "| lưu:", stats)
    assert stats["shown"]>=4 and stats["blurred"]>=1
    await pp.screenshot(path=f"{OUT}/v19_popup.png")
    # 9. Tắt công tắc -> không nhắc nữa
    await sw.evaluate("chrome.storage.local.set({sendNudge:false})"); await t.wait_for_timeout(400)
    await t.fill("#txt","Mã OTP của mình là 111222 nè"); await t.press("#txt","Enter"); await t.wait_for_timeout(300)
    print("9. Tắt 'Nhắc trước khi gửi': gửi thẳng:", await count("111222")==1, "| lỗi JS:", errs)
    assert await count("111222")==1 and not errs
    await ctx.close()
  # 10. App điện thoại: ô "Tin mình sắp gửi"
  srv=subprocess.Popen([sys.executable,"server.py"],cwd="/home/claude/edushield",stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  try:
    for _ in range(40):
      try: urllib.request.urlopen(B+"/health"); break
      except Exception: time.sleep(0.5)
    async with async_playwright() as p:
      b=await p.chromium.launch(args=["--no-proxy-server"])
      m=await (await b.new_context(viewport={"width":400,"height":860},device_scale_factor=2)).new_page(); e2=[]; m.on("pageerror",lambda e:e2.append(str(e)))
      await m.goto(B+"/app/"); await m.wait_for_timeout(600)
      await m.click("[data-go='2']"); await m.click("[data-go='3']"); await m.check("#agree"); await m.click("#startBtn"); await m.wait_for_timeout(400)
      await m.fill("#outTxt","mày béo như con lợn, cả lớp ghét mày"); await m.click("#outBtn"); await m.wait_for_timeout(300)
      r=(await m.inner_text("#outRes")).replace("\n"," ")
      print("10. App - tin sắp gửi:", r[:110]); assert "Khoan" in r
      await m.locator("#outCard").scroll_into_view_if_needed(); await m.screenshot(path=f"{OUT}/v19_app_out.png")
      await m.click("#outRes .chip >> nth=0"); await m.wait_for_timeout(200)
      r2=(await m.inner_text("#outRes")).replace("\n"," ")
      print("    Chọn câu gợi ý ->", await m.input_value("#outTxt"), "|", r2[:60], "| lỗi JS:", e2)
      assert "Khoan" not in r2 and not e2
      await b.close()
  finally: srv.terminate()
  print("OK: v1.9 nhắc trước khi gửi và làm mờ ảnh bạo lực hoạt động; học sinh luôn được quyền 'Vẫn gửi'/'Vẫn xem'")
asyncio.run(main())

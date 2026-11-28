# Kiểm thử v1.5.1: tiện ích nói rõ vì sao không gửi được thống kê
import asyncio, tempfile, json, shutil, os, threading, subprocess, sys, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from playwright.async_api import async_playwright
SRC="/home/claude/edushield/extension"; OUT="/home/claude/e2e"

class Fake502(BaseHTTPRequestHandler):  # giống Codespace đang mở nhưng server.py không chạy
    def do_GET(self): self.send_response(502); self.send_header("Content-Length","3"); self.end_headers(); self.wfile.write(b"bad")
    do_POST=do_GET
    def log_message(self,*a): pass

def make_ext(server, extra_host=None):
    d=tempfile.mkdtemp(); e=os.path.join(d,"ext"); shutil.copytree(SRC,e)
    open(os.path.join(e,"config.js"),"w").write('globalThis.EDUSHIELD_DEPLOY = { school: "THPT_ABC", server: "%s" };\n'%server)
    if extra_host:
        m=json.load(open(os.path.join(e,"manifest.json"))); m["host_permissions"].append(extra_host); json.dump(m,open(os.path.join(e,"manifest.json"),"w"))
    return e

async def popup_state(p, ext, name):
    ctx=await p.chromium.launch_persistent_context(tempfile.mkdtemp(),headless=True,channel="chromium",viewport={"width":420,"height":900},args=[f"--disable-extensions-except={ext}",f"--load-extension={ext}","--no-proxy-server"])
    sw=ctx.service_workers[0] if ctx.service_workers else await ctx.wait_for_event("serviceworker",timeout=15000); eid=sw.url.split("/")[2]
    pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
    await pg.goto(f"chrome-extension://{eid}/popup.html"); await pg.wait_for_timeout(2500)
    st=await pg.evaluate("""({s:document.getElementById('server').textContent, url:document.getElementById('serverUrl').textContent,
      why:document.getElementById('serverReason').textContent, grant:getComputedStyle(document.getElementById('grantBtn')).display,
      box:getComputedStyle(document.getElementById('serverWhy')).display})""")
    print(name, json.dumps(st, ensure_ascii=False), "lỗi JS:", errs)
    if st["box"]!="none": await pg.locator("#serverWhy").scroll_into_view_if_needed()
    await pg.screenshot(path=f"{OUT}/z_{name}.png", full_page=True)
    await ctx.close(); return st

async def main():
    srv=ThreadingHTTPServer(("127.0.0.1",8771),Fake502); threading.Thread(target=srv.serve_forever,daemon=True).start()
    async with async_playwright() as p:
        a=await popup_state(p, make_ext("http://127.0.0.1:8765"), "A_local_tat")            # nạp từ thư mục gốc, máy mình không chạy server
        b=await popup_state(p, make_ext("http://127.0.0.1:8771","http://127.0.0.1:8771/*"), "B_502")   # Codespace mở, server.py tắt
        c=await popup_state(p, make_ext("http://127.0.0.1:8779","http://127.0.0.1:8779/*"), "C_khong_toi")  # Codespace dừng
        d=await popup_state(p, make_ext("https://abc-8765.app.github.dev"), "D_link_codespace")  # chưa cấp quyền
        assert "CHÍNH máy này" in a["why"]; assert "server.py không chạy" in b["why"]; assert "Codespace đã dừng" in c["why"]
        # v1.6: tiện ích có quyền trên mọi trang web nên không còn bước "cho phép kết nối"
        assert d["grant"]=="none" and "Không tới được máy chủ" in d["why"]
        # E: máy chủ chạy thật -> ô chẩn đoán ẩn
        proc=subprocess.Popen([sys.executable,"/home/claude/edushield/server.py"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        import urllib.request
        for _ in range(40):  # máy chủ huấn luyện mô hình khi khởi động (v1.7 dữ liệu lớn hơn): chờ tới khi /health trả lời
            time.sleep(0.5)
            try: urllib.request.urlopen("http://127.0.0.1:8765/health", timeout=1); break
            except Exception: pass
        try:
            e=await popup_state(p, make_ext("http://127.0.0.1:8765"), "E_dang_chay"); assert e["box"]=="none" and "đang kết nối" in e["s"]
        finally: proc.terminate()
    print("OK: cả 5 tình huống đều báo đúng nguyên nhân (v1.6: không cần bước cấp quyền)")
asyncio.run(main())

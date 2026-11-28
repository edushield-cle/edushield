// Gắn giao diện diễn tập vào trang; nếu chạy trong tiện ích thì báo cho nền (background) lên lịch lần sau.
(function () {
  const onSchedule = (st) => {
    try { if (globalThis.chrome && chrome.runtime && chrome.runtime.sendMessage) chrome.runtime.sendMessage({ type: "drillSchedule", next: st.next }); } catch (e) {}
    try { if (window.EduShieldAndroid) window.EduShieldAndroid.schedule(String(st.next || 0)); } catch (e) {}
    try { if (window.webkit && webkit.messageHandlers && webkit.messageHandlers.drill) webkit.messageHandlers.drill.postMessage({ next: st.next || 0 }); } catch (e) {}
  };
  EduShieldDrill.mount(document.getElementById("root"), { onSchedule });

  // Nút "← Màn hình chính": về giao diện chính của nơi đang chạy (app Android, app iPhone, tiện ích, app web).
  const goHome = () => {
    try { if (window.EduShieldAndroid && window.EduShieldAndroid.home) { window.EduShieldAndroid.home(); return; } } catch (e) {}
    try { if (window.webkit && webkit.messageHandlers && webkit.messageHandlers.drill) { webkit.messageHandlers.drill.postMessage({ home: true }); return; } } catch (e) {}
    if (location.protocol === "chrome-extension:") { location.href = "popup.html?full=1"; return; } // giao diện tiện ích, mở ngay trong tab này
    location.href = "index.html";
  };
  const back = document.getElementById("dBack");
  if (back) back.onclick = goHome;
})();

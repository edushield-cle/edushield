const $ = (i) => document.getElementById(i);
const N = 4;
function show(n) { for (let k = 1; k <= N; k++) $("s" + k).classList.toggle("hide", k !== n); document.querySelectorAll(".dots i").forEach((d, i) => d.classList.toggle("on", i === n - 1)); }
$("n1").onclick = () => show(2); $("b2").onclick = () => show(1); $("n2").onclick = () => show(3);
$("b3a").onclick = () => show(2); $("n3").onclick = () => show(4); $("b4").onclick = () => show(3);
$("a").onchange = () => ($("go").disabled = !$("a").checked);
$("go").onclick = () => chrome.storage.local.set({ consented: true }, () => {
  $("ok").innerHTML = "✅ Đã bật. Các tab đang mở cũng được bảo vệ ngay. Muốn xem EduShield hoạt động thế nào? ";
  const b = document.createElement("button"); b.textContent = "🧪 Thử ngay trên trang mô phỏng";
  b.onclick = () => (location.href = chrome.runtime.getURL("thu-nghiem.html"));
  $("ok").appendChild(b); $("go").disabled = true;
});

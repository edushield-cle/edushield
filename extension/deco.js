// Lớp nền trang trí: các biểu tượng trôi nhẹ phía sau nội dung (không bắt chuột, tự đứng yên nếu máy đặt "giảm chuyển động").
(function () {
  if (document.getElementById("es-deco")) return;
  const ICONS = ["🛡️", "💬", "🔒", "✨", "📱", "🔍", "💡", "🌐", "🔔", "✅", "🧠", "🤝", "📚", "⭐"];
  // vị trí rải đều quanh mép, tránh giữa trang để không rối mắt
  const SPOTS = [[4, 8], [88, 5], [12, 30], [93, 26], [3, 52], [90, 48], [8, 76], [86, 72], [46, 3], [52, 95], [24, 92], [72, 88], [30, 14], [68, 18]];
  const st = document.createElement("style");
  st.textContent = "#es-deco{position:fixed;inset:0;pointer-events:none;z-index:-1;overflow:hidden}" +
    "#es-deco span{position:absolute;opacity:.16;user-select:none;animation:esFloat var(--d) ease-in-out var(--dl) infinite alternate}" +
    "@keyframes esFloat{from{transform:translate(0,0) rotate(-8deg) scale(1)}to{transform:translate(var(--x),var(--y)) rotate(10deg) scale(1.08)}}" +
    "@media (prefers-reduced-motion: reduce){#es-deco span{animation:none}}@media (prefers-color-scheme: dark){#es-deco span{opacity:.12}}";
  const box = document.createElement("div");
  box.id = "es-deco"; box.setAttribute("aria-hidden", "true");
  SPOTS.forEach(([x, y], i) => {
    const s = document.createElement("span");
    s.textContent = ICONS[i % ICONS.length];
    const size = 18 + ((i * 7) % 18);
    s.style.cssText = `left:${x}%;top:${y}%;font-size:${size}px;--d:${6 + (i % 5) * 1.7}s;--dl:-${i * 0.9}s;--x:${(i % 2 ? 1 : -1) * (8 + (i % 4) * 4)}px;--y:${(i % 3 ? -1 : 1) * (10 + (i % 5) * 3)}px`;
    box.appendChild(s);
  });
  document.head.appendChild(st);
  document.body.insertBefore(box, document.body.firstChild);
})();

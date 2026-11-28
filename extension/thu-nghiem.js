// Trang thử nghiệm: dựng một nhóm chat mô phỏng để kiểm tra EduShield mà không cần máy chủ hay tài khoản mạng xã hội.
(function () {
  const PEOPLE = { An: "#e85d04", Bình: "#1a7f37", Chi: "#8250df", "Cô Lan (giả)": "#d1242f", "Tài khoản lạ": "#57606a", Mình: "#0084ff" };
  const CHAT = [
    ["An", "Chào cả nhóm, mai mình họp lúc 7 giờ nhé"],
    ["Bình", "Ok, nhớ mang bản kế hoạch bài thuyết trình"],
    ["Chi", "Mai nhớ mang sách Toán nha, cô dặn kiểm tra 15 phút"],
    ["Cô Lan (giả)", "Cô chủ nhiệm đây, em chuyển gấp 500k tiền học phí vào stk 190355667788 nhé, không là bị khoá tài khoản"],
    ["An", "Ủa cô nhắn qua tài khoản này hả?"],
    ["Bình", "Tối nay ai rảnh ôn Lý cùng mình không?"],
    ["Chi", "Haha hôm qua đá bóng vui ghê"],
    ["An", "Mình gửi đề cương Văn ở nhóm lớp rồi đó"],
    ["Bình", "Cảm ơn An nhiều nha"],
    ["Chi", "Thứ bảy này lớp mình đi dã ngoại đúng không?"],
    ["An", "Đúng rồi, tập trung ở cổng trường lúc 6 giờ 30"],
    ["Bình", "Nhớ mang nước với mũ nha mọi người"],
    ["Tài khoản lạ", "Đồ ngu, cả lớp ghét mày, biến đi cho khuất mắt"],
    ["Chi", "Ai vậy? Sao nói vậy với bạn?"],
    ["An", "Mọi người đừng trả lời, chụp màn hình lại rồi báo cô nhé"],
    ["Bình", "Bài tập Hoá trang 45 làm câu mấy vậy?"],
    ["Chi", "Câu 2 với câu 5 thôi"],
    ["An", "Cuối tuần có ai đi thư viện không?"],
    ["Tài khoản lạ", "Chúc mừng bạn trúng thưởng iPhone, gửi mã OTP vừa nhận để nhận quà nhé"],
    ["Bình", "Đừng ai gửi OTP nha, lừa đảo đó"],
    ["Chi", "Mình chặn tài khoản đó rồi"],
    ["An", "Chiều nay CLB tiếng Anh họp phòng 204"],
    ["Tài khoản lạ", "Mày mà mách cô thì đừng trách tao, tan học tao chờ ở cổng"],
    ["Bình", "Mình báo thầy giám thị rồi, cậu đừng lo"],
    ["Chi", "Tối nay xem trận bóng không mọi người?"],
    ["Tài khoản lạ", "Đây là cán bộ công an, em có liên quan đến một vụ án rửa tiền, tuyệt đối không được nói với bố mẹ, phải thuê phòng khách sạn ở một mình"],
    ["An", "Công an không làm việc qua tin nhắn đâu, báo bố mẹ ngay nhé"],
    ["Chi", "Đoàn trường vừa đăng: kẻ gian giả danh công an gọi điện doạ học sinh dính vụ án, bắt giữ bí mật rồi đòi chuyển tiền. Tuyệt đối không làm theo, hãy báo bố mẹ"],
    ["Bình", "Cô dặn: ai nhắn xin mã OTP hay rủ “việc nhẹ lương cao, nạp trước 200k” thì đều là lừa đảo, gặp là báo cô nhé"],
  ];
  const SAMPLES = ["Tuyển CTV việc nhẹ lương cao 500k/ngày, chỉ cần đặt cọc 200k là nhận việc", "Mai nhớ mang áo đồng phục nha", "Cả lớp ghét mày, đừng vào nhóm nữa", "Mã OTP của mình là 482913 nè"];
  const box = document.getElementById("msgs");
  function add(who, text) {
    const row = document.createElement("div");
    row.className = "mrow" + (who === "Mình" ? " me" : "");
    const av = document.createElement("div");
    av.className = "av"; av.style.background = PEOPLE[who] || "#57606a"; av.textContent = who[0];
    const wrap = document.createElement("div");
    if (who !== "Mình") { const w = document.createElement("div"); w.className = "who"; w.textContent = who; wrap.appendChild(w); }
    const b = document.createElement("div");
    b.className = "bubble"; b.setAttribute("dir", "auto"); b.textContent = text;
    wrap.appendChild(b); row.appendChild(av); row.appendChild(wrap); box.appendChild(row);
    return row;
  }
  CHAT.forEach(([w, t], i) => {
    add(w, t);
    // Ảnh và video mô phỏng: EduShield chỉ kiểm tra sau khi bạn XEM chúng ít nhất 5 giây
    if (i === 9) addMedia("Tài khoản lạ", () => { const im = document.createElement("img"); im.src = "thu-nghiem-anh.png"; im.width = 320; im.height = 150;
      im.alt = "Tuyển cộng tác viên gấp. Việc nhẹ lương cao 500k/ngày, chỉ cần đặt cọc 200k để nhận việc"; return im; });
    // v1.9: ảnh có chữ đi kèm mô tả bạo lực -> EduShield làm mờ ngay khi ảnh hiện ra
    if (i === 21) addMedia("Tài khoản lạ", () => { const im = document.createElement("img"); im.src = "thu-nghiem-anh-2.png"; im.width = 320; im.height = 180;
      im.alt = "Clip học sinh bị đánh hội đồng sau giờ học, ai muốn xem full thì vào nhóm"; return im; });
    if (i === 16) addMedia("Tài khoản lạ", () => { const v = document.createElement("video"); v.src = "thu-nghiem-video.webm"; v.width = 320; v.height = 180; v.controls = true; v.muted = true; v.loop = true; v.autoplay = true;
      const tr = document.createElement("track"); tr.kind = "subtitles"; tr.srclang = "vi"; tr.label = "Tiếng Việt"; tr.src = "thu-nghiem-video.vtt"; tr.default = true; v.appendChild(tr); return v; });
  });
  function addMedia(who, make) {
    const row = add(who, "");
    const b = row.querySelector(".bubble"); b.textContent = ""; b.style.padding = "6px"; b.appendChild(make());
  }
  const pick = document.getElementById("pick"), txt = document.getElementById("txt");
  SAMPLES.forEach((t) => { const o = document.createElement("option"); o.value = t; o.textContent = t.slice(0, 38) + "…"; pick.appendChild(o); });
  pick.onchange = () => { txt.value = pick.value; };
  const go = () => { const t = txt.value.trim(); if (!t) return; add("Mình", t).scrollIntoView({ behavior: "smooth", block: "end" }); txt.value = ""; pick.value = ""; };
  document.getElementById("send").onclick = go;
  txt.addEventListener("keydown", (e) => { if (e.key === "Enter") go(); });
})();

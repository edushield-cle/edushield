// EduShield - bộ phát hiện chạy HOÀN TOÀN trong trình duyệt. Không gửi dữ liệu đi đâu.
(function (g) {
  const M = g.EDUSHIELD_MODEL;
  const RX_URL = new RegExp(M.regex.url, "g");
  const RX_PHONE = new RegExp(M.regex.phone, "g");
  const RX_NUM = new RegExp(M.regex.num, "g");
  const SIGNALS = M.signals.map(([label, pat, desc, sev, cat]) => ({ label, re: new RegExp(pat), desc, sev, cat }));
  // v1.7: đặc trưng khung ngữ cảnh (tuyên truyền, kể lại, trích dẫn...) - cùng biểu thức với bản Python
  const FRAME = (M.frame || []).map(([name, pat]) => [name, new RegExp(pat)]);
  const RX_QUOTE = M.quote ? new RegExp(M.quote, "g") : null;
  const HARM = ["bat_nat", "lua_dao"];
  const VI = { binh_thuong: "Bình thường", bat_nat: "Dấu hiệu bắt nạt", lua_dao: "Dấu hiệu lừa đảo", tuyen_truyen: "Thông tin tuyên truyền, cảnh báo" };
  const ADVICE = {
    bat_nat: "Bạn không có lỗi gì cả. Đừng trả lời lại khi đang bực. Hãy chụp màn hình lưu bằng chứng, chặn người gửi và nói với thầy cô, cha mẹ hoặc phòng tư vấn. Nếu thấy không an toàn, gọi Tổng đài 111 (miễn phí, 24/7).",
    lua_dao: "Đừng bấm link, đừng chuyển tiền, tuyệt đối không gửi mã OTP hay mật khẩu. Nếu tin nhắn tự nhận là thầy cô hay người thân, hãy gọi điện trực tiếp cho họ để kiểm tra. Chụp màn hình, chặn và báo cáo tài khoản.",
  };

  function strip(s) {
    return s.replace(/đ/g, "d").replace(/Đ/g, "D").normalize("NFD").replace(/[̀-ͯ]/g, "");
  }

  const AL = g.EDUSHIELD_ALLOWLIST || { domains: [], suffixes: [] };
  function trustedHost(h) {
    return AL.suffixes.some((s) => h.endsWith(s)) || AL.domains.some((d) => h === d || h.endsWith("." + d));
  }
  function hostOf(u) {
    return u.toLowerCase().replace(/^https?:\/\//, "").replace(/^www\./, "").split(/[/?#]/)[0].replace(/[.,;:!)]+$/, "");
  }
  function norm(t) {
    t = strip(t).toLowerCase();
    const urls = t.match(RX_URL) || [];
    const tok = urls.length && urls.every((u) => trustedHost(hostOf(u))) ? " linkoktoken " : " urltoken ";
    t = t.replace(RX_URL, tok).replace(RX_PHONE, " phonetoken ").replace(RX_NUM, " numtoken ");
    t = t.replace(/[^a-z0-9]+/g, " ");
    return t.trim().split(/\s+/).filter(Boolean).join(" ");
  }

  function feats(n, text) {
    const toks = n ? n.split(" ") : [];
    const s = new Set(toks);
    for (let i = 0; i + 1 < toks.length; i++) s.add(toks[i] + " " + toks[i + 1]);
    for (const [name, re] of FRAME) if (re.test(n)) s.add(name);
    if (RX_QUOTE && text && (text.match(RX_QUOTE) || []).length >= 2) s.add("__trich");
    return s;
  }

  function predict(text) {
    const n = norm(text);
    const z = M.intercept.slice();
    for (const f of feats(n, text)) {
      const w = M.weights[f];
      if (w) for (let c = 0; c < z.length; c++) z[c] += w[c];
    }
    const mx = Math.max(...z);
    const e = z.map((v) => Math.exp(v - mx));
    const sum = e.reduce((a, b) => a + b, 0);
    return { norm: n, probs: e.map((v) => v / sum) };
  }

  // Độ nhạy do học sinh chọn: it = ít phiền, can_bang = mặc định, nhay = nhạy hơn
  const SENS = { it: 0.15, can_bang: 0, nhay: -0.15 };
  const FRIENDLY = {
    bat_nat: "Bạn không có lỗi. Đừng đáp trả lúc đang bực.",
    lua_dao: "Đừng làm theo khi chưa kiểm tra.",
  };
  // Tên ngắn của từng nhóm nguy cơ (hiện ở tiêu đề cảnh báo)
  const CAT_VI = {
    ld_otp: "Xin mã OTP / mật khẩu", ld_chuyen_tien: "Đòi chuyển tiền", ld_trung_thuong: "Trúng thưởng giả",
    ld_viec_lam: "Việc nhẹ lương cao", ld_de_doa: "Giả danh công an, doạ khoá tài khoản", ld_thong_tin: "Đòi thông tin cá nhân",
    ld_the_cao: "Nhờ mua thẻ cào", ld_khac: "Lôi kéo, cá cược, tài khoản ảo", link_nguy_hiem: "Link nguy hiểm",
    bn_de_doa: "Đe doạ", bn_phat_tan: "Doạ tung ảnh, bí mật", bn_tran_lot: "Trấn lột, ép đưa tiền",
    bn_lang_ma: "Lăng mạ, miệt thị", bn_co_lap: "Cô lập, tẩy chay", bn_tin_don: "Tung tin đồn", bn_khac: "Kêu gọi tấn công tập thể",
  };
  // Việc nên làm ngay (không tự động làm thay bạn, chỉ gợi ý)
  const TODO = {
    bat_nat: ["Đừng trả lời lại khi đang bực.", "Chụp màn hình để lưu bằng chứng, đừng xoá tin.", "Chặn người gửi và báo cáo trên ứng dụng bạn đang dùng.", "Nói với một người lớn bạn tin (thầy cô, cha mẹ, phòng tư vấn). Cần giúp gấp: gọi 111."],
    lua_dao: ["Đừng bấm link, đừng chuyển tiền.", "Tuyệt đối không gửi mã OTP hay mật khẩu cho ai.", "Gọi điện trực tiếp cho người đang được nhắc tên để xác nhận.", "Chụp màn hình, chặn và báo cáo tài khoản. Cần giúp: gọi 111 hoặc hỏi thầy cô."],
  };
  // Các bước RIÊNG cho từng nhóm nguy cơ (khi bấm "Cần làm gì ngay?")
  const TODO_CAT = {
    ld_otp: ["Không đọc, không gửi mã OTP hay mật khẩu cho bất kỳ ai, kể cả người xưng là ngân hàng, nhà mạng, bạn bè.",
      "Ngân hàng và nhà mạng không bao giờ xin mã OTP qua tin nhắn hay cuộc gọi.",
      "Lỡ gửi mã: đổi mật khẩu ngay, đăng xuất khỏi mọi thiết bị, bật xác thực hai lớp.",
      "Nếu mã liên quan đến tài khoản ngân hàng: báo cha mẹ và gọi tổng đài in trên thẻ để khoá tạm."],
    ld_chuyen_tien: ["Chưa chuyển đồng nào khi chưa xác minh, dù người đó giục “gấp”.",
      "Gọi điện trực tiếp vào số quen của người được nhắc tên (thầy cô, người thân) để hỏi lại.",
      "Tiền học phí, quỹ lớp chỉ nộp theo thông báo chính thức của trường, không qua tài khoản lạ.",
      "Lỡ chuyển: báo ngay cha mẹ, gọi tổng đài ngân hàng yêu cầu tra soát, lưu lại biên lai và tin nhắn."],
    ld_trung_thuong: ["Bạn không tham gia thì không thể trúng thưởng.",
      "Giải thưởng thật không bắt đóng phí, nạp thẻ hay nhập mật khẩu để nhận.",
      "Không bấm link “nhận quà”; tự tìm trang chính thức của chương trình để kiểm tra.",
      "Chặn và báo cáo tài khoản gửi tin."],
    ld_viec_lam: ["Việc thật không bắt đặt cọc, nạp tiền hay “làm nhiệm vụ” để rút lãi.",
      "Lãi gấp đôi trong vài phút là dấu hiệu lừa đảo kinh điển: lần đầu được trả để bạn nạp nhiều hơn.",
      "Không cài ứng dụng lạ, không gửi ảnh giấy tờ để “đăng ký việc”.",
      "Hỏi cha mẹ hoặc thầy cô trước khi nhận bất kỳ việc làm online nào."],
    ld_de_doa: ["Công an, toà án, ngân hàng không làm việc qua tin nhắn hay mạng xã hội và không đòi chuyển tiền.",
      "Ai bắt bạn giữ bí mật với bố mẹ, ở một mình trong phòng hay khách sạn để “phục vụ điều tra” là lừa đảo “bắt cóc online”: gọi ngay cho bố mẹ hoặc 113.",
      "Câu doạ “trong 24 giờ”, “bị khoá ngay” là để bạn hoảng mà làm theo. Hãy dừng lại.",
      "Không bấm link “xác minh”; tự mở ứng dụng chính thức hoặc gọi số tổng đài in trên thẻ.",
      "Kể với cha mẹ trước khi làm bất cứ điều gì."],
    ld_thong_tin: ["Không gửi ảnh CCCD, ngày sinh, địa chỉ, mật khẩu cho người lạ.",
      "Thông tin này có thể bị dùng để mở tài khoản, vay tiền hay giả danh bạn.",
      "Nếu là việc của trường, hỏi lại giáo viên chủ nhiệm qua kênh chính thức.",
      "Lỡ gửi: báo cha mẹ và để ý tin nhắn, cuộc gọi lạ trong thời gian tới."],
    ld_the_cao: ["Không mua thẻ cào rồi gửi mã cho người khác, kể cả tài khoản của bạn bè.",
      "“Nhờ mua thẻ hộ” là chiêu quen khi tài khoản bạn bè bị chiếm.",
      "Gọi điện hoặc gặp trực tiếp người đó để hỏi lại.",
      "Báo cho người bạn đó biết tài khoản có thể đã bị chiếm."],
    ld_khac: ["Không mở hay cho thuê tài khoản ngân hàng, thuê bao điện thoại đứng tên mình: đó là tiếp tay cho tội phạm và có thể bị xử lý.",
      "Không tải ứng dụng cá cược, “lấy lại tiền bị lừa”, “cho số”: đều là bẫy lấy tiền.",
      "Ai rủ bỏ học, đóng tiền cho “nhóm” lạ: kể ngay với cha mẹ, thầy cô.",
      "Lỡ làm theo: báo cha mẹ và trình báo công an nơi gần nhất."],
    link_nguy_hiem: ["Không bấm link; nếu đã bấm, không nhập gì và đóng trang.",
      "Lỡ đăng nhập ở trang đó: đổi mật khẩu ngay và đăng xuất mọi thiết bị.",
      "Báo cáo link với nền tảng và nhắc bạn bè trong nhóm đừng bấm."],
    bn_de_doa: ["Nếu bị doạ đánh, hẹn gặp: không đi một mình tới chỗ bị hẹn.",
      "Báo ngay giáo viên chủ nhiệm, giám thị hoặc cha mẹ, hôm nay.",
      "Chụp màn hình lưu bằng chứng, không xoá tin.",
      "Nguy hiểm tức thời: gọi 113. Cần người lắng nghe: gọi 111 (miễn phí, 24/7)."],
    bn_phat_tan: ["Không gửi thêm ảnh, không trả tiền hay làm theo yêu cầu, vì đòi hỏi thường tăng dần.",
      "Lưu bằng chứng (ảnh chụp màn hình, tên tài khoản), nhưng đừng tự chia sẻ ảnh đó cho ai.",
      "Kể ngay với cha mẹ hoặc thầy cô bạn tin. Bạn không có lỗi.",
      "Báo cáo với nền tảng để gỡ nội dung; gọi 111 để được hỗ trợ."],
    bn_tran_lot: ["Không đưa tiền hay đồ, vì đưa một lần thường bị đòi tiếp.",
      "Đi cùng bạn bè, tránh chỗ vắng ở nơi bị hẹn.",
      "Báo giám thị, giáo viên chủ nhiệm và cha mẹ; lưu lại tin nhắn.",
      "Cần giúp gấp: gọi 111 hoặc 113."],
    bn_lang_ma: ["Đừng đáp trả; lời lẽ đó không nói lên giá trị của bạn.",
      "Chặn hoặc hạn chế người gửi, tắt thông báo cuộc trò chuyện.",
      "Nếu lặp lại nhiều lần: chụp màn hình và báo thầy cô.",
      "Thấy buồn kéo dài: nói chuyện với người lớn bạn tin hoặc gọi 111."],
    bn_co_lap: ["Bị gạt ra khỏi nhóm không phải lỗi của bạn.",
      "Tìm một hai người bạn tin cậy để trò chuyện, đừng ở một mình với chuyện này.",
      "Kể với giáo viên chủ nhiệm hoặc phòng tư vấn để được giúp nhẹ nhàng.",
      "Ghi lại sự việc (ảnh chụp, ngày giờ) nếu tình trạng kéo dài."],
    bn_khac: ["Bạn không có lỗi khi bị nhiều người cùng tấn công trên mạng.",
      "Tạm khoá bình luận, để chế độ riêng tư, chặn tài khoản quấy rối.",
      "Chụp màn hình làm bằng chứng, báo cáo với nền tảng và nhờ thầy cô, cha mẹ can thiệp.",
      "Thấy quá sức chịu đựng: gọi 111 (miễn phí, 24/7)."],
    bn_tin_don: ["Không chia sẻ tiếp tin đồn, kể cả để thanh minh trong nhóm.",
      "Chụp màn hình bài đăng, tin nhắn làm bằng chứng.",
      "Báo cáo bài đăng với nền tảng và nhờ thầy cô can thiệp.",
      "Nếu tin đồn về chính bạn: tâm sự với người lớn bạn tin, đừng tự chịu một mình."],
  };
  const TODO_MEDIA = {
    lua_dao: ["Ảnh, video quảng cáo “trúng thưởng”, “việc nhẹ lương cao” thường là lừa đảo: đừng làm theo.",
      "Không quét mã QR hay bấm link xuất hiện trong ảnh, video lạ.",
      "Không liên hệ số điện thoại, tài khoản ghi trên ảnh."],
    bat_nat: ["Không chia sẻ tiếp ảnh, video đó, kể cả để phản đối.",
      "Chụp màn hình bài đăng làm bằng chứng rồi báo cáo với nền tảng.",
      "Nếu ảnh, video nói về bạn hoặc bạn bè: báo thầy cô, cha mẹ, hoặc gọi 111."],
  };
  const HELP_MSG = "Mình vừa nhận được một tin nhắn lạ làm mình lo. Bạn/thầy/cô xem giúp mình với được không?";

  // Phân loại nhóm chi tiết bằng mô hình đã học (chỉ chạy khi có cảnh báo)
  function fineCats(n, label, text) {
    const F = M.fine;
    const pre = label === "lua_dao" ? "ld_" : "bn_";
    const idx = F.classes.map((c, i) => (c.startsWith(pre) ? i : -1)).filter((i) => i >= 0);
    const z = F.intercept.slice();
    for (const f of feats(n, text)) { const w = F.weights[f]; if (w) for (let i = 0; i < z.length; i++) z[i] += w[i]; }
    const mx = Math.max(...idx.map((i) => z[i]));
    const e = idx.map((i) => Math.exp(z[i] - mx)); const sum = e.reduce((a, b) => a + b, 0);
    const ranked = idx.map((i, k) => [F.classes[i], e[k] / sum]).sort((a, b) => b[1] - a[1]);
    const out = ranked.filter(([, p], k) => k === 0 ? p >= 0.4 : p >= 0.3).slice(0, 2).map(([c]) => c);
    return out.length ? out : [label === "lua_dao" ? "ld_khac" : "bn_khac"];
  }

  function analyze(text, opt) {
    const { norm: n, probs } = predict(text);
    let ci = 0;
    for (let c = 1; c < probs.length; c++) if (probs[c] > probs[ci]) ci = c;
    let label = M.classes[ci];
    let p = probs[ci];
    let sev = 0;
    const reasons = [];
    const cats = new Set();
    // Luật an toàn v1.7: lời "cảnh báo" có kèm link lạ / số tài khoản / số điện thoại và dấu hiệu nguy cơ mạnh
    // thì không được coi là tuyên truyền (kẻ xấu hay giả dạng thông báo chính thức).
    let override = false;
    // chỉ xét phần KHÔNG nằm trong ngoặc kép (tin lừa được trích lại để cảnh báo thì không tính)
    const nq = label === "tuyen_truyen" && M.qspan ? norm(text.replace(new RegExp(M.qspan, "g"), " ")) : n;
    if (label === "tuyen_truyen" && M.direct && M.act && new RegExp(M.direct).test(nq) && new RegExp(M.act).test(nq)) {
      const neg = FRAME.find(([name]) => name === "__phu_dinh");
      if (!(neg && neg[1].test(nq))) {
        const hl = HARM.reduce((a, c) => (probs[M.classes.indexOf(c)] > probs[M.classes.indexOf(a)] ? c : a));
        label = hl; p = probs[M.classes.indexOf(hl)]; override = true;
      }
    }
    if (HARM.includes(label)) {
      sev = 1;
      for (const s of SIGNALS) {
        if (s.label === label && s.re.test(n)) { reasons.push(s.desc); sev = Math.max(sev, s.sev); if (s.cat) cats.add(s.cat); }
      }
    }
    // Nhóm chính: ưu tiên dấu hiệu rõ ràng, sau đó tới mô hình phân nhóm chi tiết
    const R = M.rule;
    const dl = SENS[(opt && opt.sens) || "can_bang"] || 0;
    const warn = HARM.includes(label) && (override || p >= R.p_warn + dl || (p >= R.p_warn_with_signal + dl && sev >= R.sev_signal));
    const level = !warn ? "an_toan" : sev >= 4 ? "khan_cap" : (p >= 0.85 || sev >= 3) ? "canh_bao" : "luu_y";
    const out = {
      label, label_vi: VI[label], p: Math.round(p * 1000) / 1000,
      probs: Object.fromEntries(M.classes.map((c, i) => [c, Math.round(probs[i] * 1000) / 1000])),
      sev, reasons: reasons.length ? reasons : (warn ? ["Giống các mẫu nguy cơ mô hình đã học"] : []),
      warn, level, advice: ADVICE[label] || "", friendly: FRIENDLY[label] || "",
      // v1.7: nội dung đang TUYÊN TRUYỀN / cảnh báo / kể lại (nhắc tới nguy cơ nhưng không nhắm vào bạn)
      frame: label === "tuyen_truyen" ? "tuyen_truyen" : "",
      main: reasons.length ? reasons[0] : (warn ? "Giống các mẫu nguy cơ mô hình đã học" : ""),
      // Loại nguy cơ dùng cho thống kê ẩn danh (chỉ là mã loại, không chứa nội dung)
      cats: [],
    };
    if (warn) {
      const fine = fineCats(n, label, text);
      const main = [...cats][0] || fine[0];
      out.cat = main;
      out.cat_vi = CAT_VI[main] || VI[label];
      out.todo = TODO_CAT[main] || TODO[label] || [];
      out.cats = [label === "lua_dao" ? "lua_dao_bat_ky" : "bat_nat_bat_ky", ...new Set([main, ...fine])];
      const s = " " + n + " ";
      const pre = label === "lua_dao" ? /^(ld_|link)/ : /^bn_/;
      const hit = (M.phrases || []).filter(([k, , c]) => pre.test(c) && s.includes(" " + k + " "));
      // bỏ cụm nằm gọn trong cụm dài hơn đã khớp (vd "OTP" trong "mã OTP")
      const keep = hit.filter(([k]) => !hit.some(([k2]) => k2 !== k && (" " + k2 + " ").includes(" " + k + " ")));
      out.phrases = [...new Set(keep.map(([, show]) => show))].slice(0, 4);
    } else { out.todo = []; out.phrases = []; }
    return out;
  }

  // Che thông tin cá nhân TRƯỚC KHI bất cứ thứ gì rời trang (chỉ khi học sinh bấm "Phân tích sâu" hoặc "Báo cáo")
  function domainOf(u) {
    return u.toLowerCase().replace(/^https?:\/\//, "").replace(/^www\./, "").split(/[/?#]/)[0].replace(/[.,;:!)]+$/, "");
  }
  function mask(text) {
    const domains = new Set();
    let m = text.replace(/\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b/g, "<EMAIL>");
    m = m.replace(new RegExp(M.regex.url, "gi"), (x) => { domains.add(domainOf(x)); return "<LINK>"; });
    m = m.replace(RX_PHONE, "<SĐT>").replace(RX_NUM, "<SỐ>").replace(/@[\w.]+/g, "<NGƯỜI>");
    return { masked: m, domains: [...domains] };
  }

  // ---------- v1.9: TIN MÌNH SẮP GỬI và NỘI DUNG BẠO LỰC ----------
  // Nhắc học sinh dừng lại, đọc lại trước khi gửi (không chặn, không báo ai); làm mờ ảnh/video có chữ đi kèm mô tả bạo lực.
  const RX_VIOLENT = /\b(danh hoi dong|danh nhau|bi danh(?! la\b| cua\b)|danh ban(?! phim)|danh dap|danh dan man|hanh hung|bao luc hoc duong|tat lien tuc|tat toi tap|dam da|giam dap|dap vao (?:dau|mat|bung)|lot do|dam chem|chem nhau|vung dao|be hoi dong|danh ghen|clip danh)\b/;
  function violentMedia(text) {
    const m = norm(text || "").match(RX_VIOLENT);
    if (!m) return { hit: false };
    // tìm lại cụm từ có dấu trong chữ gốc để hiện cho học sinh (tránh "bi danh" bị đọc nhầm thành "bí danh")
    const n = m[0].split(" ").length, w = String(text).split(/\s+/);
    let word = m[0];
    for (let i = 0; i + n <= w.length; i++) { const c = w.slice(i, i + n).join(" "); if (norm(c) === m[0]) { word = c.replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, ""); break; } }
    return { hit: true, word };
  }
  const OUT_TIPS = {
    bat_nat: {
      title: "Khoan đã, tin này có thể làm bạn kia tổn thương",
      body: "Một câu nói lúc nóng giận có thể làm người nhận buồn rất lâu, và tin đã gửi thì không rút lại được.",
      rewrite: ["Mình không đồng ý với bạn, mình muốn nói chuyện riêng với bạn nhé.", "Mình đang bực, để mình bình tĩnh rồi nói sau.", "Mình xin lỗi nếu lúc nãy làm bạn buồn."],
    },
    lua_dao: {
      title: "Tin bạn sắp gửi giống tin lừa đảo",
      body: "Nếu bạn đang làm theo yêu cầu của người khác (chuyển tiền, gửi mã, gửi thông tin), hãy dừng lại và hỏi người lớn. Nếu bạn chuyển tiếp để cảnh báo mọi người, hãy ghi rõ là cảnh báo.",
      rewrite: [],
    },
    otp: {
      title: "Bạn sắp gửi một dãy số giống mã OTP",
      body: "Không ai cần mã OTP của bạn, kể cả ngân hàng, thầy cô hay bạn thân. Ai xin mã là dấu hiệu lừa đảo.",
      rewrite: [],
    },
  };
  function outgoing(text, opt) {
    const t = String(text || "").trim();
    if (t.length < 3) return { nudge: false };
    const nt = norm(t);
    const code = /(^|\D)\d{4,8}(\D|$)/.test(t) && !/\d{9,}/.test(t) && t.length <= 60 && (/\b(ma|otp|code|xac nhan|xac minh)\b/.test(nt) || t.replace(/[\d\s.,:-]/g, "").length <= 3);
    if (code) return Object.assign({ nudge: true, kind: "otp" }, OUT_TIPS.otp);
    const r = analyze(t, opt);
    if (r.warn && HARM.includes(r.label)) {
      const tip = OUT_TIPS[r.label];
      const rewrite = r.label === "lua_dao" ? ["Cảnh báo, đừng làm theo tin này: “" + t.slice(0, 200) + "”"] : tip.rewrite;
      return { nudge: true, kind: r.label, r, title: tip.title, body: tip.body, rewrite, why: r.cat_vi || r.label_vi };
    }
    return { nudge: false, r };
  }

  g.EduShieldDetector = { analyze, norm, mask, domainOf, VI, HELP_MSG, TODO, TODO_CAT, TODO_MEDIA, CAT_VI, outgoing, violentMedia };
})(globalThis);

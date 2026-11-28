// EduShield - CHẾ ĐỘ "THỰC CHIẾN GIẢ LẬP" (diễn tập như diễn tập phòng cháy) và CHỈ SỐ MIỄN DỊCH SỐ.
// Dùng chung cho tiện ích trình duyệt, app web, Android (WebView) và iOS (WKWebView).
// Nguyên tắc: học sinh TỰ BẬT; tin diễn tập luôn đến từ EduShield (không giả làm Zalo, Messenger hay số điện thoại thật);
// mọi tên, số, link đều giả; sau mỗi lần trả lời luôn nói rõ "đây là bài diễn tập"; điểm chỉ lưu trên máy học sinh.
(function (g) {
  "use strict";
  // Nhóm kỹ năng dùng để tính Chỉ số miễn dịch số
  const GROUPS = {
    otp: "Giữ kín mã OTP, mật khẩu",
    tien: "Không chuyển tiền khi chưa xác minh",
    gia_danh: "Nhận ra giả danh công an, \"bắt cóc online\"",
    viec_lam: "Cảnh giác việc nhẹ lương cao, đầu tư",
    qua: "Cảnh giác quà tặng, học bổng giả",
    thong_tin: "Bảo vệ giấy tờ, tài khoản ngân hàng",
    bat_nat: "Ứng phó khi bị bắt nạt",
    chung_kien: "Giúp bạn khi thấy bắt nạt",
    tin_that: "Không hoảng với tin thật",
  };
  // Mỗi tình huống: hành động [chữ, điểm 0-100, giải thích]; dấu hiệu [chữ, đúng(1)/không(0)]
  const S = [
    { id: "otp1", g: "otp", lv: 1, from: "Linh (bạn cùng lớp)", msgs: ["Ơi mình đổi điện thoại nên không đăng nhập được Facebook 😭", "Có mã 6 số vừa gửi vào máy cậu đó, đọc giúp mình với, gấp lắm!"],
      act: [["Đọc mã cho bạn vì là bạn thân", 0, "Mã gửi vào máy bạn là chìa khoá tài khoản CỦA BẠN. Kẻ chiếm tài khoản của Linh đang muốn chiếm tiếp tài khoản của bạn."],
        ["Gọi điện thẳng cho Linh để hỏi", 100, "Đúng! Gọi điện hoặc gặp trực tiếp là cách chắc chắn nhất để biết có phải Linh thật không."],
        ["Nhắn lại hỏi \"có đúng là cậu không?\"", 40, "Kẻ đang dùng tài khoản của Linh sẽ trả lời \"đúng rồi\". Hỏi lại qua chính tài khoản đó không xác minh được gì."],
        ["Không trả lời", 60, "An toàn, nhưng nên báo cho Linh qua kênh khác rằng tài khoản có thể đã bị chiếm."]],
      sig: [["Xin mã gửi vào máy mình", 1], ["Giục \"gấp lắm\"", 1], ["Lý do \"đổi điện thoại\"", 1], ["Có biểu tượng cảm xúc", 0], ["Nhắn lúc tối", 0]],
      lesson: "Không ai cần mã OTP của bạn, kể cả bạn thân, ngân hàng hay nhà mạng." },
    { id: "otp2", g: "otp", lv: 2, from: "Tổng đài hỗ trợ (số lạ)", msgs: ["Tài khoản ngân hàng của bạn đang có giao dịch 4.900.000đ chờ xử lý.", "Để huỷ giao dịch, vui lòng đọc mã xác thực vừa gửi cho nhân viên hỗ trợ trong 5 phút."],
      act: [["Đọc mã để huỷ giao dịch cho nhanh", 0, "Mã đó chính là mã để kẻ gian XÁC NHẬN chuyển tiền đi. Ngân hàng không bao giờ xin mã OTP."],
        ["Tự gọi số tổng đài in trên thẻ hoặc mở app ngân hàng chính thức", 100, "Đúng! Tự liên hệ kênh chính thức, không dùng số hay link trong tin nhắn."],
        ["Gọi lại vào số vừa nhắn", 30, "Số đó do kẻ gian giữ, họ sẽ tiếp tục thuyết phục bạn."],
        ["Kể với bố mẹ rồi cùng kiểm tra", 90, "Rất tốt. Người lớn sẽ giúp bạn bình tĩnh và gọi đúng tổng đài."]],
      sig: [["Xin mã xác thực", 1], ["Tạo áp lực \"trong 5 phút\"", 1], ["Số tiền lớn gây hoảng sợ", 1], ["Có dấu chấm cuối câu", 0], ["Gọi mình là \"bạn\"", 0]],
      lesson: "Giao dịch lạ: tự mở app ngân hàng hoặc gọi số in trên thẻ, đừng làm theo tin nhắn." },
    { id: "otp3", g: "otp", lv: 3, from: "Ban quản trị nhóm học tập", msgs: ["Nhóm đang lọc tài khoản ảo trước kỳ thi.", "Bạn nào chưa xác minh thì gửi mã 6 số Zalo vừa gửi cho admin trước 21h, quá giờ sẽ bị mời ra khỏi nhóm nhé."],
      act: [["Gửi mã vì sợ bị mời ra khỏi nhóm", 0, "\"Xác minh thành viên bằng mã\" là chiêu chiếm tài khoản. Không nhóm nào cần mã đăng nhập của bạn."],
        ["Không gửi, báo cho thầy cô hoặc lớp trưởng biết", 100, "Đúng! Bạn vừa bảo vệ mình và cả nhóm."],
        ["Hỏi bạn khác đã gửi chưa rồi làm theo", 30, "Nhiều người làm theo không có nghĩa là an toàn."],
        ["Rời nhóm luôn", 60, "An toàn cho bạn, nhưng nên cảnh báo các bạn khác."]],
      sig: [["Xin mã đăng nhập", 1], ["Doạ mời ra khỏi nhóm", 1], ["Hạn giờ \"trước 21h\"", 1], ["Nói về kỳ thi", 0], ["Có chữ \"admin\"", 0]],
      lesson: "Đe doạ kiểu \"không làm thì bị loại\" là để bạn hoảng mà làm theo." },
    { id: "tien1", g: "tien", lv: 1, from: "Cô Hằng (tài khoản mới)", msgs: ["Cô chủ nhiệm đây, cô đổi tài khoản Zalo.", "Em chuyển giúp cô 300k tiền quỹ lớp vào số 9999 1234 5678 trong sáng nay nhé, cô đang họp."],
      act: [["Chuyển ngay vì là cô giáo", 0, "Tài khoản \"mới\" xưng thầy cô xin tiền là chiêu rất phổ biến đầu năm học."],
        ["Hỏi lại cô trực tiếp ở lớp hoặc gọi số quen của cô", 100, "Đúng! Xác minh bằng kênh bạn đã biết từ trước."],
        ["Chuyển một nửa trước cho chắc", 0, "Chuyển bao nhiêu cũng là mất."],
        ["Báo lớp trưởng và cả lớp cẩn thận", 90, "Rất tốt, bạn còn giúp cả lớp không bị lừa."]],
      sig: [["Tài khoản mới, đổi tài khoản", 1], ["Xin chuyển tiền vào tài khoản lạ", 1], ["Lý do bận \"đang họp\"", 1], ["Gọi mình là \"em\"", 0], ["Nhắc tới quỹ lớp", 0]],
      lesson: "Tiền của trường, của lớp chỉ nộp theo thông báo chính thức, không qua tài khoản cá nhân lạ." },
    { id: "tien2", g: "tien", lv: 2, from: "Số lạ", msgs: ["Chị lỡ chuyển nhầm 2.000.000đ vào tài khoản em, em kiểm tra giúp chị.", "Em chuyển lại vào số này giúp chị nha, chị cảm ơn nhiều 🙏"],
      act: [["Chuyển lại ngay cho người ta", 10, "Tiền \"chuyển nhầm\" có thể là tiền bẩn hoặc khoản vay đứng tên bạn. Chuyển lại theo tin nhắn là mắc bẫy."],
        ["Báo bố mẹ, liên hệ ngân hàng để ngân hàng xử lý", 100, "Đúng! Chỉ trả lại tiền qua ngân hàng hoặc cơ quan chức năng."],
        ["Tiêu luôn số tiền đó", 0, "Tiêu tiền không phải của mình có thể vi phạm pháp luật."],
        ["Không trả lời", 50, "Chưa đủ: hãy báo bố mẹ và ngân hàng."]],
      sig: [["\"Chuyển nhầm\" rồi đòi chuyển lại", 1], ["Đưa số tài khoản khác", 1], ["Lời lẽ lịch sự, tha thiết", 1], ["Số tiền tròn", 0], ["Gọi mình là \"em\"", 0]],
      lesson: "Tiền lạ vào tài khoản: báo ngân hàng, không tự chuyển trả theo lời người lạ." },
    { id: "tien3", g: "tien", lv: 3, from: "Mẹ (số mới)", msgs: ["Mẹ đây, điện thoại mẹ rơi vỡ nên mượn máy cô bán hàng.", "Con chuyển 1 triệu cho cô ấy theo số tài khoản này giúp mẹ, tối mẹ đưa lại con."],
      act: [["Chuyển ngay vì mẹ cần", 0, "Kẻ gian thường giả làm người thân \"đổi số\" để xin tiền gấp."],
        ["Gọi vào số cũ của mẹ hoặc hỏi bố, người thân", 100, "Đúng! Luôn gọi lại số quen trước khi chuyển tiền."],
        ["Hỏi một câu chỉ mẹ mới biết", 70, "Tốt, nhưng gọi điện trực tiếp vẫn chắc chắn hơn."],
        ["Chuyển một ít trước", 0, "Chuyển ít hay nhiều đều có thể mất."]],
      sig: [["Người thân dùng số mới", 1], ["Nhờ chuyển cho người lạ", 1], ["Hứa trả lại sau", 1], ["Gọi mình là \"con\"", 0], ["Có chữ \"tối\"", 0]],
      lesson: "Người thân xin tiền qua số lạ: gọi lại số cũ trước khi làm gì." },
    { id: "gd1", g: "gia_danh", lv: 1, from: "Cán bộ điều tra (số lạ)", msgs: ["Đây là cơ quan công an. Em có liên quan đến một vụ án rửa tiền.", "Tuyệt đối không được nói với bố mẹ, nếu không em sẽ bị bắt tạm giam."],
      act: [["Làm theo vì sợ bị bắt", 0, "Công an không làm việc qua tin nhắn, không bắt giữ bí mật với gia đình."],
        ["Dừng trả lời và kể ngay với bố mẹ", 100, "Đúng! Ai bắt bạn giữ bí mật với bố mẹ là dấu hiệu nguy hiểm nhất."],
        ["Hỏi lại họ tên, cấp bậc của cán bộ", 30, "Kẻ gian có sẵn tên, cấp bậc, cả \"giấy tờ\" giả."],
        ["Gọi 113 hoặc tới công an gần nhất để hỏi", 90, "Rất tốt, nhưng nên báo bố mẹ cùng lúc."]],
      sig: [["Bắt giữ bí mật với bố mẹ", 1], ["Đe doạ bắt giam", 1], ["Công an làm việc qua tin nhắn", 1], ["Gọi mình là \"em\"", 0], ["Câu viết đúng chính tả", 0]],
      lesson: "Không ai có quyền bắt bạn giữ bí mật với bố mẹ." },
    { id: "gd2", g: "gia_danh", lv: 2, from: "Viện kiểm sát (gọi video)", msgs: ["Hồ sơ của em đang chuyển sang toà án.", "Để chứng minh trong sạch, em ra một khách sạn gần nhà, ở một mình, bật camera liên tục để cán bộ theo dõi."],
      act: [["Đi ngay để chứng minh mình trong sạch", 0, "Đây là kịch bản \"bắt cóc online\": cô lập bạn rồi đòi gia đình chuyển tiền chuộc."],
        ["Tắt máy, gọi bố mẹ hoặc 113 ngay", 100, "Đúng! Cơ quan chức năng không bao giờ yêu cầu như vậy."],
        ["Hỏi xem có được đi cùng bạn không", 10, "Không nên tiếp tục nói chuyện với kẻ gian."],
        ["Xin thêm thời gian suy nghĩ", 30, "Đừng chờ, hãy kể với người lớn ngay."]],
      sig: [["Yêu cầu ở một mình trong khách sạn", 1], ["Bật camera liên tục", 1], ["Xưng viện kiểm sát, toà án", 1], ["Nhắc tới hồ sơ", 0], ["Gọi video", 0]],
      lesson: "Bị yêu cầu ở một mình, tắt liên lạc với gia đình: đó là \"bắt cóc online\"." },
    { id: "gd3", g: "gia_danh", lv: 3, from: "Phòng an ninh mạng (email)", msgs: ["Bạn đăng bài vi phạm luật an ninh mạng.", "Nộp phạt 1.500.000đ vào tài khoản tạm giữ trong 24 giờ để huỷ hồ sơ, quá hạn sẽ chuyển công an địa phương."],
      act: [["Nộp phạt cho xong", 0, "Không có \"tài khoản tạm giữ\" nào thu phạt qua email."],
        ["Kể với bố mẹ, thầy cô và kiểm tra ở cơ quan chức năng", 100, "Đúng!"],
        ["Xoá hết bài đăng rồi nộp phạt", 0, "Sợ hãi là thứ kẻ gian muốn."],
        ["Trả lời email để giải thích", 20, "Trả lời giúp kẻ gian biết bạn đang lo lắng."]],
      sig: [["Nộp phạt vào tài khoản cá nhân", 1], ["Hạn 24 giờ", 1], ["Doạ chuyển công an", 1], ["Gửi qua email", 0], ["Có số tiền cụ thể", 0]],
      lesson: "Phạt thật có quyết định giấy và nộp ở kênh nhà nước, không qua tin nhắn, email." },
    { id: "vl1", g: "viec_lam", lv: 1, from: "Tuyển CTV online", msgs: ["Việc nhẹ lương cao cho học sinh: like, chia sẻ bài, 300-500k/ngày.", "Chỉ cần nạp 100k kích hoạt tài khoản nhiệm vụ là bắt đầu được nhé!"],
      act: [["Nạp 100k vì rẻ", 0, "Lần đầu có thể được trả, rồi bị yêu cầu nạp nhiều hơn và mất trắng."],
        ["Bỏ qua và chặn", 90, "An toàn."],
        ["Hỏi bố mẹ, thầy cô trước khi nhận việc online", 100, "Đúng! Việc thật không bắt nạp tiền."],
        ["Rủ bạn cùng làm cho vui", 0, "Bạn có thể kéo cả bạn mình vào bẫy."]],
      sig: [["Phải nạp tiền mới được làm", 1], ["Lương cao, việc dễ", 1], ["Nhắm vào học sinh", 1], ["Có biểu tượng cảm xúc", 0], ["Nhắc tới mạng xã hội", 0]],
      lesson: "Việc thật trả tiền cho bạn, không bắt bạn trả tiền." },
    { id: "vl2", g: "viec_lam", lv: 2, from: "Anh Tuấn (nhóm đầu tư)", msgs: ["Hôm qua em gái anh nạp 500k, sáng nay rút về 1 triệu, có ảnh chụp đây.", "Em vào nhóm VIP đi, anh hướng dẫn, chắc thắng 100%."],
      act: [["Nạp thử ít tiền", 0, "\"Chắc thắng\" là không có thật; ảnh lợi nhuận có thể làm giả."],
        ["Từ chối, rời nhóm", 90, "Tốt."],
        ["Kể với người lớn và báo cáo nhóm", 100, "Đúng! Bạn giúp người khác không bị lừa."],
        ["Xin anh ấy cho rút thử trước", 20, "Rút được lần đầu là mồi để bạn nạp nhiều hơn."]],
      sig: [["Hứa \"chắc thắng\", lãi gấp đôi", 1], ["Ảnh chụp lợi nhuận", 1], ["Nhóm \"VIP\" kín", 1], ["Gọi mình là \"em\"", 0], ["Nhắc tới em gái", 0]],
      lesson: "Lợi nhuận gấp đôi trong một đêm là dấu hiệu lừa đảo kinh điển." },
    { id: "qua1", g: "qua", lv: 1, from: "Chương trình tri ân", msgs: ["Chúc mừng bạn trúng iPhone trong chương trình tri ân khách hàng!", "Nhập tài khoản và mật khẩu Facebook tại qua-tang-tri-an.xyz để nhận quà."],
      act: [["Nhập để nhận quà", 0, "Trang giả sẽ lấy mật khẩu của bạn."],
        ["Không bấm, xoá tin", 90, "An toàn."],
        ["Chụp màn hình báo cáo, nhắc bạn bè", 100, "Đúng!"],
        ["Bấm xem thử nhưng không nhập", 40, "Bấm link lạ vẫn có thể gặp mã độc."]],
      sig: [["Trúng thưởng dù không tham gia", 1], ["Đòi mật khẩu", 1], ["Link lạ", 1], ["Quà là điện thoại", 0], ["Có chữ \"chúc mừng\"", 0]],
      lesson: "Không tham gia thì không thể trúng thưởng." },
    { id: "qua2", g: "qua", lv: 2, from: "Quỹ học bổng quốc tế", msgs: ["Em được xét học bổng du học 100%.", "Đóng 2.000.000đ phí hồ sơ trong tuần này để giữ suất, chuyển khoản cho cán bộ phụ trách."],
      act: [["Đóng phí vì học bổng rất giá trị", 0, "Học bổng thật không thu phí giữ suất qua tài khoản cá nhân."],
        ["Kiểm tra trên trang chính thức và hỏi thầy cô", 100, "Đúng!"],
        ["Gửi bảng điểm, căn cước để họ xét trước", 10, "Gửi giấy tờ cho người lạ có thể bị lợi dụng."],
        ["Bỏ qua", 70, "An toàn, nên báo thầy cô để các bạn khác cảnh giác."]],
      sig: [["Đóng phí để giữ suất", 1], ["Chuyển khoản cá nhân", 1], ["Hạn \"trong tuần này\"", 1], ["Học bổng 100%", 1], ["Gọi mình là \"em\"", 0]],
      lesson: "Học bổng, cuộc thi thật được công bố trên trang chính thức của trường, của Bộ." },
    { id: "tt1", g: "thong_tin", lv: 2, from: "Anh Khoa (bạn của anh họ)", msgs: ["Em có tài khoản ngân hàng không? Cho anh thuê vài tuần để nhận tiền hàng.", "Mỗi tuần anh gửi em 500k, em không phải làm gì cả."],
      act: [["Đồng ý vì có tiền tiêu vặt", 0, "Tài khoản đứng tên bạn có thể bị dùng để rửa tiền; bạn có thể bị xử lý theo pháp luật."],
        ["Từ chối và kể với bố mẹ", 100, "Đúng!"],
        ["Cho mượn một tuần thử", 0, "Một ngày cũng đủ để tài khoản bị dùng cho việc phạm pháp."],
        ["Hỏi anh ấy nhận tiền hàng gì", 20, "Không cần tìm hiểu, câu trả lời luôn là không."]],
      sig: [["Thuê tài khoản ngân hàng", 1], ["Trả tiền mà không làm gì", 1], ["Người quen gián tiếp", 1], ["Số tiền 500k", 0], ["Gọi mình là \"em\"", 0]],
      lesson: "Không mở, không cho mượn, không cho thuê tài khoản, sim đứng tên mình." },
    { id: "tt2", g: "thong_tin", lv: 1, from: "Khảo sát học sinh", msgs: ["Khảo sát nhận quà 50k cho học sinh THPT!", "Điền họ tên, ngày sinh, số căn cước và ảnh hai mặt căn cước vào form nhé."],
      act: [["Điền đầy đủ để nhận quà", 0, "Ảnh căn cước có thể bị dùng mở tài khoản, vay tiền mang tên bạn."],
        ["Không điền, hỏi thầy cô khảo sát có thật không", 100, "Đúng!"],
        ["Điền tên thật nhưng bỏ ảnh căn cước", 30, "Vẫn lộ thông tin cá nhân."],
        ["Bỏ qua", 80, "An toàn."]],
      sig: [["Đòi ảnh căn cước", 1], ["Quà nhỏ để dụ", 1], ["Form không rõ đơn vị", 1], ["Dành cho học sinh THPT", 0], ["Có dấu chấm than", 0]],
      lesson: "Giấy tờ tuỳ thân chỉ đưa cho cơ quan, trường học qua kênh chính thức." },
    { id: "bn1", g: "bat_nat", lv: 1, from: "Nhóm chat lớp", msgs: ["[Một bạn trong nhóm] Nhìn ảnh nó kìa, béo như con heo 🐷 haha", "[Bạn khác] Đúng rồi, từ mai đừng ai ngồi cạnh nó"],
      act: [["Chửi lại thật nặng", 10, "Đáp trả lúc tức giận thường làm mọi chuyện tệ hơn và có thể khiến bạn bị phạt."],
        ["Chụp màn hình, rời nhóm và kể với thầy cô hoặc bố mẹ", 100, "Đúng! Bạn không có lỗi và không phải chịu một mình."],
        ["Im lặng chịu đựng", 30, "Bạn xứng đáng được giúp đỡ. Hãy kể với người bạn tin."],
        ["Xoá tài khoản luôn", 40, "Có thể tạm nghỉ, nhưng hãy lưu bằng chứng và tìm người giúp."]],
      sig: [["Chê ngoại hình", 1], ["Rủ cả nhóm cô lập", 1], ["Nói trong nhóm đông người", 1], ["Có chữ \"haha\"", 0], ["Gửi buổi tối", 0]],
      lesson: "Chụp màn hình, không đáp trả, kể với người lớn. Gọi 111 nếu cần người lắng nghe." },
    { id: "bn2", g: "bat_nat", lv: 2, from: "Tài khoản ẩn danh", msgs: ["Tao có ảnh của mày lúc thay đồ ở phòng thể chất.", "Chuyển 500k không thì tối nay ảnh lên confession."],
      act: [["Chuyển tiền để được yên", 0, "Đưa tiền một lần sẽ bị đòi tiếp, ảnh cũng không chắc bị xoá."],
        ["Không trả lời, lưu bằng chứng, kể ngay với bố mẹ hoặc thầy cô", 100, "Đúng! Đây là hành vi phạm pháp, người lớn và công an có thể can thiệp."],
        ["Năn nỉ họ xoá ảnh", 20, "Năn nỉ cho họ biết bạn sợ."],
        ["Tự tìm xem là ai để đánh", 0, "Nguy hiểm cho bạn."]],
      sig: [["Đe doạ tung ảnh riêng tư", 1], ["Đòi tiền", 1], ["Tài khoản ẩn danh", 1], ["Nhắc tới confession", 1], ["Viết tắt", 0]],
      lesson: "Bị doạ tung ảnh: không trả tiền, lưu bằng chứng, báo người lớn, gọi 111." },
    { id: "bn3", g: "bat_nat", lv: 3, from: "Bạn cùng lớp", msgs: ["Mày mà kể với cô vụ hôm qua thì tan học đợi đấy.", "Liệu hồn."],
      act: [["Giữ im lặng vì sợ", 20, "Lời đe doạ cần được người lớn biết."],
        ["Báo giám thị hoặc thầy cô ngay trong ngày, đi về cùng bạn bè", 100, "Đúng!"],
        ["Mang theo đồ để tự vệ", 0, "Nguy hiểm và có thể vi phạm nội quy, pháp luật."],
        ["Nhắn lại xin lỗi cho xong", 30, "Bạn không có lỗi khi kể chuyện bị bắt nạt."]],
      sig: [["Đe doạ hẹn gặp", 1], ["Cấm kể với thầy cô", 1], ["\"Liệu hồn\"", 1], ["Nhắc chuyện hôm qua", 0], ["Tin nhắn ngắn", 0]],
      lesson: "Bị doạ đánh: báo ngay giám thị, thầy cô; đừng đi một mình." },
    { id: "ck1", g: "chung_kien", lv: 1, from: "Nhóm chat lớp", msgs: ["[Nam] Mọi người vào bình luận chửi con bé lớp bên cho nó bỏ mạng xã hội đi", "[Nam] Ai không chửi là về phe nó"],
      act: [["Vào bình luận cho cùng phe", 0, "Hùa theo là tham gia bắt nạt."],
        ["Không tham gia, nhắn hỏi thăm bạn bị nhắm tới, báo thầy cô", 100, "Đúng! Người chứng kiến lên tiếng có thể chặn đứng bắt nạt."],
        ["Im lặng, không làm gì", 40, "Không tham gia là tốt, nhưng bạn có thể giúp nhiều hơn."],
        ["Chia sẻ tin nhắn này sang nhóm khác cho mọi người biết", 20, "Lan truyền thêm có thể làm bạn kia tổn thương hơn. Hãy báo người lớn."]],
      sig: [["Kêu gọi tấn công tập thể", 1], ["Ép mọi người chọn phe", 1], ["Nhắm vào một người", 1], ["Gửi trong nhóm lớp", 0], ["Viết hoa đầu câu", 0]],
      lesson: "Không hùa theo, hỏi thăm bạn bị nhắm tới, báo người lớn." },
    { id: "ck2", g: "chung_kien", lv: 2, from: "Bạn thân", msgs: ["Ê xem clip con Thảo bị đánh ở cổng trường chưa, hài vãi", "Share đi cho cả trường xem"],
      act: [["Share cho vui", 0, "Chia sẻ clip bạo lực là tiếp tay cho bạo lực."],
        ["Không xem tiếp, không share, báo thầy cô và báo cáo clip", 100, "Đúng!"],
        ["Xem nhưng không share", 40, "Tốt hơn share, nhưng nên báo người lớn để giúp bạn Thảo."],
        ["Nhắn bạn thân đừng share nữa", 70, "Tốt! Thêm việc báo thầy cô thì càng tốt."]],
      sig: [["Clip bạo lực", 1], ["Rủ lan truyền", 1], ["Coi chuyện bị đánh là \"hài\"", 1], ["Gửi từ bạn thân", 0], ["Có chữ \"vãi\"", 0]],
      lesson: "Không chia sẻ clip bạo lực; báo người lớn và báo cáo với nền tảng." },
    { id: "th1", g: "tin_that", lv: 1, from: "Sổ liên lạc điện tử của trường", msgs: ["Nhà trường thông báo: thứ bảy tuần này họp phụ huynh lúc 8h tại phòng học.", "Mọi khoản thu sẽ có thông báo bằng văn bản."],
      act: [["Báo bố mẹ lịch họp", 100, "Đúng! Đây là thông báo bình thường từ kênh chính thức, không đòi tiền, không đòi mã."],
        ["Chặn và báo cáo lừa đảo", 20, "Không có dấu hiệu lừa đảo. Cẩn thận là tốt, nhưng đừng nghi ngờ mọi thông báo thật."],
        ["Gọi hỏi cô cho chắc", 70, "Không sai, nhưng tin này không có yêu cầu gì rủi ro."],
        ["Bỏ qua", 40, "Bố mẹ có thể lỡ buổi họp."]],
      sig: [["Đến từ kênh chính thức của trường", 0], ["Không đòi tiền, mã hay thông tin", 0], ["Có ngày giờ cụ thể", 0], ["Đòi chuyển tiền, đòi mã", 0]],
      safe: true, lesson: "Không phải tin nào cũng là lừa đảo: hãy nhìn yêu cầu trong tin (tiền, mã, bí mật) và kênh gửi." },
    { id: "th2", g: "tin_that", lv: 2, from: "Bài đăng của Đoàn trường", msgs: ["Cảnh báo: kẻ gian giả danh công an gọi điện doạ học sinh dính vụ án.", "Tuyệt đối không làm theo, hãy báo bố mẹ hoặc gọi 113."],
      act: [["Chia sẻ cho bạn bè cùng biết", 100, "Đúng! Đây là tin tuyên truyền, nhắc tới thủ đoạn để mọi người cảnh giác."],
        ["Báo cáo bài đăng là lừa đảo", 10, "Bài không đòi bạn làm gì nguy hiểm; nó đang giúp bạn phòng tránh."],
        ["Gọi ngay 113 vì sợ", 30, "Chỉ cần gọi khi chính bạn bị đe doạ."],
        ["Đọc và ghi nhớ", 80, "Tốt."]],
      sig: [["Nhắc tới thủ đoạn ở ngôi thứ ba", 0], ["Lời khuyên \"tuyệt đối không làm theo\"", 0], ["Đến từ Đoàn trường", 0], ["Có chữ \"công an\", \"vụ án\"", 0]],
      safe: true, lesson: "Tin tuyên truyền dùng từ giống kẻ xấu nhưng không đòi bạn làm gì: đó là lời nhắc, không phải nguy cơ." },
    { id: "th3", g: "tin_that", lv: 3, from: "Bạn Minh (gặp ở lớp)", msgs: ["Mai mình chuyển khoản trả cậu 30k tiền trà sữa hôm trước nhé, số tài khoản cậu vẫn như cũ đúng không?"],
      act: [["Trả lời đúng rồi, cảm ơn", 100, "Đúng! Bạn quen, đang TRẢ tiền cho bạn, không đòi gì của bạn."],
        ["Chặn Minh vì nhắc tới chuyển khoản", 10, "Chuyển khoản không phải lúc nào cũng là lừa đảo. Hãy xem ai đang đòi ai làm gì."],
        ["Hỏi lại khi gặp ở lớp", 70, "Không sai, nhưng không cần thiết."],
        ["Gửi luôn mã OTP để Minh chuyển cho nhanh", 0, "Nhận tiền không bao giờ cần mã OTP!"]],
      sig: [["Bạn quen, chuyện có thật", 0], ["Người kia trả tiền cho mình", 0], ["Không đòi mã hay tiền", 0], ["Có chữ \"chuyển khoản\"", 0]],
      safe: true, lesson: "Nhận tiền không cần mã OTP; chỉ cảnh giác khi bị đòi tiền, mã, bí mật." },
    { id: "gd4", g: "gia_danh", lv: 3, from: "Thầy Long (phòng đào tạo)", msgs: ["Em có tên trong danh sách thiếu học phí, nếu không đóng hôm nay sẽ bị gạch tên khỏi kỳ thi.", "Em chuyển 1.200.000đ vào tài khoản cá nhân của thầy, đừng làm phiền phụ huynh."],
      act: [["Chuyển ngay để không bị gạch tên", 0, "Trường không thu học phí qua tài khoản cá nhân và không bảo bạn giấu phụ huynh."],
        ["Hỏi giáo viên chủ nhiệm và bố mẹ", 100, "Đúng!"],
        ["Hỏi thầy số tài khoản trường", 30, "Kẻ gian sẽ đưa tiếp một số tài khoản giả."],
        ["Mượn tiền bạn để chuyển", 0, "Bạn sẽ mất cả tiền của bạn mình."]],
      sig: [["Tài khoản cá nhân", 1], ["Giấu phụ huynh", 1], ["Hạn ngay hôm nay", 1], ["Nhắc kỳ thi", 0], ["Xưng thầy", 0]],
      lesson: "Học phí chỉ nộp theo giấy báo chính thức; ai bảo giấu bố mẹ là đáng ngờ." },
    { id: "otp4", g: "otp", lv: 2, from: "Người bán đồ cũ", msgs: ["Mình chuyển tiền mua máy cho bạn qua ví nhé.", "Bạn bấm link này, đăng nhập ngân hàng để \"nhận tiền\" rồi đọc mã cho mình xác nhận."],
      act: [["Làm theo để nhận tiền", 0, "Nhận tiền không bao giờ cần đăng nhập qua link hay đọc mã."],
        ["Từ chối, chỉ nhận chuyển khoản thường hoặc tiền mặt", 100, "Đúng!"],
        ["Bấm link xem trước", 30, "Link giả có thể đánh cắp tài khoản."],
        ["Nhờ bố mẹ kiểm tra cùng", 90, "Rất tốt."]],
      sig: [["Đăng nhập qua link để nhận tiền", 1], ["Đòi đọc mã", 1], ["Mua bán với người lạ", 1], ["Nói về ví điện tử", 0], ["Lời lẽ thân thiện", 0]],
      lesson: "Nhận tiền chỉ cần số tài khoản; ai bắt đăng nhập, đọc mã là lừa." },
  ];
  const LEVEL = [[85, "Miễn dịch cao"], [70, "Vững vàng"], [40, "Đang hình thành"], [0, "Dễ tổn thương"]];
  const ALPHA = 0.4, START = 40, HALF_LIFE_DAYS = 90, DAY = 864e5;

  function blank() {
    return { v: 1, enabled: false, consent: false, freq: "tuan", from: 17, to: 21, mastery: {}, history: [], seen: [], next: 0, pending: null };
  }
  // ---- lưu trữ: chrome.storage (tiện ích) hoặc localStorage (app web, Android, iOS) ----
  const KEY = "edushield_drill";
  function load() {
    return new Promise((res) => {
      try {
        if (g.chrome && chrome.storage && chrome.storage.local) chrome.storage.local.get(KEY, (o) => res(Object.assign(blank(), (o && o[KEY]) || {})));
        else res(Object.assign(blank(), JSON.parse((g.localStorage && localStorage.getItem(KEY)) || "{}")));
      } catch (e) { res(blank()); }
    });
  }
  function save(s) {
    return new Promise((res) => {
      try {
        if (g.chrome && chrome.storage && chrome.storage.local) chrome.storage.local.set({ [KEY]: s }, () => res());
        else { localStorage.setItem(KEY, JSON.stringify(s)); res(); }
      } catch (e) { res(); }
    });
  }
  // ---- độ thành thạo từng nhóm, có quên dần theo thời gian ----
  function effective(rec, now) {
    if (!rec || !rec.n) return null;
    const days = Math.max(0, (now - rec.last) / DAY);
    return 50 + (rec.m - 50) * Math.pow(0.5, days / HALF_LIFE_DAYS);
  }
  // Chỉ số miễn dịch số: trung bình có trọng số của các nhóm; nhóm chưa luyện tính START (chưa rõ) với trọng số nhỏ.
  function dii(s, now) {
    now = now || Date.now();
    let sw = 0, sm = 0; const by = {};
    for (const gk of Object.keys(GROUPS)) {
      const rec = s.mastery[gk];
      const e = effective(rec, now);
      const w = e == null ? 0.3 : 1 - Math.pow(0.6, rec.n);
      const m = e == null ? START : e;
      by[gk] = { m: Math.round(m), n: rec ? rec.n : 0 };
      sw += w; sm += w * m;
    }
    const value = Math.round(sm / sw);
    return { value, level: LEVEL.find(([t]) => value >= t)[1], by, tried: Object.values(s.mastery).filter((r) => r.n).length };
  }
  // ---- chấm điểm một lần diễn tập ----
  function score(sc, actIdx, picked, ms) {
    const a = sc.act[actIdx];
    const truth = sc.sig.map((x) => x[1] === 1);
    const pos = truth.filter(Boolean).length;
    let hit = 0, wrong = 0;
    picked.forEach((on, i) => { if (on && truth[i]) hit++; if (on && !truth[i]) wrong++; });
    const sigScore = pos ? Math.max(0, Math.min(100, Math.round(100 * hit / pos - 25 * wrong))) : (wrong ? Math.max(0, 100 - 50 * wrong) : 100);
    const total = Math.round(0.7 * a[1] + 0.3 * sigScore);
    return { total, actScore: a[1], sigScore, hit, pos, wrong, ms: ms || 0, why: a[2], best: sc.act.reduce((b, x, i) => (x[1] > sc.act[b][1] ? i : b), 0) };
  }
  function update(s, sc, r, now) {
    now = now || Date.now();
    const rec = s.mastery[sc.g] || { m: START, n: 0, last: now };
    const base = effective(rec, now); // quên dần trước khi cập nhật
    rec.m = Math.round(((base == null ? START : base) + ALPHA * (r.total - (base == null ? START : base))) * 10) / 10;
    rec.n += 1; rec.last = now;
    s.mastery[sc.g] = rec;
    s.history.push({ t: now, id: sc.id, g: sc.g, score: r.total, dii: 0 });
    s.history[s.history.length - 1].dii = dii(s, now).value;
    if (s.history.length > 200) s.history = s.history.slice(-200);
    s.seen = [sc.id, ...s.seen.filter((x) => x !== sc.id)].slice(0, 10);
    return s;
  }
  // ---- chọn tình huống tiếp theo: ưu tiên nhóm còn yếu và lâu chưa luyện; độ khó theo năng lực ----
  function pick(s, rng, now) {
    rng = rng || Math.random; now = now || Date.now();
    const ws = Object.keys(GROUPS).map((gk) => {
      const rec = s.mastery[gk], e = effective(rec, now);
      const m = e == null ? START : e;
      const days = rec ? Math.min(14, (now - rec.last) / DAY) : 14;
      return [gk, (100 - m + 15) * (1 + days / 7) * (rec && rec.n ? 1 : 1.5)];
    });
    let r = rng() * ws.reduce((a, [, w]) => a + w, 0), gk = ws[0][0];
    for (const [k, w] of ws) { r -= w; if (r <= 0) { gk = k; break; } }
    const rec = s.mastery[gk], m = effective(rec, now) == null ? START : effective(rec, now);
    const want = m < 50 ? 1 : m < 75 ? 2 : 3;
    let pool = S.filter((x) => x.g === gk && !s.seen.includes(x.id));
    if (!pool.length) pool = S.filter((x) => x.g === gk);
    pool.sort((a, b) => Math.abs(a.lv - want) - Math.abs(b.lv - want));
    const best = pool.filter((x) => Math.abs(x.lv - want) === Math.abs(pool[0].lv - want));
    return best[Math.floor(rng() * best.length)];
  }
  // Ngẫu nhiên hoá cả tình huống lẫn thời điểm ĐỂ RÈN PHẢN XẠ (như diễn tập phòng cháy), nhưng chỉ trong khung giờ học sinh chọn
  function scheduleNext(s, now, rng) {
    rng = rng || Math.random; now = now || Date.now();
    if (!s.enabled || s.freq === "tat") return 0;
    const days = s.freq === "thuong" ? 2 + rng() * 1.5 : 5 + rng() * 4;
    const d = new Date(now + days * DAY);
    const hour = s.from + rng() * Math.max(0.5, s.to - s.from);
    d.setHours(Math.floor(hour), Math.floor((hour % 1) * 60), 0, 0);
    return d.getTime();
  }
  function byId(id) { return S.find((x) => x.id === id); }

  // ---------------- GIAO DIỆN ----------------
  const esc = (x) => String(x).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  function spark(hist) {
    const pts = hist.slice(-20).map((h) => h.dii);
    if (pts.length < 2) return "";
    const W = 300, H = 70, n = pts.length;
    const xy = pts.map((v, i) => [Math.round(i * (W - 10) / (n - 1)) + 5, Math.round(H - 8 - (v / 100) * (H - 16))]);
    return `<svg class="spark" viewBox="0 0 ${W} ${H}" role="img" aria-label="Chỉ số miễn dịch số qua ${n} lần diễn tập gần nhất">
      <line x1="0" x2="${W}" y1="${H - 8 - 0.7 * (H - 16)}" y2="${H - 8 - 0.7 * (H - 16)}" class="sl"/>
      <polyline points="${xy.map((p) => p.join(",")).join(" ")}" class="sp"/>${xy.map(([x, y]) => `<circle cx="${x}" cy="${y}" r="3" class="sd"/>`).join("")}</svg>`;
  }
  function mount(root, opt) {
    opt = opt || {};
    let st = blank(), cur = null, t0 = 0, actIdx = -1, picked = [];
    const view = (h) => { root.innerHTML = h; };
    async function home() {
      st = await load();
      const d = dii(st);
      const rows = Object.entries(GROUPS).map(([gk, name]) => {
        const b = d.by[gk];
        return `<div class="grow"><span>${esc(name)}</span><span class="bar"><i style="width:${b.m}%" class="${b.n ? "" : "un"}"></i></span><b>${b.n ? b.m : "?"}</b></div>`;
      }).join("");
      const last = st.history.slice(-5).reverse().map((h) => `<li>${new Date(h.t).toLocaleDateString("vi-VN")} · ${esc(GROUPS[h.g])}: <b>${h.score}</b> điểm</li>`).join("");
      view(`<div class="card hero"><div class="lbl">Chỉ số miễn dịch số</div><div class="big">${d.value}<small>/100</small></div>
          <div class="lv">${esc(d.level)} · đã luyện ${d.tried}/${Object.keys(GROUPS).length} nhóm kỹ năng</div>${spark(st.history)}</div>
        <div class="card"><b>🎯 Thực chiến giả lập</b><p class="small">Giống diễn tập phòng cháy: thỉnh thoảng EduShield gửi một tin nhắn <b>giả định</b> để bạn luyện phản xạ. Tin luôn đến từ EduShield, mọi tên, số, link đều giả, điểm chỉ lưu trên máy này.</p>
          ${st.consent ? "" : `<label class="chk"><input type="checkbox" id="dConsent"> Mình hiểu và muốn thử. Tin diễn tập có thể đến bất ngờ trong khung giờ mình chọn.</label>`}
          <div class="row"><label>Tần suất <select id="dFreq"><option value="tat">Tắt (chỉ khi mình bấm)</option><option value="tuan">Khoảng 1 lần/tuần</option><option value="thuong">2–3 lần/tuần</option></select></label>
          <label>Khung giờ <select id="dWin"><option value="17-21">17h–21h</option><option value="12-14">12h–14h</option><option value="19-22">19h–22h</option></select></label></div>
          <div class="row"><button id="dStart">▶️ Diễn tập ngay</button><button class="sec" id="dSave">Lưu</button></div>
          <p class="small" id="dMsg">${st.enabled && st.next ? "Lần diễn tập tiếp theo: bất ngờ trong khung giờ đã chọn." : ""}</p></div>
        <div class="card"><b>Theo nhóm kỹ năng</b>${rows}<p class="small">Điểm giảm dần nếu lâu không luyện; nhóm chưa luyện hiện “?”.</p></div>
        ${last ? `<div class="card"><b>Gần đây</b><ul class="hist">${last}</ul></div>` : ""}`);
      root.querySelector("#dFreq").value = st.enabled ? st.freq : "tat";
      root.querySelector("#dWin").value = `${st.from}-${st.to}`;
      root.querySelector("#dSave").onclick = saveSettings;
      root.querySelector("#dStart").onclick = () => start();
    }
    async function saveSettings() {
      const c = root.querySelector("#dConsent");
      if (c && !c.checked) { root.querySelector("#dMsg").textContent = "Hãy tích ô đồng ý trước khi bật."; return; }
      if (c) st.consent = true;
      const f = root.querySelector("#dFreq").value, [a, b] = root.querySelector("#dWin").value.split("-").map(Number);
      st.enabled = f !== "tat"; st.freq = f; st.from = a; st.to = b;
      st.next = scheduleNext(st); await save(st);
      if (opt.onSchedule) opt.onSchedule(st);
      root.querySelector("#dMsg").textContent = st.enabled ? "Đã lưu. Tin diễn tập sẽ đến bất ngờ trong khung giờ đã chọn." : "Đã tắt diễn tập tự động.";
    }
    async function start(id) {
      st = await load();
      cur = (id && byId(id)) || pick(st);
      actIdx = -1; picked = cur.sig.map(() => false);
      view(`<div class="phone"><div class="ph-top">📩 ${esc(cur.from)}</div><div class="ph-body" id="bub"></div></div><div id="q"></div>`);
      const bub = root.querySelector("#bub");
      cur.msgs.forEach((m, i) => setTimeout(() => { bub.insertAdjacentHTML("beforeend", `<div class="bubble">${esc(m)}</div>`); }, 350 * (i + 1)));
      setTimeout(ask, 350 * (cur.msgs.length + 1));
    }
    function ask() {
      t0 = Date.now();
      root.querySelector("#q").innerHTML = `<div class="card"><b>Bạn sẽ làm gì?</b>${cur.act.map((a, i) => `<button class="opt" data-a="${i}">${esc(a[0])}</button>`).join("")}</div>`;
      root.querySelectorAll("[data-a]").forEach((b) => (b.onclick = () => { actIdx = +b.dataset.a; signs(); }));
    }
    function signs() {
      const ms = Date.now() - t0;
      root.querySelector("#q").innerHTML = `<div class="card"><b>Tin này có những dấu hiệu nguy cơ nào?</b><p class="small">Chọn tất cả dấu hiệu nguy cơ bạn thấy. Nếu không có, bấm luôn “Xem kết quả”.</p>
        <div class="chips">${cur.sig.map((s, i) => `<button class="chip" data-s="${i}">${esc(s[0])}</button>`).join("")}</div><button id="dDone">Xem kết quả</button></div>`;
      root.querySelectorAll("[data-s]").forEach((b) => (b.onclick = () => { const i = +b.dataset.s; picked[i] = !picked[i]; b.classList.toggle("on", picked[i]); }));
      root.querySelector("#dDone").onclick = () => reveal(ms);
    }
    async function reveal(ms) {
      st = await load();
      const before = dii(st).value;
      const r = score(cur, actIdx, picked, ms);
      update(st, cur, r);
      if (st.enabled) st.next = scheduleNext(st);
      st.pending = null; await save(st);
      if (opt.onSchedule) opt.onSchedule(st);
      const after = dii(st).value, delta = after - before;
      root.querySelector("#q").innerHTML = `<div class="card reveal"><div class="tag">🛡️ Đây là bài DIỄN TẬP của EduShield, không phải tin thật</div>
        <div class="big2">${r.total}<small> điểm</small></div>
        <p><b>Bạn chọn:</b> ${esc(cur.act[actIdx][0])} <span class="pill ${r.actScore >= 90 ? "ok" : r.actScore >= 50 ? "mid" : "bad"}">${r.actScore >= 90 ? "An toàn" : r.actScore >= 50 ? "Tạm được" : "Nguy hiểm"}</span></p>
        <p class="small">${esc(r.why)}</p>
        ${r.actScore < 90 ? `<p><b>Nên làm:</b> ${esc(cur.act[r.best][0])}</p>` : ""}
        <p><b>Dấu hiệu:</b> ${cur.sig.map((s, i) => `<span class="chip ${s[1] ? "yes" : "no"} ${picked[i] ? "on" : ""}">${s[1] ? "⚠️" : "·"} ${esc(s[0])}</span>`).join(" ")}</p><p class="small">⚠️ là dấu hiệu nguy cơ thật; ô viền đậm là ô bạn đã chọn.</p>
        <p class="lesson">💡 ${esc(cur.lesson)}</p>
        <p>Chỉ số miễn dịch số: <b>${before} → ${after}</b> ${delta > 0 ? "⬆️" : delta < 0 ? "⬇️" : ""}</p>
        <div class="row"><button id="dAgain">Tình huống khác</button><button class="sec" id="dHome">Xem chỉ số</button></div></div>`;
      root.querySelector("#dAgain").onclick = () => start();
      root.querySelector("#dHome").onclick = home;
      if (opt.onResult) opt.onResult(r, cur);
    }
    const q = new URLSearchParams(g.location ? g.location.search : "");
    if (q.get("id") || q.get("auto") || g.__EDUSHIELD_AUTO) start(q.get("id")); else home();
    return { home, start };
  }

  g.EduShieldDrill = { GROUPS, SCENARIOS: S, LEVEL, load, save, blank, dii, score, update, pick, scheduleNext, byId, mount, effective };
})(typeof globalThis !== "undefined" ? globalThis : this);

"""TẬP KIỂM TRA VIẾT TAY (v1.7) - chỉ dùng để ĐO, tuyệt đối không dùng để huấn luyện hay chọn ngưỡng.

Học sinh tự viết từng câu (không sinh từ khuôn câu), theo văn phong thường gặp trên mạng:
bài tuyên truyền của công an, nhà trường, báo chí; bình luận, lời nhắc nhau cảnh giác;
tin bình thường dễ bị nhầm; và tin nguy cơ thật, kể cả tin lừa đảo GIẢ DẠNG lời cảnh báo.
Mọi tên, số, link đều là giả.

Cột: text, label (binh_thuong / bat_nat / lua_dao), nhom
  tuyen_truyen : nội dung tuyên truyền, cảnh báo, kể lại, giáo dục (nhắc tới nguy cơ nhưng KHÔNG nhắm vào người đọc)
  thuong_kho   : tin bình thường có từ dễ gây nhầm
  truc_tiep    : tin nguy cơ nhắm thẳng vào người đọc
  gia_canh_bao : tin nguy cơ giả dạng lời cảnh báo, thông báo chính thức
Chạy: python src/kiem_tra_viet_tay.py -> data/kiem_tra_viet_tay.csv
"""
import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TUYEN_TRUYEN = [
    # --- công an, cơ quan chức năng khuyến cáo ---
    "Công an tỉnh khuyến cáo: tuyệt đối không cung cấp mã OTP, mật khẩu cho bất kỳ ai, kể cả người tự xưng là nhân viên ngân hàng.",
    "Cảnh báo thủ đoạn mới: đối tượng giả danh công an gọi điện cho học sinh, nói em liên quan vụ án rửa tiền rồi yêu cầu giữ bí mật với gia đình.",
    "Bộ Công an khẳng định cơ quan công an không làm việc qua điện thoại, Zalo hay Facebook và không bao giờ yêu cầu chuyển tiền vào tài khoản cá nhân.",
    "Nguyên tắc 3 kiểm tra - 3 không: không vội tin, không chuyển tiền, không cung cấp thông tin cá nhân khi chưa xác minh.",
    "Thời gian gần đây xuất hiện tình trạng kẻ gian mạo danh giáo viên chủ nhiệm nhắn tin cho phụ huynh báo con cấp cứu, yêu cầu chuyển tiền viện phí.",
    "Các đối tượng thường dụ học sinh làm nhiệm vụ online, ban đầu trả hoa hồng nhỏ để tạo lòng tin rồi yêu cầu nạp số tiền lớn hơn.",
    "Phòng An ninh mạng khuyến cáo người dân không bấm vào đường link lạ được gửi qua tin nhắn, đặc biệt là link yêu cầu đăng nhập để nhận quà.",
    "Lưu ý: ngân hàng không bao giờ gửi tin nhắn kèm đường link yêu cầu khách hàng cập nhật thông tin hay xác thực tài khoản.",
    "Thủ đoạn bắt cóc online thường kéo dài nhiều giờ, kẻ gian yêu cầu nạn nhân thuê phòng khách sạn ở một mình và tắt liên lạc với người thân.",
    "Nếu nhận được cuộc gọi xưng là viện kiểm sát, toà án yêu cầu phối hợp điều tra qua video, hãy cúp máy và báo ngay cho bố mẹ hoặc gọi 113.",
    "Công an phường đề nghị phụ huynh nhắc con không cho người khác mượn, thuê tài khoản ngân hàng vì có thể bị lợi dụng để rửa tiền.",
    "Cảnh giác với lời mời việc nhẹ lương cao, làm cộng tác viên tại nhà, chỉ cần điện thoại là có thu nhập vài trăm nghìn mỗi ngày.",
    "Cục An toàn thông tin ghi nhận nhiều trang web giả mạo cổng tuyển sinh, đề nghị thí sinh chỉ tra cứu điểm trên trang chính thức của Bộ.",
    "Khuyến cáo: không tham gia các hội nhóm hứa lấy lại tiền đã bị lừa, đây thường là bẫy lừa đảo lần hai.",
    "Kẻ xấu có thể chiếm tài khoản Facebook của bạn bè rồi nhắn tin nhờ mua thẻ cào hoặc chuyển khoản gấp, hãy gọi điện xác minh trước.",
    "Đối tượng lừa đảo thường tạo cảm giác khẩn cấp như tài khoản sẽ bị khoá trong 24 giờ để nạn nhân không kịp suy nghĩ.",
    "Học sinh, sinh viên không mua bán, cho thuê, cho mượn tài khoản thanh toán, thẻ ngân hàng, giấy tờ tuỳ thân dưới bất kỳ hình thức nào.",
    "Không có chương trình trúng thưởng nào bắt người nhận phải đóng phí trước, mọi yêu cầu như vậy đều là dấu hiệu lừa đảo.",
    "Mùa nhập học, các đối tượng giả danh nhà trường gửi giấy báo trúng tuyển giả kèm link yêu cầu đóng phí giữ chỗ.",
    "Bộ Giáo dục và Đào tạo khẳng định không tổ chức cuộc thi thu phí qua tài khoản cá nhân, đề nghị học sinh cảnh giác.",
    # --- nhà trường, giáo viên nhắc nhở ---
    "Nhà trường thông báo: học phí chỉ nộp qua tài khoản của trường in trên giấy báo, các em không chuyển tiền cho bất kỳ tài khoản cá nhân nào.",
    "Cô nhắc cả lớp: nếu có ai nhắn tin xưng là cô để xin tiền quỹ hay số điện thoại phụ huynh thì đó là tài khoản giả, các em báo cô ngay nhé.",
    "Tiết sinh hoạt tuần này lớp mình thảo luận chủ đề nhận diện bắt nạt trên mạng và cách giúp đỡ bạn bị bắt nạt.",
    "Thầy hiệu trưởng nhắc học sinh không quay clip, không chia sẻ hình ảnh đánh nhau lên mạng xã hội vì đó cũng là hành vi bạo lực.",
    "Đoàn trường phát động cuộc thi thiết kế poster với chủ đề nói không với bạo lực học đường và bắt nạt trực tuyến.",
    "Phòng tư vấn tâm lý của trường mở cửa vào giờ ra chơi, bạn nào đang bị trêu chọc, cô lập hay đe doạ trên mạng có thể đến gặp cô.",
    "Thông báo: buổi ngoại khoá an toàn trên không gian mạng sẽ có cán bộ công an đến chia sẻ về các thủ đoạn lừa đảo nhắm vào học sinh.",
    "Giáo viên chủ nhiệm đề nghị phụ huynh dành thời gian trò chuyện với con về những tin nhắn lạ, đặc biệt là tin yêu cầu giữ bí mật.",
    "Mỗi học sinh cần nhớ: khi bị doạ tung ảnh riêng tư, không gửi thêm ảnh và không chuyển tiền, hãy kể ngay với người lớn tin cậy.",
    "Nội quy lớp: không đặt biệt danh xúc phạm, không chế ảnh bạn, không lập nhóm chat để nói xấu hay tẩy chay bạn khác.",
    # --- giáo dục, định nghĩa ---
    "Bắt nạt trên mạng là hành vi dùng mạng xã hội, tin nhắn để lăng mạ, đe doạ, tung tin đồn hoặc cô lập một người một cách lặp đi lặp lại.",
    "Các hình thức bắt nạt trực tuyến phổ biến gồm chế giễu ngoại hình, bình luận ác ý, đăng ảnh xấu, lập nhóm tẩy chay và mạo danh để nói xấu.",
    "Dấu hiệu con bị bắt nạt trên mạng: ngại dùng điện thoại, giật mình khi có tin nhắn, buồn bã, không muốn đến trường.",
    "Theo khảo sát, nhiều học sinh bị bắt nạt trên mạng nhưng không biết tìm sự giúp đỡ ở đâu, vì vậy cần có kênh hỗ trợ kín đáo.",
    "Những câu như mày béo như heo, đồ vô dụng nghe có vẻ là trêu đùa nhưng lặp lại nhiều lần có thể gây tổn thương sâu sắc.",
    "Tống tiền bằng ảnh nhạy cảm là thủ đoạn đối tượng làm quen, xin ảnh riêng tư rồi đe doạ phát tán nếu không gửi tiền.",
    "Tổng đài quốc gia bảo vệ trẻ em 111 hoạt động 24/7, miễn phí, tiếp nhận thông tin về bạo lực, xâm hại và bắt nạt trẻ em.",
    "Chiến dịch Không một mình nhắn nhủ các bạn trẻ: khi gặp chuyện trên mạng, hãy chia sẻ với người thân, thầy cô, đừng tự xử lý một mình.",
    "10 điều thanh thiếu niên cần nhớ để an toàn trực tuyến: bảo vệ mật khẩu, không gặp người quen qua mạng một mình, không gửi ảnh riêng tư.",
    "Trong bài học hôm nay, các em sẽ phân tích một tin nhắn lừa đảo mẫu để tìm ra các dấu hiệu như giục gấp, đòi chuyển tiền và link lạ.",
    # --- trích lại lời kẻ xấu để cảnh báo ---
    "Nếu bạn nhận được tin kiểu “Bạn đã trúng iPhone, bấm link để nhận quà” thì đừng bấm, đó là lừa đảo.",
    "Mọi người cẩn thận nhé, có acc giả cô chủ nhiệm nhắn “con chuyển gấp 500k tiền quỹ lớp vào số này” đấy, đừng ai chuyển.",
    "Kẻ gian thường nhắn: “Đây là công an, em có liên quan đến vụ án, không được nói với bố mẹ”. Gặp câu này hãy báo người thân ngay.",
    "Câu “gửi mình mã OTP vừa nhận được với, mình bấm nhầm” là chiêu quen thuộc để chiếm tài khoản, tuyệt đối không gửi.",
    "Một tin nhắn lừa đảo điển hình: “Việc nhẹ lương cao, làm tại nhà, mỗi ngày 500k, nạp trước 200k để kích hoạt tài khoản.”",
    "Ví dụ về bắt nạt trên mạng: “Cả lớp đừng ai chơi với nó nữa”, “Đăng ảnh xấu của nó lên cho mọi người cười”. Nếu thấy, hãy báo thầy cô.",
    "Có bạn hỏi câu “mày mà mách cô thì biết tay” có phải bắt nạt không. Có, đó là lời đe doạ và cần được báo cho người lớn.",
    "Đoạn chat mẫu trong tài liệu: kẻ xấu nói “ở yên trong phòng, bật camera, giữ bí mật” – đây là dấu hiệu bắt cóc online.",
    "Thủ đoạn quen thuộc: tin nhắn báo “tài khoản của bạn sẽ bị khoá, đăng nhập ngay tại link sau để xác minh”. Đừng làm theo.",
    "Hôm trước có người nhắn em gái mình “chị chuyển nhầm tiền vào tài khoản em, em chuyển lại giúp chị”, nhà mình báo ngân hàng thì mới biết là lừa.",
    # --- kể lại, chia sẻ trải nghiệm, tin tức ---
    "Hôm qua mình bị một số lạ gọi xưng là công an, bảo mình dính vụ rửa tiền, may mà mình cúp máy rồi gọi cho bố.",
    "Một nữ sinh lớp 11 bị lừa gần 200 triệu đồng sau khi bị kẻ gian giả danh công an thao túng tâm lý suốt hai ngày.",
    "Báo đưa tin một nhóm học sinh bị phạt vì lập trang confession bôi nhọ bạn cùng trường.",
    "Năm ngoái lớp mình có bạn bị tẩy chay trong nhóm chat, sau đó cô chủ nhiệm và phòng tư vấn đã giúp bạn ấy rất nhiều.",
    "Nhà mình suýt mất tiền vì tin nhắn giả ngân hàng, giờ mình luôn gọi tổng đài in trên thẻ để kiểm tra.",
    "Công an đã khởi tố đường dây lừa đảo tuyển cộng tác viên online chiếm đoạt hàng tỷ đồng của hàng trăm sinh viên.",
    "Video tái hiện cảnh một học sinh bị bạn bè đe doạ qua tin nhắn được chiếu trong buổi chào cờ để mọi người rút kinh nghiệm.",
    "Em từng bị trêu là đồ béo trên nhóm lớp, giờ em muốn chia sẻ để các bạn biết những câu đùa đó làm người khác buồn thế nào.",
    "Tin tức: lực lượng chức năng triệt phá nhóm đối tượng mua bán tài khoản ngân hàng của sinh viên để rửa tiền.",
    "Bạn mình kể bị người lạ làm quen rồi xin ảnh, may mà bạn ấy kể với mẹ trước khi gửi.",
    # --- bình luận dưới bài tuyên truyền ---
    "Cảm ơn công an đã cảnh báo, hôm trước nhà em cũng nhận được cuộc gọi giả danh như vậy.",
    "Chia sẻ để mọi người cùng biết, đặc biệt là phụ huynh có con đang đi học.",
    "Bài viết rất hữu ích, mình sẽ gửi cho nhóm lớp để các bạn đề phòng.",
    "Ai đọc được thì nhắc ông bà bố mẹ giúp nhé, người lớn tuổi hay bị lừa kiểu này lắm.",
    "Cái vụ đòi mã OTP này tháng trước bạn em dính rồi, mất luôn tài khoản game.",
    "Đúng là phải nói với con từ sớm, đừng để con một mình đối mặt với mấy tin nhắn đe doạ.",
    "Lớp em vừa được nghe tuyên truyền về lừa đảo việc nhẹ lương cao, thấy rất thực tế.",
    "Mọi người đừng share clip đánh nhau nữa, như vậy là tiếp tay cho bạo lực đó.",
    "Tag những người bạn cần đọc bài này để không bị lừa chuyển tiền nhé.",
    "Nhớ kỹ: công an không bao giờ bắt mình chuyển tiền qua mạng, gặp là cúp máy.",
    # --- lời động viên, hỗ trợ người bị bắt nạt ---
    "Đừng để ý mấy lời chê bai trên mạng, bạn không có lỗi gì cả, mình luôn ở đây nếu bạn cần.",
    "Nếu ai trong lớp đang bị nói xấu hay bị đe doạ, cứ nhắn riêng mình, mình sẽ đi cùng bạn đến gặp cô.",
    "Mình không đồng ý với việc cả nhóm tẩy chay bạn ấy, như thế là bắt nạt chứ không phải đùa.",
    "Bạn ơi đừng sợ, việc bị tung tin đồn không phải lỗi của bạn, mình báo thầy cô cùng nhau nhé.",
    "Các bạn ơi dừng lại đi, bình luận chê ngoại hình người khác như vậy là không ổn.",
    "Ai bị doạ đánh sau giờ học thì báo giám thị ngay, đừng đi một mình nhé.",
    "Mình đã chặn và báo cáo tài khoản chuyên đăng ảnh chế bạn trong lớp, mọi người cũng báo cáo giúp nhé.",
    "Hôm nay lớp mình cùng ký cam kết không bắt nạt, không cô lập bạn bè trên mạng xã hội.",
    # --- poster, khẩu hiệu ---
    "Nói không với bạo lực học đường – Hãy là người bạn tử tế trên không gian mạng.",
    "Dừng lại – Suy nghĩ – Kiểm tra trước khi chuyển tiền hay bấm vào đường link lạ.",
    "Đừng im lặng khi thấy bạn bị bắt nạt, một lời lên tiếng có thể thay đổi tất cả.",
    "Mật khẩu và mã OTP là chìa khoá nhà bạn, đừng trao cho người lạ.",
    "Chậm một giây, an toàn cả đời: xác minh trước khi chuyển khoản.",
    "Mạng xã hội không phải nơi để trút giận, hãy bình luận bằng sự tôn trọng.",
    # --- thông báo chính thống có từ tiền, OTP ---
    "Ngân hàng thông báo: chúng tôi không bao giờ yêu cầu khách hàng cung cấp mã OTP qua điện thoại, tin nhắn hay mạng xã hội.",
    "Ứng dụng sẽ gửi mã OTP để bạn tự xác nhận giao dịch, không chia sẻ mã này với bất kỳ ai, kể cả nhân viên ngân hàng.",
    "Trường đã gửi giấy báo nộp học phí qua sổ liên lạc điện tử, phụ huynh vui lòng đối chiếu số tài khoản của trường trước khi nộp.",
    "Hướng dẫn: khi phát hiện trang giả mạo, người dân có thể báo cáo qua cổng cảnh báo an toàn thông tin của cơ quan chức năng.",
    "Infographic: 5 dấu hiệu nhận biết tin nhắn lừa đảo gồm giục gấp, đòi tiền, xin mã, link lạ và yêu cầu giữ bí mật.",
    # --- thêm đa dạng ---
    "Thông tin về việc nhiều tài khoản giả mạo thầy cô xuất hiện trong các nhóm phụ huynh đầu năm học là có thật, mong các bố mẹ cảnh giác.",
    "Trong buổi tập huấn, chuyên gia phân tích vì sao kẻ lừa đảo hay dọa nạn nhân bằng cụm từ vụ án, lệnh bắt và tài khoản bị phong toả.",
    "Bài thuyết trình nhóm em về chủ đề bắt nạt qua mạng: nguyên nhân, hậu quả và cách phòng tránh.",
    "Đề bài nghị luận: Suy nghĩ của em về hiện tượng học sinh quay clip bạn bị đánh rồi đăng lên mạng.",
    "Tờ rơi phát cho học sinh ghi rõ: không ai có quyền ép em giữ bí mật với bố mẹ, nếu có, đó là dấu hiệu nguy hiểm.",
    "Khi thấy ai đó bị bình luận ác ý, bạn có thể nhắn tin hỏi thăm, báo cáo bình luận và kể với người lớn.",
    "Một số trang mạng đăng tuyển người mẫu nhí rồi thu phí casting, phụ huynh nên kiểm tra kỹ trước khi đăng ký cho con.",
    "Người dân phản ánh nhận tin nhắn tự xưng điện lực đòi tiền điện kèm đường link lạ, công ty điện lực khẳng định không gửi tin như vậy.",
    "Tâm sự: mình từng là người im lặng khi bạn bị cả nhóm chế giễu, giờ mình hối hận và mong các bạn đừng như mình.",
    "Hướng dẫn phụ huynh cài đặt quyền riêng tư cho tài khoản mạng xã hội của con để hạn chế người lạ nhắn tin.",
    "Cảnh báo phụ huynh: hiện có các nhóm kín trên mạng lôi kéo học sinh bỏ học đi làm việc nhẹ lương cao ở nước ngoài.",
    "Sáng nay trường tổ chức diễn đàn học sinh với chủ đề làm gì khi bị đe doạ tung ảnh trên mạng.",
    "Mình là lớp trưởng, mình xin nhắc lại là tiền quỹ lớp chỉ nộp trực tiếp cho thủ quỹ hoặc qua tài khoản trường, ai nhắn khác là giả.",
    "Phân biệt: trêu đùa là khi cả hai cùng vui, còn bắt nạt là khi một người bị tổn thương và không thể dừng lại.",
    "Nếu lỡ chuyển tiền cho kẻ lừa đảo, hãy gọi ngay tổng đài ngân hàng để yêu cầu tạm khoá và đến công an gần nhất trình báo.",
    "Chuyên mục an toàn số tuần này: nhận diện tài khoản mạo danh người nổi tiếng kêu gọi từ thiện.",
    "Đừng tin những lời hứa hẹn kiếm tiền dễ dàng trên mạng, đằng sau thường là cái bẫy.",
    "Tớ vừa đọc bài báo về thủ đoạn giả danh công an, thấy giống hệt cuộc gọi hôm qua của nhà tớ.",
    "Lời khuyên của cô tư vấn: khi bị chửi bới trên mạng, đừng đáp trả, hãy chụp màn hình lưu lại và báo người lớn.",
]

THUONG_KHO = [
    "Tối nay bắn rank không, tao gánh cho, đứa nào feed là tao kick khỏi team đấy nhé.",
    "Ê mày ngu thế, câu dễ vậy mà cũng sai, mai tao giảng lại cho haha.",
    "Mẹ ơi con chuyển khoản tiền mua sách cho cô rồi nhé, cô gửi số tài khoản trên nhóm lớp chính thức.",
    "Mình quên mật khẩu email, bấm quên mật khẩu thì nó gửi mã xác nhận về điện thoại của mình rồi, ổn rồi.",
    "Con nhận được mã OTP của ngân hàng khi mẹ đang chuyển tiền đúng không mẹ, con đọc mẹ nghe nhé.",
    "Lớp trưởng đây, mai các bạn nộp 50k tiền in đề cương trực tiếp cho mình trong giờ ra chơi nhé.",
    "Đứa nào ăn hết bánh của tao, khai ra không tao xử đẹp, đùa thôi mai mua bù nha.",
    "Game này boss khó vãi, tao chết 10 lần rồi, chắc phải nạp skin mới đánh nổi.",
    "Bố gửi con 200 nghìn vào tài khoản để mai con đi học thêm nhé.",
    "Cô gửi các em link bài tập trên trang của trường, hạn nộp tối thứ sáu.",
    "Thằng kia béo như con lợn mà chạy nhanh vãi, hôm nay đá bóng nó ghi hai bàn.",
    "Tao giận mày rồi đấy, đi xem phim mà không rủ tao, mai bao trà sữa thì tha.",
    "Nhóm mình cần chọn đề tài thuyết trình, mình đề xuất chủ đề an toàn trên mạng xã hội.",
    "Hôm nay cô cho làm bài kiểm tra 15 phút bất ngờ, cả lớp hoảng luôn.",
    "Ai có số điện thoại của thầy dạy toán không, mình cần hỏi lịch học bù.",
    "Bạn chuyển giúp mình 30k tiền vé gửi xe tháng này nhé, mình đưa tiền mặt bạn rồi mà bạn quên.",
    "Trận này thua là tại tao, tao vô dụng thật sự, mai tập lại.",
    "Chị ơi em đặt cọc 100k mua váy ở shop quen của lớp mình nha, chị gửi ảnh mẫu giúp em.",
    "Ê nhớ mang áo đoàn ngày mai nhé, ai quên là bị ghi tên đấy.",
    "Hôm nay mạng lag quá, đăng nhập vào app học mà nó cứ đòi xác minh lại hoài.",
    "Đi học về nhớ mua giúp mẹ chai nước mắm với nhé con.",
    "Tao với mày từ nay cạch mặt nhau, đùa đấy, mai qua nhà tao học nhóm.",
    "Phim kinh dị hôm qua có cảnh doạ ma ghê thật, tao mất ngủ luôn.",
    "Ông nội bảo cuối tuần cả nhà về quê, con nhớ ôn bài trước nhé.",
    "Mình vừa trúng giải ba cuộc thi vẽ của trường, cô bảo thứ hai lên nhận giấy khen.",
    "Trời ơi con mèo nhà tao lại cắn nát dây sạc rồi.",
    "Thầy nhắc ai chưa nộp đơn đăng ký câu lạc bộ thì nộp trước thứ tư.",
    "Đứa nào lấy nhầm áo khoác xanh của tao ở phòng thể chất thì trả lại giúp nhé.",
    "Nhóm học tiếng Anh tối nay học online qua Google Meet, link cô gửi trên Classroom.",
    "Tao bảo mày rồi, ăn nhiều thế béo như heo bây giờ, thôi ăn đi tao trêu thôi.",
    "Hôm nay mẹ chuyển tiền học phí qua app ngân hàng, mẹ bảo trường gửi hóa đơn điện tử rồi.",
    "Câu lạc bộ tranh biện tuần này tranh luận về việc có nên cấm điện thoại trong trường không.",
    "Shopee đang sale, ai mua chung đơn để được miễn phí ship không.",
    "Ê mai kiểm tra lý đấy, tao chết chắc rồi, chưa học chữ nào.",
    "Bạn nào nhặt được thẻ học sinh tên Minh lớp 10A2 thì báo giúp mình với.",
    "Tao block mày khỏi nhóm game một hôm vì spam meme quá, mai add lại.",
    "Cả nhà ơi tối nay ăn lẩu nhé, con về sớm phụ mẹ nấu.",
    "Mai trường tổ chức tiêm chủng, các bạn nhớ mang sổ tiêm.",
    "Bài văn của mày hay vãi, cô chắc cho mười điểm.",
    "Tớ cho cậu mượn vở ghi môn sử, nhớ trả trước thứ năm nhé.",
    "Hôm nay có bạn mới chuyển vào lớp, mọi người nhớ giúp đỡ bạn nhé.",
    "Chú bảo vệ nhắc học sinh dắt xe vào cổng phụ vì cổng chính đang sửa.",
    "Ê cho tao xin wifi nhà mày, mạng nhà tao hỏng rồi.",
    "Trận chung kết bóng đá trường chiều nay, cả lớp ra cổ vũ nhé.",
    "Thôi đừng buồn nữa, điểm thấp lần này thì lần sau cố gắng hơn.",
    "Ông bà gửi quà cho con qua bưu điện, mai con ra nhận giúp mẹ nhé, nhớ mang căn cước.",
    "Chiều nay câu lạc bộ nhảy tập ở sân sau, ai muốn tham gia thì cứ tới nhé.",
    "Cô chủ nhiệm nhắn trong nhóm chính thức: thứ bảy họp phụ huynh lúc 8 giờ tại phòng học lớp.",
    "Mấy câu đùa trong nhóm lớp hôm nay vui quá, cười đau cả bụng.",
    "Tao vừa xem video hướng dẫn làm bánh, cuối tuần thử làm rồi mời cả nhóm.",
]

TRUC_TIEP = [
    # lừa đảo
    "Đây là cán bộ điều tra, em đang liên quan đến đường dây rửa tiền, không được kể với ai, làm theo hướng dẫn của anh ngay.",
    "Em cần thuê một phòng khách sạn ở một mình, bật camera liên tục để bên điều tra theo dõi, tuyệt đối không liên lạc với gia đình.",
    "Cô chủ nhiệm đây, em chuyển gấp 300k tiền quỹ lớp vào số tài khoản 0123456789 giúp cô, cô đang bận họp.",
    "Bạn ơi mình bấm nhầm số, có mã 6 số gửi vào điện thoại bạn, đọc giúp mình với mình cần gấp.",
    "Chúc mừng bạn đã trúng thưởng điện thoại, bấm vào quatang-vn.xyz và nhập mật khẩu Facebook để nhận.",
    "Việc nhẹ lương cao cho học sinh, làm tại nhà mỗi ngày 300k, nạp trước 100k để kích hoạt nhiệm vụ.",
    "Tài khoản của bạn sẽ bị khoá trong 24h, đăng nhập tại bank-xacminh.top để xác thực ngay.",
    "Em ơi mua giúp chị 5 thẻ cào 100k rồi gửi mã qua đây, tối chị trả, chị đang kẹt quá.",
    "Bạn được chọn nhận học bổng 100%, đóng 500k phí hồ sơ vào tài khoản cá nhân của cán bộ phụ trách để giữ suất.",
    "Cho anh thuê tài khoản ngân hàng đứng tên em, mỗi tháng anh trả 2 triệu, không phải làm gì cả.",
    "Mẹ đây, mẹ đổi số rồi, con chuyển 1 triệu cho cô bán hàng theo số tài khoản này giúp mẹ nhé, gấp lắm.",
    "Nhóm kéo tài xỉu bao thắng, vào nhóm nạp 200k ăn 1 triệu, chỉ hôm nay thôi.",
    "Gửi ảnh mặt trước mặt sau căn cước và ngày sinh của em để anh làm hồ sơ nhận quà.",
    "Lần này em mà kể với bố mẹ thì hồ sơ của em sẽ chuyển sang toà, em sẽ bị bắt ngay.",
    "Anh có người quen trong hội đồng thi, đưa 5 triệu đảm bảo nâng điểm cho em.",
    # bắt nạt
    "Mày mà còn mách cô thì tan học ra cổng sau, tao cho mày biết tay.",
    "Cả lớp đừng ai chơi với con này nữa, đứa nào nói chuyện với nó là tao kick khỏi nhóm.",
    "Gửi 500k đây không thì tối nay ảnh của mày lên khắp các nhóm.",
    "Đồ béo như lợn, nhìn mặt mày thôi đã thấy ghét, biến khỏi lớp đi.",
    "Tao có ảnh chụp màn hình tin nhắn của mày rồi, không làm theo thì tao đăng lên confession.",
    "Ngày mai mang tiền đến nộp cho bọn tao, không thì đừng trách.",
    "Mày là thứ vô dụng nhất lớp, chết đi cho đỡ chật đất.",
    "Mọi người vào report nick con kia cho bay màu đi, spam chửi nó luôn.",
    "Nghe nói nó trộm tiền của bạn cùng phòng đấy, share cho cả trường biết đi.",
    "Từ nay nhóm mình không ai nói chuyện với thằng đó nữa, unfollow hết đi.",
    "Đứa nào bênh nó là tao xử luôn, nhớ mặt từng đứa.",
    "Ảnh dìm của mày tao lưu hết rồi, ngoan thì tao giữ, không thì cả trường xem.",
    "Câm mồm đi đồ rác rưởi, ai cho mày lên tiếng.",
    "Tối nay tao gửi địa chỉ nhà nó vào nhóm, ai rảnh thì qua hỏi thăm.",
    "Mày đi đường cẩn thận đấy, tao biết nhà mày ở đâu.",
    # thêm lừa đảo dạng bình luận, quảng cáo
    "Inbox mình nhận việc gõ chữ tại nhà, thu nhập 10 triệu một tháng, cọc 300k nhận tài liệu.",
    "Ai cần lấy lại tiền bị lừa inbox mình, hỗ trợ 100%, phí dịch vụ trả trước.",
    "Tặng 1000 kim cương miễn phí, nhập tài khoản và mật khẩu game tại link dưới.",
    "Shop đang xả hàng giá 1k, chuyển khoản trước 50k phí ship để giữ đơn nhé bạn.",
    "Tuyển CTV chốt đơn online, làm 15 phút mỗi ngày lãi gấp đôi tiền nạp.",
]

GIA_CANH_BAO = [
    "CẢNH BÁO: tài khoản của bạn có dấu hiệu bị lừa đảo, vui lòng xác minh danh tính tại vn-baomat.xyz trong 2 giờ để tránh bị khoá.",
    "Thông báo từ Bộ Công an: em có tên trong danh sách điều tra vụ án rửa tiền, giữ bí mật và chuyển tiền vào tài khoản tạm giữ để chứng minh trong sạch.",
    "Cảnh giác lừa đảo! Để bảo vệ tiền của bạn, hãy chuyển toàn bộ số dư sang tài khoản an toàn 0987654321 do ngân hàng chỉ định.",
    "Ngân hàng cảnh báo: giao dịch bất thường trên tài khoản của bạn, gửi mã OTP vừa nhận để chúng tôi huỷ giao dịch.",
    "Phòng chống lừa đảo: nhóm hỗ trợ nạn nhân lấy lại tiền, đóng phí hồ sơ 500k để luật sư xử lý vụ của bạn.",
    "Cục An toàn thông tin cảnh báo thiết bị của bạn nhiễm mã độc, tải ứng dụng bảo mật tại app-antoan.top và đăng nhập ngân hàng để quét.",
    "Nhà trường thông báo khẩn: học sinh chưa nộp học phí chuyển ngay vào tài khoản cá nhân của thầy kế toán trước 17h hôm nay.",
    "Tuyên truyền phòng chống bạo lực học đường: đứa nào đi mách cô là đứa đó tự chuốc hoạ, nhớ đấy.",
    "Công an thông báo: em vi phạm luật an ninh mạng, nộp phạt 2 triệu qua số tài khoản này nếu không sẽ bị khởi tố.",
    "Để tránh bị lừa, bạn hãy cung cấp số căn cước và mật khẩu ngân hàng để chúng tôi kích hoạt chế độ bảo vệ.",
    "Bài viết chống bắt nạt nhưng sự thật là con bé lớp 10A3 ấy đáng bị cả trường tẩy chay, mọi người share ảnh nó đi.",
    "Lưu ý quan trọng: tài khoản Zalo của bạn bị báo cáo vi phạm, đăng nhập lại tại zalo-hotro.site để không bị khoá vĩnh viễn.",
    "Thông báo trúng thưởng chương trình tri ân của nhà mạng, để tránh lừa đảo vui lòng chỉ nộp phí nhận quà qua số tài khoản chính thức sau.",
    "Viện kiểm sát cảnh báo: hồ sơ của em đang bị chuyển sang toà án, không được nói với bố mẹ, gọi lại số này ngay.",
    "Cảnh báo an ninh: bạn cần đọc mã xác minh vừa gửi tới điện thoại cho tổng đài viên để bảo vệ tài khoản.",
]

DATA = ([(t, "binh_thuong", "tuyen_truyen") for t in TUYEN_TRUYEN]
        + [(t, "binh_thuong", "thuong_kho") for t in THUONG_KHO]
        + [(t, "lua_dao" if i < 15 or i >= 30 else "bat_nat", "truc_tiep") for i, t in enumerate(TRUC_TIEP)]
        + [(t, "bat_nat" if ("mách" in t or "tẩy chay" in t) else "lua_dao", "gia_canh_bao") for t in GIA_CANH_BAO])


def main():
    out = os.path.join(ROOT, "data", "kiem_tra_viet_tay.csv")
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "text", "label", "nhom"])
        for i, (t, l, n) in enumerate(DATA, 1):
            w.writerow(["VT%03d" % i, t, l, n])
    from collections import Counter
    print(len(DATA), Counter(n for _, _, n in DATA), Counter(l for _, l, _ in DATA))


if __name__ == "__main__":
    main()

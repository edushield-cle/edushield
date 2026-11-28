"""BỘ DỮ LIỆU PHÂN BIỆT NGỮ CẢNH (v1.7): TUYÊN TRUYỀN hay ĐANG GẶP NGUY CƠ?

Vấn đề ở v1.6: bài tuyên truyền, tin tức, lời nhắc nhau cảnh giác dùng ĐÚNG những từ của kẻ xấu
(OTP, chuyển tiền, công an, vụ án, tẩy chay...) nên mô hình chỉ nhìn từ sẽ báo nhầm.
Bộ này dạy mô hình nhìn vào KHUNG của câu:
  - tuyen_truyen : nhắc tới thủ đoạn ở ngôi thứ ba (đối tượng, kẻ gian, nạn nhân), lời khuyên phủ định
                   (đừng, tuyệt đối không), trích lại tin lừa đảo trong ngoặc kép để cảnh báo, tin tức, kể lại,
                   định nghĩa, khẩu hiệu, bình luận ủng hộ, lời động viên người bị bắt nạt.
  - binh_thuong  : tin bình thường có từ dễ nhầm (chơi game, tự trêu mình, OTP của chính mình, chuyển tiền trong nhà).
  - lua_dao / bat_nat (gia_canh_bao) : tin nguy cơ GIẢ DẠNG lời cảnh báo, thông báo chính thức
                   để mô hình không bị đánh lừa bởi chữ "cảnh báo".
Cách viết khung câu dựa trên văn phong các khuyến cáo công khai của công an, Bộ GD&ĐT, Cục An toàn thông tin,
UNICEF; mọi tên, số, link đều GIẢ. Lõi tin nguy cơ được trích lại lấy từ phần HUẤN LUYỆN của bộ cũ (khung thuộc
tập huấn luyện) hoặc phần KIỂM TRA (khung thuộc tập kiểm tra độc lập) để không rò rỉ dữ liệu.

Chia theo KHUNG CÂU, phân tầng theo nhóm: 60% huấn luyện, 15% kiểm định, 25% kiểm tra độc lập (doc_lap).
Chạy:  python src/data_tuyen_truyen.py  -> data/bo_phan_biet_ngu_canh.csv
"""
import csv
import os
import random
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_gen_10k import TEN, MON, LOP, GIO, TIEN, XUC_PHAM, TIN_DON, augment, canon, phone, stk, SCAM_DOMAINS, PATHS  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = 2711

NGUON = ["Công an tỉnh", "Công an thành phố", "Công an phường", "Bộ Công an", "Cục An toàn thông tin", "Phòng An ninh mạng",
         "Bộ GD&ĐT", "Sở Giáo dục", "nhà trường", "Đoàn trường", "ngân hàng", "nhà mạng", "cơ quan chức năng",
         "Cục Cảnh sát hình sự", "Công an xã", "Hội Phụ nữ phường", "UNICEF", "báo điện tử"]
DONG_TU = ["cảnh báo", "khuyến cáo về", "lưu ý", "vừa phát đi cảnh báo về", "thông tin về", "nhắc nhở người dân về"]
NAN = ["người dân", "học sinh", "sinh viên", "phụ huynh", "các em học sinh", "người dùng mạng xã hội", "tân sinh viên",
       "người cao tuổi", "học sinh, sinh viên", "các gia đình", "thanh thiếu niên"]
NAN_1 = ["một nữ sinh", "một nam sinh lớp 11", "một sinh viên năm nhất", "một phụ huynh", "một học sinh lớp 9", "hai chị em",
         "một cụ ông", "một tân sinh viên", "một nữ sinh lớp 12"]
DIA = ["Hà Nội", "Nghệ An", "Đà Nẵng", "Cần Thơ", "Bắc Ninh", "Hải Phòng", "Quảng Nam", "Bình Dương", "Thanh Hoá",
       "Lâm Đồng", "Huế", "Khánh Hoà", "Thái Nguyên", "Đồng Nai"]
KENH = ["qua Zalo", "qua Facebook", "qua tin nhắn", "qua điện thoại", "trên TikTok", "qua Messenger", "trong nhóm chat lớp",
        "qua cuộc gọi video", "trên Telegram", "qua email"]
AI = ["em gái mình", "mẹ mình", "bạn cùng bàn của tớ", "bố em", "chị họ mình", "một bạn trong lớp", "bà nội tớ", "anh trai mình",
      "nhà mình", "đứa bạn thân của mình"]
AN_TOAN = ["mình đã gọi hỏi lại người thân", "bố mẹ phát hiện kịp", "mình kể với cô chủ nhiệm", "mình cúp máy ngay",
           "mình không bấm vào link", "mình nhớ lời công an tuyên truyền", "mình chặn luôn tài khoản đó", "cả nhà bình tĩnh kiểm tra lại"]
GIO2 = ["2 giờ", "24 giờ", "30 phút", "hôm nay"]

# Thủ đoạn, mô tả ở NGÔI THỨ BA (học sinh tóm tắt lại từ các khuyến cáo công khai)
THU_DOAN = {
    "ld_de_doa": [
        "giả danh công an, viện kiểm sát gọi điện nói nạn nhân liên quan vụ án rồi đe doạ bắt giam",
        "yêu cầu học sinh thuê phòng khách sạn ở một mình và cắt liên lạc với gia đình để phục vụ điều tra",
        "thao túng tâm lý, ép nạn nhân giữ bí mật với bố mẹ rồi buộc gia đình chuyển tiền",
        "nhắn tin báo tài khoản sắp bị khoá trong 24 giờ để nạn nhân hoảng sợ làm theo",
        "gọi video mặc trang phục công an, đọc lệnh bắt giả để uy hiếp tinh thần",
        "dựng kịch bản bắt cóc online, khủng bố tinh thần học sinh rồi đòi tiền chuộc",
    ],
    "ld_otp": [
        "giả danh nhân viên ngân hàng, nhà mạng gọi điện xin mã OTP",
        "chiếm tài khoản của bạn bè rồi nhắn nhờ đọc giúp mã xác nhận vừa gửi về máy",
        "gửi đường link giả trang ngân hàng để lấy mật khẩu và mã OTP",
        "dụ người dùng cung cấp mật khẩu game, mạng xã hội để nhận quà",
    ],
    "ld_chuyen_tien": [
        "mạo danh giáo viên chủ nhiệm nhắn phụ huynh chuyển tiền viện phí vì con bị tai nạn",
        "giả làm người thân vừa đổi số điện thoại rồi nhờ chuyển tiền gấp",
        "giả vờ chuyển nhầm tiền rồi đòi nạn nhân chuyển trả kèm lãi",
        "mạo danh nhà trường thu học phí, tiền quỹ qua tài khoản cá nhân",
        "rao phòng trọ giá rẻ, yêu cầu đặt cọc trước rồi chặn liên lạc",
        "giả danh ban quản lý ký túc xá yêu cầu chuyển tiền giữ chỗ",
    ],
    "ld_trung_thuong": [
        "thông báo trúng thưởng điện thoại, xe máy rồi yêu cầu đóng phí nhận quà",
        "giả mạo chương trình học bổng du học, thu phí hồ sơ và phí chứng minh tài chính",
        "mời trẻ làm người mẫu nhí rồi thu phí casting",
        "báo có bưu kiện quà tặng từ nước ngoài và đòi nộp phí hải quan",
        "tổ chức cuộc thi giả mạo danh nghĩa Bộ GD&ĐT để thu lệ phí",
    ],
    "ld_viec_lam": [
        "tuyển cộng tác viên làm nhiệm vụ online, ban đầu trả hoa hồng rồi yêu cầu nạp số tiền lớn",
        "mời làm việc nhẹ lương cao tại nhà và bắt đóng tiền cọc tài liệu",
        "lôi kéo đầu tư sinh lời gấp đôi chỉ trong vài ngày",
        "dụ học sinh bỏ học sang nước ngoài làm việc lương cao",
    ],
    "ld_thong_tin": [
        "xin ảnh căn cước, ngày sinh với lý do làm hồ sơ nhận quà",
        "giả mạo cổng dịch vụ công yêu cầu cập nhật thông tin định danh",
        "gửi phiếu khảo sát giả để thu thập thông tin cá nhân của học sinh",
    ],
    "ld_the_cao": ["chiếm Facebook của người quen rồi nhờ mua thẻ cào gửi mã", "nhờ học sinh nạp thẻ cào hộ rồi hứa trả gấp đôi"],
    "ld_khac": [
        "lôi kéo học sinh, sinh viên mở hoặc cho thuê tài khoản ngân hàng để rửa tiền",
        "mời tham gia ứng dụng cá cược, tài xỉu và hứa bao thắng",
        "lập hội nhóm hứa lấy lại tiền đã bị lừa để lừa thêm lần nữa",
        "mua bán thuê bao điện thoại, tài khoản mạng xã hội đứng tên học sinh",
    ],
    "bn_de_doa": ["nhắn tin đe doạ đánh, hẹn gặp sau giờ học", "doạ nạt khiến bạn không dám báo thầy cô"],
    "bn_phat_tan": ["đe doạ tung ảnh riêng tư, tin nhắn cá nhân lên mạng", "làm quen xin ảnh nhạy cảm rồi tống tiền",
                    "cắt ghép ảnh của bạn để chế giễu"],
    "bn_tran_lot": ["ép bạn đưa tiền, đồ dùng nếu không sẽ bị đánh"],
    "bn_lang_ma": ["chế giễu ngoại hình, gọi bạn bằng biệt danh xúc phạm trên nhóm chat", "để lại bình luận ác ý, lăng mạ dưới bài đăng của bạn"],
    "bn_co_lap": ["lập nhóm chat riêng để tẩy chay, cô lập một bạn", "kêu gọi cả lớp không nói chuyện với một bạn"],
    "bn_tin_don": ["tung tin đồn thất thiệt, bóc phốt bạn trên trang confession", "lan truyền địa chỉ nhà, thông tin cá nhân của bạn"],
    "bn_khac": ["kêu gọi nhiều người cùng vào chửi bới, báo cáo tài khoản của một bạn", "mạo danh tài khoản của bạn để đăng nội dung xấu"],
}
LD_KEYS = [k for k in THU_DOAN if k.startswith("ld_")]
BN_KEYS = [k for k in THU_DOAN if k.startswith("bn_")]
KHUYEN_LD = ["giữ kín mã OTP và mật khẩu", "xác minh kỹ trước khi chuyển bất kỳ khoản tiền nào",
             "liên lạc trực tiếp với người thân để hỏi lại", "bỏ qua các đường link không rõ nguồn gốc", "kể ngay với bố mẹ, thầy cô",
             "đến cơ quan công an gần nhất để trình báo", "chỉ đóng tiền qua tài khoản mang tên nhà trường",
             "ngắt cuộc gọi và báo 113 khi bị uy hiếp", "không đứng tên mở tài khoản hộ người khác",
             "tra cứu lại trên trang chính thức", "không cài phần mềm theo lời người lạ",
             "bình tĩnh hỏi ý kiến người lớn", "không giữ bí mật với gia đình khi bị yêu cầu"]
KHUYEN_BN = ["không đáp trả khi đang tức giận", "chụp màn hình lưu bằng chứng", "chặn và báo cáo tài khoản đó",
             "kể với thầy cô, cha mẹ hoặc gọi 111", "không chia sẻ tiếp ảnh, clip đó", "lên tiếng bảo vệ bạn bị bắt nạt",
             "đến phòng tư vấn tâm lý của trường", "nhắn tin hỏi thăm bạn bị bắt nạt"]
HV = ["chế giễu ngoại hình của bạn", "lập nhóm chat để nói xấu bạn", "đăng ảnh xấu của bạn lên mạng", "bình luận ác ý dưới bài đăng",
      "đe doạ đánh bạn sau giờ học", "tung tin đồn về bạn", "gọi bạn bằng biệt danh xúc phạm", "tẩy chay một bạn trong lớp",
      "quay clip bạn bị đánh rồi đăng lên mạng", "ép bạn đưa tiền"]
HV_BI = ["chế giễu ngoại hình", "nói xấu trong nhóm chat", "đăng ảnh dìm", "bình luận ác ý", "đe doạ trên mạng", "tung tin đồn",
         "tẩy chay", "doạ tung ảnh riêng tư", "ép đưa tiền"]
DAU_HIEU = ["giục gấp và đòi chuyển tiền", "xin mã OTP", "đường link lạ", "yêu cầu giữ bí mật với gia đình",
            "hứa lợi nhuận quá cao", "tự xưng cơ quan chức năng làm việc qua mạng", "đòi phí trước khi nhận quà"]
DAU_HIEU_BN = ["tắt màn hình vội khi có người đến gần", "mất ngủ, ăn uống thất thường", "đột nhiên xoá tài khoản mạng xã hội",
               "thu mình, ít trò chuyện với gia đình"]
LOAI_CHIEU = ["lừa đảo giả danh công an", "lừa đảo việc nhẹ lương cao", "lừa đảo chiếm mã OTP", "bắt cóc online",
              "lừa đảo trúng thưởng", "mạo danh giáo viên xin tiền", "bắt nạt trên mạng", "tống tiền bằng ảnh nhạy cảm",
              "lừa đảo học bổng du học", "cho thuê tài khoản ngân hàng"]
CHU_DE = ["phòng chống lừa đảo trực tuyến", "phòng chống bắt nạt trên mạng", "an toàn trên không gian mạng",
          "nhận diện thủ đoạn giả danh công an", "phòng chống bạo lực học đường", "bảo vệ thông tin cá nhân", "ứng xử văn minh trên mạng xã hội"]
TO_CHUC = ["Công an", "Ngân hàng", "Nhà trường", "Nhà mạng", "Toà án", "Bộ GD&ĐT", "Cổng dịch vụ công"]
YEU_CAU = ["yêu cầu chuyển tiền qua tài khoản cá nhân", "xin mã OTP qua điện thoại", "làm việc với người dân qua Zalo, Facebook",
           "gửi đường link yêu cầu đăng nhập", "bắt giữ bí mật với gia đình", "thu phí để nhận quà"]
KENH_CHINH_THUC = ["thu tiền qua tài khoản có tên trường", "liên hệ qua số tổng đài in trên thẻ", "gửi giấy mời trực tiếp",
                   "thông báo trên trang thông tin chính thức"]
HIEN_TUONG = ["học sinh quay clip bạn bị đánh rồi đăng lên mạng", "bình luận ác ý trên mạng xã hội", "học sinh bị lừa vì tin việc nhẹ lương cao",
              "lập nhóm chat để tẩy chay bạn", "giới trẻ chia sẻ thông tin cá nhân lên mạng"]
LO_LAM = ["chuyển tiền cho kẻ gian", "đọc mã OTP cho người lạ", "bấm vào link giả", "gửi ảnh riêng tư cho người lạ", "cài ứng dụng lạ"]
SAU_KHI = ["gọi ngay tổng đài ngân hàng để khoá tài khoản", "báo bố mẹ và đến công an gần nhất trình báo",
           "đổi mật khẩu và đăng xuất khỏi mọi thiết bị", "kể với người lớn tin cậy và gọi 111", "lưu lại toàn bộ tin nhắn làm bằng chứng"]
KHAU_HIEU = ["Trường học hạnh phúc, không có chỗ cho bạo lực", "Kiểm tra kỹ, không lo mất tiền", "Thấy bạn bị bắt nạt, hãy lên tiếng",
             "Giữ kín mã OTP như giữ chìa khoá nhà", "Không một mình, cùng nhau an toàn trên mạng", "Bấm chậm lại, nghĩ kỹ hơn",
             "Mỗi bình luận tử tế là một liều thuốc cho bạn bè", "Không chia sẻ, không lan truyền clip bạo lực",
             "Không tin lời lạ, không bấm link lạ, không gửi mã OTP", "Lên tiếng đúng lúc, bảo vệ bạn bè"]
TU_CHOI = ["Cảm ơn", "Cảm ơn nhiều", "Thanks", "Cảm ơn ad"]

# --- KHUNG CÂU TUYÊN TRUYỀN (mỗi khung là một template_id riêng) ---
TT = [
    ("tt01", "ld", "{nguon} {dong_tu} thủ đoạn {td}, đề nghị {nan} {khuyen}."),
    ("tt02", "ld", "{nguon} khuyến cáo {nan}: {khuyen}, {khuyen2}."),
    ("tt03", "ld", "Thời gian qua xuất hiện tình trạng đối tượng {td}. {nguon} đề nghị {nan} {khuyen}."),
    ("tt04", "ld", "Cảnh giác: các đối tượng đang {td} {kenh}. Hãy {khuyen}."),
    ("tt05", "ld", "Theo {nguon}, kẻ gian thường {td}; khi gặp trường hợp này cần {khuyen}."),
    ("tt06", "ld", "Nhận diện lừa đảo: {td}. Nếu gặp, hãy {khuyen} và {khuyen2}."),
    ("tt07", "x", "Xin nhắc lại: {to_chuc} không {yeu_cau}, ai làm vậy là mạo danh."),
    ("tt08", "ld", "Thông tin cảnh báo từ {nguon}: đối tượng {td}, nhiều {nan} đã bị chiếm đoạt tài sản."),
    ("tt09", "ld", "[CẢNH BÁO] Thủ đoạn {td}. {nguon} lưu ý {nan} {khuyen}."),
    ("tt10", "ld", "Để phòng tránh thủ đoạn {td}, {nan} cần {khuyen}, đồng thời {khuyen2}."),
    ("tt11", "ld", "Nhà trường thông báo: gần đây có đối tượng {td}, các em {khuyen}."),
    ("tt12", "ld", "Thầy dặn: thấy ai {td} thì báo ngay cho giáo viên, đừng tự xử lý một mình."),
    ("tt13", "x", "Kế hoạch sinh hoạt chủ nhiệm tháng này: lồng ghép nội dung về {chu_de}."),
    ("tt14", "x", "Mời các lớp đăng ký hội thi tìm hiểu {chu_de} do Đoàn trường tổ chức, hạn nộp {gio} thứ sáu."),
    ("tt15", "ld", "Kính gửi quý phụ huynh: gần đây có tình trạng đối tượng {td}, mong gia đình nhắc các con {khuyen}."),
    ("tt16", "x", "Ban giám hiệu lưu ý: mọi khoản thu đều có thông báo bằng văn bản, phụ huynh không chuyển tiền theo tin nhắn riêng."),
    ("tt17", "ld", "Tại {dia}, {nan_1} mất {tien} vì tin lời đối tượng {td}."),
    ("tt18", "ld", "Lực lượng chức năng ở {dia} bắt giữ nhóm đối tượng chuyên {td}."),
    ("tt19", "bn", "Một trường ở {dia} đã tổ chức hoà giải sau khi học sinh bị bạn {hv_ngan}."),
    ("tt20", "bn", "Vụ việc học sinh bị {hv_bi} ở {dia} khiến nhiều phụ huynh lo lắng."),
    ("tt21", "ld", "Tuần trước {ai} gặp đúng chiêu đối tượng {td}, may mà {an_toan}."),
    ("tt22", "ld", "Kinh nghiệm của mình: có lần bị kẻ xấu {td}, từ đó mình luôn {khuyen}."),
    ("tt23", "bn", "{ai_hoa} kể từng bị {hv_bi}, nhờ thầy cô giúp nên đã vượt qua."),
    ("tt24", "ld", "Báo động cho cả nhóm: đang có người {td}, ai gặp thì {khuyen}."),
    ("tt25", "ld", "Nhờ các bạn về kể lại cho gia đình: hiện có kẻ {td}."),
    ("tt26", "qld", "Gặp tin “{core}” thì xác định đó là lừa đảo, {khuyen}."),
    ("tt27", "qld", "Phân tích tin “{core}”: có {dau_hieu} nên đây là lừa đảo."),
    ("tt28", "qld", "Đây là mẫu câu kẻ xấu hay dùng: “{core}”. Lời khuyên: {khuyen}."),
    ("tt29", "qld", "Chị mình nhận được “{core}” {kenh}, nhờ đọc bài cảnh báo nên chị đã không làm theo."),
    ("tt30", "qld", "Tin nhắn dạng \"{core}\" đang lan truyền, mọi người cẩn trọng."),
    ("tt31", "qbn", "Theo tài liệu tập huấn, “{core}” được xếp vào hành vi bắt nạt trực tuyến; hướng xử lý là {khuyen_bn}."),
    ("tt32", "qbn", "Trong buổi tập huấn, cô đưa ví dụ “{core}” và cả lớp thống nhất cần {khuyen_bn}."),
    ("tt33", "qbn", "Đừng bao giờ nói với bạn mình những câu như “{core}”, đó là bắt nạt."),
    ("tt34", "qbn", "Ảnh chụp tin nhắn “{core}” đã được chuyển cho thầy cô để xử lý."),
    ("tt35", "qld", "Cô chiếu lên màn hình câu “{core}” để cả lớp tìm dấu hiệu {dau_hieu}."),
    ("tt36", "bn", "Một số biểu hiện của bắt nạt qua mạng: {hv}, {hv2}."),
    ("tt37", "bn", "Việc {hv} là một dạng bắt nạt trực tuyến, nếu gặp hãy {khuyen_bn}."),
    ("tt38", "bn", "Là người chứng kiến bạn bị {hv_bi}, việc nên làm là {khuyen_bn}."),
    ("tt39", "bn", "Cha mẹ nên để ý nếu con {dau_hieu_bn}, đó có thể là dấu hiệu bị bắt nạt qua mạng."),
    ("tt40", "bn", "Ranh giới giữa vui đùa và bắt nạt rất mỏng: {hv} nhiều lần là đã làm tổn thương người khác."),
    ("tt41", "bn", "Gửi bạn đang bị {hv_bi}: lỗi không nằm ở bạn, hãy tìm một người lớn để chia sẻ."),
    ("tt42", "bn", "Tớ phản đối chuyện {hv}, nhóm mình không nên như vậy."),
    ("tt43", "bn", "Bạn nào bị {hv_bi} cần người đi cùng lên phòng tư vấn thì gọi tớ."),
    ("tt44", "bn", "Thôi đủ rồi mọi người, {hv} chẳng vui chút nào."),
    ("tt45", "x", "Nhà em cũng từng gặp chiêu {loai_chieu}, may có bài cảnh báo của {nguon}."),
    ("tt46", "x", "Lưu bài này lại, {loai_chieu} đang nhắm vào {nan}."),
    ("tt47", "x", "Đã chuyển bài cho nhóm gia đình, mong không ai dính {loai_chieu}."),
    ("tt48", "x", "Ai có con em đang đi học thì đọc kỹ để phòng {loai_chieu}."),
    ("tt49", "x", "{khau_hieu}!"),
    ("tt50", "x", "{to_chuc} chỉ {kenh_chinh_thuc}; những yêu cầu khác đều cần kiểm tra lại."),
    ("tt51", "x", "Nhóm em làm dự án về {chu_de}, giúp các bạn biết cách tự bảo vệ mình."),
    ("tt52", "x", "Bài tập nhóm môn GDCD: tìm hiểu nguyên nhân và hậu quả của {hien_tuong}."),
    ("tt53", "x", "Áp phích ở bảng tin trường liệt kê dấu hiệu của {loai_chieu}, ví dụ {dau_hieu}."),
    ("tt54", "bn", "Hỏi đáp: Nếu bị {hv_bi} thì làm gì? Trả lời: {khuyen_bn}."),
    ("tt55", "ld", "Hỏi: Có người {td} thì phải làm sao? Đáp: {khuyen}."),
    ("tt56", "x", "Trường hợp đã {lo_lam} thì việc đầu tiên là {sau_khi}."),
    ("tt57", "x", "Thủ quỹ lớp thông báo: quỹ lớp tháng này thu trực tiếp tại lớp, không nhận chuyển khoản qua tài khoản nào khác."),
    ("tt58", "ld", "Phóng sự của {nguon} kể lại chuỗi thủ đoạn: đối tượng {td}."),
    ("tt59", "x", "Podcast an toàn số kỳ này nói về {loai_chieu}."),
    ("tt60", "ld", "Phụ huynh lưu ý: đối tượng {td}, hãy dặn con {khuyen}."),
    ("tt61", "ld", "Thủ đoạn cũ nhưng nhiều người vẫn mắc: {td}. Nhớ {khuyen} nhé."),
    ("tt62", "bn", "Chi đoàn phát động phong trào nói lời tử tế, không {hv} trên mạng."),
    ("tt63", "ld", "Tài liệu tuyên truyền của {nguon} nêu rõ: đối tượng {td}, vì vậy {nan} cần {khuyen}."),
    ("tt64", "qld", "Cảnh giác với những tin nhắn như “{core}”, đó là cách kẻ xấu {td}."),
    ("tt65", "qbn", "Bình luận “{core}” dưới bài đăng của bạn ấy đã bị báo cáo, mọi người đừng hùa theo nhé."),
    ("tt66", "bn", "Nhìn lại, mình thấy có lỗi vì đã đứng xem khi bạn bị {hv_bi} mà không giúp."),
]

# --- TIN BÌNH THƯỜNG CÓ TỪ DỄ NHẦM ---
GAME = ["Liên Quân", "Free Fire", "PUBG", "Minecraft", "Valorant", "Roblox", "Liên Minh"]
APP = ["Zalo", "Facebook", "Gmail", "app ngân hàng của mẹ", "app học tiếng Anh", "Messenger", "tài khoản game"]
DUA = ["haha", "đùa thôi", "trêu tí thôi", "mai bao trà sữa nhé", "hihi", "kkk", "yêu mày", "nói vui thôi mà"]
BT = [
    ("bk01", "{game} tối nay ai on, thiếu một slot, đứa nào afk là tao đá ra"),
    ("bk02", "phó bản mới khó kinh khủng, tao gục {so} lần mới qua"),
    ("bk03", "gánh team mệt quá, mấy đứa kia gà vãi {dua}"),
    ("bk04", "nạp {tien} mua skin {game} bằng tiền tiết kiệm của tao, đẹp không"),
    ("bk05", "hôm nay đánh cờ vua tao đi sai nước ngớ ngẩn, đúng là đầu đất"),
    ("bk06", "ván sau tao bắn hạ hết team bên kia cho xem"),
    ("bk07", "tao đãng trí thật, lại để quên áo khoác ở phòng thí nghiệm"),
    ("bk08", "mình ngốc quá, làm mất chìa khoá xe lần thứ hai trong tuần"),
    ("bk09", "đồ ngốc này, đi ngược chiều mà còn cãi, {dua}"),
    ("bk10", "đồ tham ăn, ăn hết bánh của tao rồi, {dua}"),
    ("bk11", "nhìn mày ngủ gật trong lớp buồn cười vãi, {dua}"),
    ("bk12", "{app} bắt xác minh lại vì mình đăng nhập máy mới, mã gửi về số của mình rồi"),
    ("bk13", "đổi mật khẩu {app} xong rồi, lần này đặt dài hơn cho chắc"),
    ("bk14", "mẹ ơi app ngân hàng hỏi vân tay của mẹ, mẹ tự quét nhé con không bấm đâu"),
    ("bk15", "nhớ bật xác thực hai lớp cho {app} nha, an toàn hơn"),
    ("bk16", "ông ngoại cho con {tien} mừng sinh nhật, mẹ gửi vào sổ tiết kiệm cho con nhé"),
    ("bk17", "tháng này nhà mình đóng tiền nước qua app, có biên lai điện tử rồi"),
    ("bk18", "con nộp {tien} tiền bảo hiểm y tế ở phòng tài vụ, cô đưa biên lai rồi"),
    ("bk19", "săn được mã giảm giá {so}0% mua sách tham khảo, rẻ ghê"),
    ("bk20", "lớp mình đặt cọc {tien} may áo lớp ở tiệm quen gần trường rồi nhé"),
    ("bk21", "đề cương {mon} dài như sớ, ôn không kịp mất"),
    ("bk22", "thầy {mon} gọi lên bảng đúng câu tao không biết, xấu hổ ghê"),
    ("bk23", "nhóm học {mon} tối nay học ở thư viện tầng hai nhé"),
    ("bk24", "phim hôm qua về đường dây lừa đảo hay thật, diễn viên đóng đạt ghê"),
    ("bk25", "đọc truyện trinh thám về vụ án ngân hàng, cuốn thật sự"),
    ("bk26", "dỗi rồi, đi ăn kem không gọi tao, {dua}"),
    ("bk27", "tạm mute nhóm game vì tụi mày gửi sticker nhiều quá, tối mở lại"),
    ("bk28", "từ giờ không thèm nói chuyện với mày nữa, {dua}, chiều đi đá bóng nhé"),
    ("bk29", "bác gửi hàng từ quê lên, con ra cổng nhận giúp mẹ với"),
    ("bk30", "bí thư chi đoàn thu {tien} đoàn phí trực tiếp ở bàn đầu nhé"),
    ("bk31", "ai thấy chiếc bình nước màu xanh để quên ở căng tin thì nhắn mình"),
    ("bk32", "đội mình thua đậm quá, chắc bị cả trường cười mất {dua}"),
    ("bk33", "chó nhà tao gặm mất đôi dép mới mua, bực mình"),
    ("bk34", "wifi trường chập chờn, {app} cứ văng ra bắt đăng nhập lại"),
    ("bk35", "trường gửi thông báo nghỉ học ngày {so} qua sổ liên lạc điện tử"),
    ("bk36", "dạo này mày tăng cân à, áo chật rồi kìa {dua}"),
    ("bk37", "mày chuyển khoản tiền trà sữa hôm qua cho tao chưa, {tien} đấy"),
    ("bk38", "anh trai tao bảo nếu tao thi trượt thì cấm chơi game cả hè, sợ thật"),
    ("bk39", "nhà ma ở hội chợ sợ phát khóc luôn"),
    ("bk40", "giải bóng rổ khối {so}, lớp mình gặp đội mạnh nhất, ai rảnh ra cổ vũ"),
    ("bk41", "chị tao đỗ học bổng của trường đại học, cả nhà mừng lắm"),
    ("bk42", "mượn tạm máy tính cầm tay của mày tiết sau nhé"),
    ("bk43", "thi trượt vòng loại cũng không sao, năm sau làm lại"),
    ("bk44", "buổi ngoại khoá kỹ năng sống tuần này dạy sơ cứu"),
]

# --- TIN NGUY CƠ GIẢ DẠNG LỜI CẢNH BÁO, THÔNG BÁO ---
CO_QUAN = ["Bộ Công an", "Công an quận", "Viện kiểm sát", "Toà án", "Cục An toàn thông tin", "Ngân hàng", "Ban quản trị nhóm", "Nhà mạng"]
VU_AN = ["rửa tiền", "ma tuý", "lừa đảo xuyên quốc gia", "mua bán tài khoản", "đánh bạc online"]
GC = [
    ("gc01", "ld_otp", "[Thông báo bảo mật] {app} phát hiện đăng nhập lạ, nhấn {link} để khôi phục quyền truy cập trong {gio2}"),
    ("gc02", "ld_de_doa", "Cán bộ điều tra thông báo: em đứng tên một tài khoản dính đến vụ {vu_an}, tối nay phải có mặt trực tuyến và không kể với người nhà"),
    ("gc03", "ld_chuyen_tien", "Tiền trong ví của bạn đang gặp rủi ro, chuyển sang ví bảo đảm số {stk} theo hướng dẫn của bộ phận an ninh"),
    ("gc04", "ld_otp", "Nhân viên hỗ trợ: để chặn giao dịch đang chờ, bạn đọc 6 số vừa nhận qua tin nhắn cho mình nhé"),
    ("gc05", "ld_khac", "Văn phòng luật miễn phí cho nạn nhân lừa đảo, chỉ cần tạm ứng {tien} phí mở hồ sơ"),
    ("gc06", "ld_otp", "Thiết bị của bạn có virus, cài phần mềm diệt virus tại {link} rồi đăng nhập internet banking để kiểm tra"),
    ("gc07", "ld_thong_tin", "Đội phản ứng nhanh chống lừa đảo cần bạn gửi ảnh hai mặt căn cước cùng mật khẩu ứng dụng để bảo vệ"),
    ("gc08", "ld_chuyen_tien", "Phòng tài vụ báo gấp: em chưa đóng tiền thì chuyển ngay vào số {stk} đứng tên cô phụ trách, quá {gio} sẽ bị gạch tên"),
    ("gc09", "ld_de_doa", "Quyết định xử phạt: em đăng bài vi phạm, nộp {tien} vào tài khoản {stk} để huỷ hồ sơ"),
    ("gc10", "ld_otp", "Fanpage của bạn sắp bị gỡ vì vi phạm bản quyền, kháng nghị tại {link} bằng tài khoản và mật khẩu"),
    ("gc11", "ld_trung_thuong", "Quà tri ân khách hàng chính hãng, phí vận chuyển {tien} chuyển trước vào {stk}, cảnh giác hàng giả bên ngoài"),
    ("gc12", "ld_otp", "Tổng đài an ninh mạng: chúng tôi vừa gửi mã kích hoạt bảo vệ, bạn đọc lại mã để hoàn tất"),
    ("gc13", "ld_de_doa", "{co_quan} triệu tập: em phải nghe máy gọi video lúc {gio}, ở một mình trong phòng, nếu báo ai biết sẽ bị xử lý"),
    ("gc14", "ld_otp", "Admin nhóm học tập: để duyệt thành viên, gửi mã 6 số Zalo vừa gửi cho bạn vào tin nhắn riêng"),
    ("gc15", "ld_trung_thuong", "Khảo sát nhận thức an toàn mạng có thưởng {tien}, đăng nhập Facebook tại {link} để nhận"),
    ("gc16", "ld_viec_lam", "Cảnh báo: chỉ còn {so} suất việc làm online chính chủ, nạp {tien} kích hoạt ngay kẻo bị đối tượng xấu giành mất"),
    ("gc17", "bn_tin_don", "Nói thật để mọi người cảnh giác: đứa {ten} lớp {lop} {tin_don}, đừng ai chơi với nó"),
    ("gc18", "bn_de_doa", "Chống bắt nạt gì chứ, đứa như mày bị đánh là đáng, liệu hồn"),
    ("gc19", "bn_lang_ma", "Góp ý chân thành thôi: mày {xuc_pham} thật, biến khỏi nhóm đi"),
    ("gc20", "bn_khac", "Cảnh báo cả trường: thấy thằng {ten} thì tránh xa, đăng ảnh nó lên cho mọi người biết mặt"),
    ("gc21", "bn_de_doa", "Phòng chống bạo lực gì thì phòng, đứa nào khai tên tao với giám thị thì tan học đợi đấy"),
    ("gc22", "bn_phat_tan", "Tao nói trước để mày cảnh giác: không chuyển {tien} thì ảnh của mày lên nhóm lớp tối nay"),
]


# --- TIN NGUY CƠ NHẮM THẲNG, CÓ TỪ "CHÍNH THỐNG" (xưng danh cơ quan, nhà trường) ---
DIA_DIEM = ["khách sạn gần nhà", "nhà nghỉ ở trung tâm", "một phòng trọ trống", "quán net vắng người"]
TC = [
    ("tc01", "ld_de_doa", "bên anh là cơ quan điều tra, hồ sơ của em có trong vụ {vu_an}, làm đúng hướng dẫn thì mới được xoá tên"),
    ("tc02", "ld_de_doa", "anh là cán bộ công an quận, em ra {dia_diem} ở một mình chờ lệnh, tắt định vị và không báo ai"),
    ("tc03", "ld_de_doa", "thư ký toà án thông báo em có giấy triệu tập điện tử, phải xác nhận qua cuộc gọi video ngay"),
    ("tc04", "ld_otp", "cán bộ ngân hàng đây, tài khoản của em bị đóng băng, đọc mã OTP để anh mở lại"),
    ("tc05", "ld_chuyen_tien", "anh bên phòng đào tạo, em đóng {tien} lệ phí phúc khảo vào {stk} trong hôm nay nhé"),
    ("tc06", "ld_chuyen_tien", "cô bên ban tuyển sinh đây, em chuyển {tien} giữ suất nhập học vào {stk} trước {gio}"),
    ("tc07", "ld_chuyen_tien", "chị quản lý ký túc xá, em cọc {tien} vào {stk} thì mới giữ được giường"),
    ("tc08", "ld_thong_tin", "em được miễn giảm học phí, gửi ảnh căn cước và mã OTP để cô hoàn tất hồ sơ"),
    ("tc09", "ld_viec_lam", "bên mình là đơn vị tuyển dụng chính thức, em cọc {tien} nhận đồng phục rồi đi làm luôn"),
    ("tc10", "ld_trung_thuong", "anh có suất học bổng nội bộ, em đóng {tien} là có tên trong danh sách"),
    ("tc11", "ld_otp", "nhà mạng thông báo sim của bạn sắp bị khoá, đọc mã vừa gửi cho tổng đài viên để chuẩn hoá"),
    ("tc12", "ld_de_doa", "em đang dính vào đường dây {vu_an}, muốn được xoá tên thì nhắn bố mẹ chuyển {tien} vào {stk}"),
    ("tc13", "ld_de_doa", "cán bộ đang ghi hình buổi làm việc, em không được rời khỏi phòng và không được dùng điện thoại gọi ai"),
    ("tc14", "ld_chuyen_tien", "thầy chủ nhiệm đây, con thầy đang cấp cứu, em chuyển giúp thầy {tien} vào {stk}, mai thầy trả"),
    ("tc15", "ld_khac", "em cho anh mượn tài khoản ngân hàng vài hôm để nhận tiền hàng, anh gửi em {tien} cảm ơn"),
    ("tc16", "bn_de_doa", "đứa nào mách thầy cô vụ hôm qua thì liệu mà giữ mồm"),
    ("tc17", "bn_co_lap", "nhóm mình thống nhất cho {ten} ra rìa, đứa nào rủ nó đi chơi là phản bội"),
    ("tc18", "bn_phat_tan", "lấy ảnh {ten} làm meme rồi thả vào group khối cho vui"),
    ("tc19", "bn_lang_ma", "{ten} nói chuyện nghe khó chịu, cả lớp nhại lại cho nó xấu hổ đi"),
    ("tc20", "bn_lang_ma", "nhìn cái mặt {ten} là thấy ghét, {xuc_pham} còn bày đặt"),
    ("tc21", "bn_tran_lot", "mai mang {tien} ra nhà xe nộp cho bọn anh, không thì đừng trách"),
    ("tc22", "bn_phat_tan", "tao có ảnh mày lúc ngủ gật, muốn tao xoá thì làm bài hộ tao cả tuần"),
]


def fill(tpl, rng, core=None):
    td = rng.choice(THU_DOAN[rng.choice(LD_KEYS if rng.random() < 0.7 else BN_KEYS)])
    k1, k2 = rng.sample(KHUYEN_LD, 2)
    h1, h2 = rng.sample(HV, 2)
    ai = rng.choice(AI)
    return tpl.format(
        nguon=rng.choice(NGUON), dong_tu=rng.choice(DONG_TU), td=td, nan=rng.choice(NAN), nan_1=rng.choice(NAN_1),
        khuyen=k1, khuyen2=k2, khuyen_bn=rng.choice(KHUYEN_BN), dia=rng.choice(DIA), kenh=rng.choice(KENH), tien=rng.choice(TIEN),
        ai=ai, ai_hoa=ai[0].upper() + ai[1:], an_toan=rng.choice(AN_TOAN), hv=h1, hv2=h2, hv_bi=rng.choice(HV_BI),
        hv_ngan=rng.choice(["đe doạ trên mạng", "tung ảnh chế", "lăng mạ trong nhóm chat", "tẩy chay", "quay clip đánh"]),
        dau_hieu=rng.choice(DAU_HIEU), dau_hieu_bn=rng.choice(DAU_HIEU_BN), loai_chieu=rng.choice(LOAI_CHIEU), chu_de=rng.choice(CHU_DE),
        to_chuc=rng.choice(TO_CHUC), yeu_cau=rng.choice(YEU_CAU), kenh_chinh_thuc=rng.choice(KENH_CHINH_THUC),
        hien_tuong=rng.choice(HIEN_TUONG), lo_lam=rng.choice(LO_LAM), sau_khi=rng.choice(SAU_KHI), khau_hieu=rng.choice(KHAU_HIEU),
        tu_choi=rng.choice(TU_CHOI), so=rng.randint(3, 9), gio=rng.choice(GIO), core=core or "",
        game=rng.choice(GAME), app=rng.choice(APP), dua=rng.choice(DUA), mon=rng.choice(MON), ten=rng.choice(TEN), lop=rng.choice(LOP),
        link="https://" + rng.choice(SCAM_DOMAINS) + "/" + rng.choice(PATHS), stk=stk(rng), sdt=phone(rng), gio2=rng.choice(GIO2),
        co_quan=rng.choice(CO_QUAN), dia_diem=rng.choice(DIA_DIEM), vu_an=rng.choice(VU_AN), xuc_pham=rng.choice(XUC_PHAM), tin_don=rng.choice(TIN_DON),
    )


def harmful_cores():
    """Lõi tin nguy cơ để TRÍCH LẠI trong khung tuyên truyền: tách theo tập của bộ gốc để không rò rỉ."""
    out = {"train": {"lua_dao": [], "bat_nat": []}, "test": {"lua_dao": [], "bat_nat": []}}
    for fn, test_splits in (("bo_huan_luyen_10000.csv", ("test",)), ("bo_bo_sung_nguon_tin_cay.csv", ("doc_lap",))):
        p = os.path.join(ROOT, "data", fn)
        with open(p, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                if r["label"] == "binh_thuong" or r["category"] == "link_nguy_hiem" or len(r["text"]) > 130:
                    continue
                t = r["text"].strip().rstrip(".!")
                key = "test" if r["split"] in test_splits else ("train" if r["split"] == "train" else None)
                if key:
                    out[key][r["label"]].append(t)
    return out


def build(seed=SEED, per_frame=70, per_bt=30, per_gc=40):
    rng = random.Random(seed)
    # chia theo khung câu, phân tầng theo nhóm (tt / bk / gc)
    split = {}
    for group in (TT, BT, GC, TC):
        ids = [g[0] for g in group]
        rng.shuffle(ids)
        n = len(ids)
        n_test, n_val = round(n * 0.25), round(n * 0.15)
        for i, t in enumerate(ids):
            split[t] = "doc_lap" if i < n_test else ("val" if i < n_test + n_val else "train")
    cores = harmful_cores()
    seen, rows = set(), []

    def add(text, label, cat, tid, obf_ok=True):
        if obf_ok:
            text, obf = augment(text, rng)
        else:
            obf = False
        text = " ".join(text.split())
        k = canon(text)
        if k in seen:
            return False
        seen.add(k)
        rows.append({"text": text, "label": label, "category": cat, "template_id": tid, "split": split[tid],
                     "co_link": int("http" in text), "do_kho": "kho", "nguon": "ngu_canh"})
        return True

    for tid, kind, tpl in TT:
        pool = cores["test" if split[tid] == "doc_lap" else "train"]
        got = tries = 0
        while got < per_frame and tries < 2000:
            tries += 1
            core = None
            if kind.startswith("q"):
                core = rng.choice(pool["lua_dao" if kind == "qld" else "bat_nat"])
            got += add(fill(tpl, rng, core), "tuyen_truyen", "tt_" + ("lua_dao" if kind in ("ld", "qld") else "bat_nat" if kind in ("bn", "qbn") else "chung"), tid)
    for tid, tpl in BT:
        got = tries = 0
        while got < per_bt and tries < 800:
            tries += 1
            got += add(fill(tpl, rng), "binh_thuong", "bt_kho", tid)
    for tid, cat, tpl in GC + TC:
        got = tries = 0
        while got < per_gc and tries < 800:
            tries += 1
            got += add(fill(tpl, rng), "lua_dao" if cat.startswith("ld") else "bat_nat", cat, tid)
    rng.shuffle(rows)
    for i, r in enumerate(rows, 1):
        r["id"] = f"N{i:05d}"
    return rows


def main():
    rows = build()
    out = os.path.join(ROOT, "data", "bo_phan_biet_ngu_canh.csv")
    cols = ["id", "text", "label", "category", "template_id", "split", "co_link", "do_kho", "nguon"]
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows({c: r[c] for c in cols} for r in rows)
    print("Tổng:", len(rows), "| khung câu:", len(TT) + len(BT) + len(GC) + len(TC))
    print("Theo nhãn:", dict(Counter(r["label"] for r in rows)))
    print("Theo tập và nhãn:", {s: dict(Counter(r["label"] for r in rows if r["split"] == s)) for s in ("train", "val", "doc_lap")})
    print("Đã ghi", out)


if __name__ == "__main__":
    main()

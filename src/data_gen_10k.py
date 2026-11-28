"""Sinh BỘ DỮ LIỆU TỔNG HỢP 10.000 mẫu tiếng Việt cho EduShield (không dùng tin nhắn thật của ai).

Mỗi mẫu = [mở đầu] + LÕI CÂU + [kết thúc], rồi biến đổi (teencode, bỏ dấu, viết thường, kéo dài chữ...).
Mỗi lõi câu có mã template_id. Chia train/val/test THEO template_id (cùng một lõi câu chỉ nằm trong một tập)
để tránh "học thuộc mẫu". Mọi tên, số điện thoại, số tài khoản, tên miền đều là GIẢ.

Chạy:  python src/data_gen_10k.py        -> data/bo_huan_luyen_10000.csv (+ data/bo_huan_luyen_10000_thongke.json)
LƯU Ý TRUNG THỰC: bộ này do người viết mẫu câu tạo ra nên vẫn hẹp hơn đời thực; điểm đo trên bộ này
không phản ánh hiệu quả trên tin nhắn thật.
"""
import csv
import re
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pii import mask_pii, strip_diacritics  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = 2026

TEN = ["An", "Bình", "Chi", "Dũng", "Giang", "Hà", "Khoa", "Linh", "Minh", "Ngọc", "Phúc", "Quân", "Trang", "Vy",
       "Nam", "Lan", "Hùng", "Mai", "Sơn", "Thảo", "Tuấn", "Yến", "Bảo", "Nhi", "Đạt", "Hạnh", "Long", "Phương", "Tú", "Uyên"]
MON = ["toán", "văn", "anh", "lý", "hoá", "sinh", "sử", "địa", "tin", "GDCD", "công nghệ"]
VAT = ["con bò", "con lợn", "cái thùng phi", "con heo", "con trâu"]
XUC_PHAM = ["vô dụng", "ngu ngốc", "đần độn", "hãm", "rác rưởi", "ăn hại", "bất tài", "phế vật"]
TIN_DON = ["hay ăn cắp vặt", "toàn nói xấu sau lưng", "bị cả lớp cũ đuổi", "bẩn lắm", "hay nói dối", "chuyên đi mách lẻo"]
QUA = ["iPhone 16", "xe máy điện", "voucher 5 triệu", "học bổng 10 triệu", "laptop", "máy tính bảng", "tai nghe xịn"]
TIEN = ["200k", "500k", "1 triệu", "2tr", "300 nghìn", "50k", "5 triệu", "150k", "700k", "3 triệu"]
LOP = ["10A1", "10A3", "11A2", "11B4", "12A1", "12C2"]
GIO = ["7h", "8h", "17h", "19h30", "20h", "6h45"]
SCAM_DOMAINS = [
    "nhanqua-hs.xyz", "trungthuong24h.top", "xacminh-taikhoan.vip", "ctv-tainha.club", "hocbong-free.site",
    "napthe-sieure.shop", "binhchon-anhdep.online", "nhiemvu-x2.cc", "vaytien-nhanh.vip", "quatang-hocsinh.top",
    "kiemtien-online.club", "dangnhap-fb-xacthuc.xyz", "giaithuong-game.shop", "tuyendung-ctv.site", "thanhtoan-ship.top",
    "hotro-tknh.vip", "chiendich0-0.vip", "uudai-sinhvien.xyz", "xemanh-lo.top", "nhanthuong-zalo.club",
]
OK_DOMAINS = ["thptmophong.edu.vn", "lms.truongmau.edu.vn", "classroom.google.com", "vnedu.vn", "olm.vn", "youtube.com",
              "drive.google.com", "docs.google.com", "meet.google.com", "tiktok.com", "sgk.edu.vn", "hoc10.vn"]
BENIGN_DOMAINS = ["vnexpress.net", "tuoitre.vn", "shopee.vn", "github.com", "dantri.com.vn", "thanhnien.vn", "canva.com", "quizlet.com", "kahoot.it",
                  "khanacademy.org", "nhaccuatui.com", "zingmp3.vn", "notion.so", "behance.net", "blog-lop10a1.site", "anhlop11b4.club", "tiki.vn", "lazada.vn"]
PATHS = ["nhan", "dk", "vote", "login", "app", "xacthuc", "quatang", "nap"]

OPEN = ["", "", "", "", "ê ", "này ", "nè ", "alo ", "{ten} ơi ", "ơi ", "nghe này, ", "mọi người ơi ", "bạn ơi "]
CLOSE_NEUTRAL = ["", "", "", "", " nha", " nhé", " đi", " ạ", "...", "!", " nhá", " luôn"]
CLOSE_URGENT = ["", "", " gấp nha", " nhanh lên", " ngay bây giờ", " trong hôm nay", " kẻo muộn", "!!", " nha!"]
CLOSE_BULLY = ["", "", " đấy", " nghe chưa", " biết chưa", " liệu hồn", "!", "!!", " haha"]


def phone(rng):  # giả: đầu số 0900000xxx
    return "0900000" + "".join(rng.choice("0123456789") for _ in range(3))


def stk(rng):  # giả: bắt đầu 9999
    return "9999" + "".join(rng.choice("0123456789") for _ in range(rng.choice([6, 8, 9])))


# ======================= LÕI CÂU THEO LOẠI =======================
# Mỗi mục: category -> (label, subtype_hint, danh sách lõi, kiểu đóng câu, mức khó)
CORES = {
    # ---------------- BÌNH THƯỜNG ----------------
    "bt_hoc_tap": ("binh_thuong", [
        "mai kiểm tra {mon} đấy, ôn chương {so} nhé", "bài {so} làm thế nào vậy, chỉ t với", "ê {ten} cho t mượn vở {mon} với",
        "t làm sai câu {so} rồi huhu", "đề {mon} năm ngoái khó thật, ôn kỹ vào", "{ten} ơi gửi t file đề cương {mon} với",
        "tối nay làm bài nhóm {mon} lúc {gio} nhé", "cô {mon} dặn mai nộp bài tập chương {so}", "ai giải thích giúp t phần {mon} hôm nay với",
        "t học mãi không vào, chỉ t cách ghi nhớ {mon} đi", "hôm nay lớp {lop} có tiết {mon} thay phòng nha", "nộp báo cáo {mon} trước thứ sáu nhé cả nhóm",
        "tài liệu ôn thi {mon} t để ở {link_ok} nha mọi người", "slide thuyết trình nhóm mình nè {link_ok}, góp ý giúp t",
        "bài kiểm tra {mon} hôm qua t được 8 điểm vui quá", "t bị điểm kém {mon} rồi, buồn quá", "mai có thi thử, mang máy tính cầm tay nha",
        "thầy giao đề cương {mon}, ai chưa có thì nói t gửi", "nhớ mang sách {mon} mai nha cả lớp", "t chưa hiểu phần {mon} hôm nay, hỏi cô thôi",
        "form đăng ký câu lạc bộ ở {link_ok}, ai tham gia thì điền nha", "đáp án đề {mon} t chụp gửi mọi người rồi đó",
    ], "neutral", False),
    "bt_ban_be": ("binh_thuong", [
        "chiều nay đá bóng không {ten} ơi", "đi trà sữa không, t khao", "phim hôm qua hay điên luôn, xem chưa", "t đói quá, xuống căng tin không",
        "cuối tuần đi xem phim không, t bao nước", "sinh nhật {ten} cuối tuần, góp mỗi đứa {tien} mua quà nha", "cảm ơn {ten} nhiều nha, hôm nay giúp t nhiều quá",
        "xin lỗi nha hôm qua t nóng tính quá", "chúc mừng {ten} được giải nhất môn {mon} nha, giỏi quá", "trận tối qua đỉnh thật, bàn thắng phút cuối luôn",
        "bài hát mới hay cực, nghe thử đi", "mưa to quá, mọi người về cẩn thận nha", "ai nhặt được hộp bút màu xanh ở lớp thì cho mình xin lại nha",
        "đội mình thua rồi, đá chán thật haha lần sau phục thù", "video này hài lắm {link_ok} xem đi rồi cười", "tối nay call nhóm lúc {gio} nha",
        "{ten} giỏi thật đấy, chỉ t cách chơi cờ với", "cuối tuần mình đi dã ngoại lớp nhé, ai đi thì báo t", "hôm nay lớp {lop} thắng trận bóng rổ rồi",
        "t mới mua cuốn truyện hay lắm, cho mượn nè", "chúc {ten} thi tốt nha, cố lên", "nhớ mang áo đồng phục thể dục mai nha cả nhà",
    ], "neutral", False),
    "bt_gia_dinh": ("binh_thuong", [
        "mẹ ơi con tan học lúc 5h, mẹ đón con nhé", "bố ơi con hết tiền ăn sáng rồi, bố cho con xin {tien} nhé", "con ăn cơm chưa, nhớ học bài rồi ngủ sớm",
        "tối nay cả nhà đi ăn ngoài nhé, con về sớm", "con nhớ mang áo mưa, hôm nay trời mưa", "mai mẹ đi họp phụ huynh lúc {gio} nhé con",
        "bà ốm nên cuối tuần mình về quê thăm bà", "con xin phép đi học nhóm ở nhà bạn {ten} đến {gio} về ạ", "anh ơi đón em ở cổng trường nhé",
        "mẹ gửi tiền ăn trưa cho con trong ví rồi đó", "con đã đến nhà bạn an toàn rồi mẹ ơi", "chủ nhật cả nhà dọn nhà nhé, con phụ mẹ",
        "con quên mang chìa khoá, ai ở nhà mở cửa giúp con", "cô ơi em xin phép nghỉ học hôm nay vì bị ốm ạ",
    ], "neutral", False),
    "bt_thong_bao_truong": ("binh_thuong", [
        "cô gửi link bài tập trên {link_ok}, các em nộp trước thứ 6", "trường thông báo nghỉ học thứ 7, xem tại {link_ok}",
        "link họp lớp tối nay {link_ok}, {gio} vào đúng giờ nhé", "lớp trưởng nhắc mai chào cờ mặc áo dài nha", "{ten} ơi cô gọi lên văn phòng nộp sổ đầu bài",
        "thầy nhắc đóng học phí qua cổng thanh toán chính thức của trường, không chuyển khoản cho cá nhân", "lịch thi học kỳ đã đăng tại {link_ok}, các em xem kỹ",
        "nhà trường thông báo hôm nay cúp điện, các lớp học buổi chiều", "kết quả học kỳ xem trên {link_ok}, đăng nhập bằng tài khoản của em nhé",
        "ngày mai sinh hoạt dưới cờ, các em tập trung lúc {gio}", "cô chủ nhiệm nhắc cả lớp mang đủ sổ liên lạc ngày mai",
        "đăng ký thi thử tại {link_ok}, hạn chót thứ năm", "trường tổ chức ngày hội đọc sách, đăng ký ở {link_ok}", "buổi tư vấn hướng nghiệp diễn ra lúc {gio} tại hội trường",
    ], "neutral", False),
    "bt_dua_gion": ("binh_thuong", [  # mẫu khó: đùa thân thiết, có từ nặng nhưng không bắt nạt
        "haha mày điên à, cười đau cả bụng", "thằng quỷ này lại quên trả sách cho tao hả haha", "ê con hâm, đi trà sữa không, t khao",
        "tao ngu quá làm sai câu {so} rồi huhu", "mày bựa vừa thôi {ten} ơi haha", "đồ ham ăn, chia t miếng bánh coi", "nhìn mày hôm nay hài như {vat} haha đùa thôi",
        "con quỷ nhỏ này, đi học muộn nữa hả haha", "t ngốc thật, quên mang bút luôn", "mày giỏi dữ vậy {ten}, ghen tị chết đi được haha",
        "thằng lười, dậy đi học thôi", "đồ mọt sách, cho t xin cách học với haha", "sao mày đẹp trai thế, khoe hoài vậy", "ê tên kia, trả t cây bút coi haha",
        "đồ tham ăn, ăn hết phần t rồi hả", "con bạn t dở người thật nhưng mà quý lắm", "ngu thật, t lại quên tắt bếp, may mà mẹ về kịp",
    ], "neutral", True),
    "bt_canh_bao_dung": ("binh_thuong", [  # mẫu khó: nhắc cảnh giác, có từ OTP/lừa đảo nhưng là lời khuyên
        "mã OTP ngân hàng không được đưa cho ai đâu nha, cô dặn rồi", "đừng bấm link lạ nhé mọi người, dạo này nhiều lừa đảo lắm",
        "cẩn thận tin nhắn mạo danh thầy cô xin chuyển tiền, gọi lại hỏi trực tiếp nhé", "không ai được chuyển khoản cho người lạ nha mọi người",
        "bài tuyên truyền hôm nay nói về lừa đảo qua mạng, ai chưa xem thì xem nhé", "nếu có người xin mật khẩu thì đừng đưa, báo ngay cho thầy cô",
        "mình vừa bị tin nhắn trúng thưởng giả, mọi người đừng bấm vào nhé", "cô dặn học sinh không chuyển tiền cho ai tự xưng là giáo viên qua tin nhắn",
        "nhớ bật xác thực hai lớp cho tài khoản nhé, đừng chia sẻ mã xác nhận", "tin nhắn kiểu 'tài khoản bị khoá, bấm link' là lừa đảo đó mọi người",
    ], "neutral", True),
    "bt_tai_chinh_hop_le": ("binh_thuong", [  # mẫu khó: chuyện tiền hợp lệ giữa bạn bè/lớp
        "lớp mình đóng quỹ lớp {tien} cho bạn thủ quỹ trước thứ 2 nhé", "tớ chuyển lại {tien} tiền trà sữa hôm qua cho cậu rồi nha, cảm ơn nhé",
        "nhóm mình góp {tien} mua quà cô nhân ngày 20/11, ai chưa góp báo t", "t chuyển khoản tiền ăn trưa cho bạn {ten} rồi nhé", "thủ quỹ báo quỹ lớp còn {tien}, cuối tháng mua giấy in",
        "mẹ chuyển tiền học thêm cho trung tâm rồi, có biên lai nè", "góp {tien} mua nước cho đội bóng nha mọi người", "{ten} ứng tiền mua đồ án nhóm {tien}, ai góp lại thì gửi bạn ấy nhé",
        "tiền xe buýt tháng này {tien}, ba mẹ đưa rồi", "nhóm mình chia tiền ăn mỗi người {tien} nha",
    ], "neutral", True),

    "bt_link_khac": ("binh_thuong", [  # link bình thường tới trang KHÔNG nằm trong danh sách tin cậy: chữ không đủ để kết luận lừa đảo
        "xem cái này đi {link_khac}", "bạn xem giúp mình nè {link_khac}", "link này hay lắm {link_khac}", "đọc thử xem {link_khac}", "tài liệu hôm trước đây {link_khac}",
        "đọc bài báo này nè {link_khac}, nói về kỳ thi sắp tới", "tớ vừa đặt hàng ở đây {link_khac}, giao nhanh lắm", "bộ câu hỏi ôn {mon} nè {link_khac}", "mình up bài tập lên {link_khac} rồi, xem giúp nha",
        "bài thuyết trình nhóm mình làm trên {link_khac}", "nghe thử bài này {link_khac} hay lắm", "bản đồ đường đến chỗ họp lớp nè {link_khac}", "ảnh chụp lớp mình hôm qua {link_khac}",
        "xem tin thể thao hôm nay {link_khac}", "kênh học {mon} này hay nè {link_khac}", "mình tìm được cuốn sách hay ở đây {link_khac}", "{link_khac}",
    ], "neutral", True),

    # ---------------- BẮT NẠT ----------------
    "bn_de_doa": ("bat_nat", [
        "tan học tao chờ mày ở cổng trường, liệu hồn", "mày mà mách cô thì đừng trách tao", "mày còn dám ngồi cạnh tao thì tao đánh cho",
        "mai tao với mấy đứa lớp bên xử mày", "mày xoá bài ngay không tao cho mày biết tay", "để tao xem mày còn dám lên mặt được bao lâu",
        "đừng để tao gặp mày một mình ở sân sau", "tao sẽ cho mày ra bã nếu mày dám khai", "cứ chờ đấy, tao không bỏ qua chuyện này đâu {ten}",
        "mày dám nói với giáo viên thì mày chết với tao", "cẩn thận cái miệng của mày, tao nhớ mặt mày rồi",
    ], "bully", False),
    "bn_phat_tan": ("bat_nat", [
        "ảnh dìm của {ten} đây, share cho cả trường cười nào", "tao sẽ đăng hết bí mật của mày lên mạng cho mày hết ngóc đầu",
        "chụp màn hình tin nhắn của nó gửi khắp nơi đi cho nó nhục", "up ảnh xấu của {ten} lên group lớp cho mọi người xem",
        "tao có clip của mày đây, không muốn cả trường xem thì liệu hồn", "đăng ảnh {ten} lên mạng kèm chú thích cho nó nhục luôn",
        "cắt ghép mặt {ten} vào ảnh hài rồi đăng lên đi", "gửi tin nhắn riêng của nó vào nhóm chung đi cho cả lớp đọc",
        "lập trang giả đăng ảnh dìm {ten} lên, đảm bảo cả trường biết", "tao chụp lại hết rồi, mai đăng lên fanpage trường cho mày nhục",
    ], "bully", False),
    "bn_tran_lot": ("bat_nat", [
        "đưa tiền ăn sáng đây không thì mai đừng đi học", "mày mang {tien} đến cho tao mai không thì khó sống đấy", "mỗi ngày nộp tao {tien} nếu muốn yên thân",
        "đưa điện thoại đây cho tao mượn, không thì biết tay", "mày không đưa tiền thì tao cho cả bọn xử mày", "mai nhớ mang bánh với {tien} cho tụi tao, không thì liệu",
        "đưa hết tiền tiêu vặt ra, không đưa là mày biết", "tuần này mày phải nộp tao {tien}, không nộp thì khỏi yên",
        "lấy đồ ăn của mày rồi đấy, mách ai thì không xong đâu", "nộp cho tao {tien} mỗi tuần, tao sẽ không động tới mày",
    ], "bully", False),
    "bn_lang_ma": ("bat_nat", [
        "mày ngu thế {ten}, học hành như {vat}", "đồ {xuc_pham}, biến khỏi lớp này đi", "thứ {xuc_pham} như mày chỉ làm xấu mặt lớp",
        "béo như {vat} mà cũng đòi mặc váy, xấu hổ thay", "mày nghĩ mày là ai hả, đồ {xuc_pham}", "nhìn mặt {ten} là thấy ghét, đừng có vào nhóm này nữa",
        "giọng {ten} quê mùa nghe buồn cười chết, nói lại cho cả lớp cười đi", "nhà nghèo mà cũng bày đặt, nhìn đôi giày rách của {ten} kìa",
        "đúng là đồ {xuc_pham}, làm gì cũng hỏng", "nhìn bộ dạng của mày kìa, xấu như {vat}", "học dốt thế này còn mặt mũi nào mà đi học hả {ten}",
        "mày tự soi gương đi, loại {xuc_pham} như mày", "đầu óc như {vat}, nói mãi cũng không hiểu",
    ], "bully", False),
    "bn_co_lap": ("bat_nat", [
        "cả lớp ơi đừng chơi với con {ten} nữa, nó {tin_don}", "kick con {ten} khỏi nhóm đi, nhìn ngứa mắt", "ai like bài của {ten} thì cũng bị tẩy chay luôn nhé",
        "tụi tao lập nhóm riêng rồi, cấm cho {ten} biết, cho nó ra rìa", "đồ mách lẻo, cả lớp sẽ không ai nói chuyện với mày nữa", "không ai ưa mày đâu, tự biết thân biết phận đi",
        "từ nay không ai được ngồi cạnh {ten}, ai ngồi là bị tẩy chay luôn", "đừng rủ {ten} đi chung, nó chỉ làm mất vui", "xoá {ten} khỏi nhóm chat đi, cả lớp đồng ý chưa",
        "ai nói chuyện với {ten} thì tao cho ra rìa luôn", "bọn mình bỏ {ten} lại, không ai thèm rủ nó nữa",
    ], "bully", False),
    "bn_tin_don": ("bat_nat", [
        "nghe nói {ten} {tin_don}, loại đấy tránh xa ra", "mọi người biết chưa, {ten} {tin_don} đó, lan truyền đi", "nghe đồn {ten} {tin_don}, đừng chơi với nó nhé",
        "loại như {ten} thì {tin_don}, ai cũng biết rồi", "có người kể {ten} {tin_don}, cả trường sắp biết hết rồi", "nghe nói nhà {ten} nợ nần, loại đấy tránh xa ra",
        "tao nghe bảo {ten} {tin_don}, chắc đúng rồi", "ai cũng bảo {ten} {tin_don}, nhưng tao thấy đúng thật",
    ], "bully", False),
    "bn_khac": ("bat_nat", [
        "mày xấu hổ chưa, cả lớp cười mày kìa", "nhìn {ten} kìa, buồn cười chết mất, quay lại đăng lên đi", "ai cũng thấy mày phiền phức, biết điều thì im đi",
        "không ai cần mày trong nhóm này đâu {ten}", "mày làm nhóm mất điểm, đừng có tham gia nữa", "thấy {ten} là phát ngán, tránh xa tụi tao ra",
        "mày chỉ giỏi làm trò cười thôi {ten}", "cả trường biết mày hèn rồi đấy", "đừng có nói chuyện với tụi tao nữa, nhìn mày là mệt",
    ], "bully", False),

    # ---------------- LỪA ĐẢO ----------------
    "ld_otp": ("lua_dao", [
        "Mình là nhân viên ngân hàng, bạn đọc giúp mã OTP vừa gửi về máy để huỷ giao dịch", "Tài khoản Zalo của bạn có đăng nhập lạ, gửi mã xác nhận cho mình để bảo vệ",
        "Em gửi cô mã xác nhận vừa nhận được nhé, cô cần kiểm tra tài khoản lớp", "Để nhận quà, bạn đọc cho mình mã OTP gồm 6 số vừa gửi", "Admin cần mã OTP của bạn để khôi phục tài khoản",
        "Bạn vừa nhận được mã xác minh, vui lòng cung cấp cho nhân viên hỗ trợ để hoàn tất", "Gửi mình mật khẩu tài khoản game để mình nâng cấp cho bạn",
        "Cho mình xin mã xác nhận vừa nhắn đến số của bạn để mình huỷ đơn hàng nhầm", "Hệ thống yêu cầu bạn gửi lại mật khẩu để xác thực tài khoản",
    ], "urgent", False),
    "ld_chuyen_tien": ("lua_dao", [
        "Cô là giáo viên chủ nhiệm đây, em chuyển gấp {tien} tiền học phí vào stk {stk} nhé", "Con ơi mẹ đang dùng số mới, chuyển cho mẹ {tien} vào stk {stk} gấp",
        "Bạn ơi mình chuyển nhầm {tien} vào tài khoản bạn, chuyển lại giúp qua stk {stk}", "Thầy đang họp, em chuyển giúp thầy {tien} vào stk {stk} nhé, lát thầy gửi lại",
        "Mình bán điện thoại giá học sinh {tien}, cọc trước 50% qua stk {stk} để giữ máy", "Anh là anh họ em đây, chuyển anh {tien} vào stk {stk} gấp có việc",
        "Cô đang họp, em chuyển gấp {tien} tiền quỹ lớp vào stk {stk} giúp cô nhé", "Nạp thẻ game giá rẻ chiết khấu 50%, chuyển khoản trước qua stk {stk}",
        "Bạn thân ơi cho mình mượn {tien} gấp, chuyển vào stk {stk} nhé, mai trả", "Em ck giúp chị {tien} vào stk {stk}, chị quên mang ví",
        "Mình mua hộ bạn đồ rồi, bạn chuyển {tien} qua stk {stk} cho mình nha",
    ], "urgent", False),
    "ld_trung_thuong": ("lua_dao", [
        "Chúc mừng bạn đã trúng thưởng {qua}! Bấm {link} để nhận trong 24h", "Bạn được chọn nhận quà tri ân, vui lòng điền thông tin tại {link}",
        "Quay thưởng {qua} cho học sinh, điền thông tin cá nhân tại {link}", "Tặng kim cương game miễn phí, nhập tài khoản và mật khẩu tại {link}",
        "Bạn là người may mắn nhận {qua} miễn phí, bấm vào {link}", "Học sinh trúng thưởng {qua}, liên hệ {sdt} để nhận quà",
        "Chương trình tri ân khách hàng: nhận {qua} miễn phí chỉ cần đăng nhập {link}", "Chúc mừng! Số điện thoại của bạn trúng {qua}, nhận tại {link}",
        "Bình chọn giúp mình cuộc thi ảnh tại {link}, đăng nhập facebook để vote nha", "Quà tặng sinh viên: {qua} miễn phí, bấm {link} ngay",
    ], "urgent", False),
    "ld_viec_lam": ("lua_dao", [
        "Tuyển CTV chốt đơn tại nhà, {tien}/ngày, không cần cọc, ib {sdt}", "Việc nhẹ lương cao cho học sinh, like video nhận {tien}, đăng ký tại {link}",
        "Nhiệm vụ đơn hàng: nạp {tien} nhận lại gấp đôi sau 10 phút, làm tại {link}", "Đầu tư {tien} nhận lãi 30% mỗi ngày, cam kết hoàn vốn, tham gia nhóm {link}",
        "Tuyển mẫu ảnh học sinh, đóng phí hồ sơ {tien}, liên hệ {sdt}", "Làm việc tại nhà không cần vốn, thu nhập {tien}/ngày, nhắn zalo {sdt}",
        "Kiếm tiền online chỉ cần điện thoại, chắc thắng mỗi ngày {tien}, vào {link}", "Vào nhóm kéo tài xỉu chắc thắng, admin hỗ trợ lấy lại vốn {link}",
        "Cộng tác viên chốt đơn, hoa hồng cao, không cần kinh nghiệm, ib {sdt}", "Cơ hội thu nhập thụ động lãi suất cao, nạp {tien} rút gấp đôi qua {link}",
    ], "urgent", False),
    "ld_de_doa": ("lua_dao", [
        "Tài khoản của bạn bị khoá, đăng nhập lại tại {link} để xác minh", "Công an thông báo bạn liên quan một vụ án, cài app tại {link} để làm việc",
        "Tài khoản ngân hàng của bạn sẽ bị khoá sau 24h nếu không xác minh tại {link}", "Phát hiện đăng nhập lạ vào tài khoản của bạn, xác minh ngay tại {link} kẻo bị khoá",
        "Bạn có bưu kiện chưa nhận, thanh toán phí ship tại {link}", "Thông báo cuối: số điện thoại của bạn bị tạm ngưng, bấm {link} để giữ số",
        "Bạn vi phạm quy định, cần xác minh danh tính ngay tại {link} trong 24h", "Tài khoản học tập của bạn sắp bị xoá, đăng nhập {link} gấp",
    ], "urgent", False),
    "ld_thong_tin": ("lua_dao", [
        "Học bổng du học toàn phần, chỉ cần gửi họ tên, số CCCD và đóng phí hồ sơ {tien}", "Bạn được chọn nhận quà tri ân, vui lòng cung cấp họ tên, số CCCD và mã OTP",
        "Để làm thủ tục vay, chụp CCCD hai mặt gửi zalo {sdt}", "Cho vay online không cần thế chấp, giải ngân 5 phút, chụp CCCD gửi zalo {sdt}",
        "Gửi mình ảnh thẻ học sinh và thông tin cá nhân để đăng ký học bổng nhé", "Cung cấp họ tên, ngày sinh, số CCCD để nhận hỗ trợ từ quỹ khuyến học",
        "Điền thông tin cá nhân và số tài khoản tại {link} để nhận tiền hỗ trợ", "Gửi ảnh CCCD của bạn để mình đăng ký giúp suất học bổng",
    ], "urgent", False),
    "ld_the_cao": ("lua_dao", [
        "Thầy đang họp, em mua giúp thầy thẻ cào {tien} rồi gửi mã số qua đây nhé", "Mua giúp chị thẻ cào {tien} gửi mã qua đây, lát chị chuyển lại",
        "Em mua thẻ cào điện thoại {tien} gửi mã số thẻ cho cô gấp nhé", "Bạn mua giúp mình thẻ cào game {tien}, gửi mã thẻ cho mình, mình trả sau",
        "Nạp thẻ cào {tien} vào link này để nhận gấp đôi: {link}", "Anh cần thẻ cào {tien} gấp, em mua rồi gửi mã số qua zalo cho anh",
    ], "urgent", False),
    "ld_khac": ("lua_dao", [
        "Bạn ơi cài giúp mình app này để nhận ưu đãi nhé: {link}", "Cho vay nặng lãi không cần giấy tờ, liên hệ {sdt}", "Mua like follow giá rẻ, thanh toán trước, ib {sdt}",
        "Bán tài khoản game giá rẻ, cọc trước giữ hàng, ib {sdt}", "Thuê tài khoản ngân hàng nhận {tien}/tháng, liên hệ {sdt}", "Bạn quan tâm gói vay sinh viên lãi 0%? Xem tại {link}",
        "Hỗ trợ lấy lại tài khoản bị hack, phí {tien}, nhắn {sdt}",
    ], "urgent", False),
    "link_nguy_hiem": ("lua_dao", [  # tin trông VÔ HẠI, chỉ có link chiến dịch -> khó với mô hình chữ
        "xem cái này đi {link}", "bạn xem giúp mình nè {link}", "link này hay lắm {link}", "ảnh của bạn nè {link}", "vào đây đi mọi người {link}", "mình thấy cái này có bạn trong đó {link}",
        "đọc thử xem {link}", "cho mình hỏi cái này là gì {link}", "video của bạn có trên này kìa {link}", "tài liệu hôm trước đây {link}", "vote giúp mình cái {link}",
        "{link}", "xem tin này đi {link}", "bạn có trong clip này không {link}", "đây là bài tập hôm nay {link}",
    ], "neutral", True),
}

TARGETS = {
    "bt_hoc_tap": 600, "bt_ban_be": 550, "bt_gia_dinh": 350, "bt_thong_bao_truong": 500, "bt_dua_gion": 700, "bt_canh_bao_dung": 300, "bt_tai_chinh_hop_le": 450, "bt_link_khac": 550,
    "bn_de_doa": 450, "bn_phat_tan": 450, "bn_tran_lot": 450, "bn_lang_ma": 450, "bn_co_lap": 450, "bn_tin_don": 400, "bn_khac": 350,
    "ld_otp": 350, "ld_chuyen_tien": 400, "ld_trung_thuong": 350, "ld_viec_lam": 350, "ld_de_doa": 300, "ld_thong_tin": 300, "ld_the_cao": 250, "ld_khac": 250, "link_nguy_hiem": 450,
}
assert sum(TARGETS.values()) == 10000, sum(TARGETS.values())

TEENCODE = [("không", "ko"), ("không", "k"), ("được", "dc"), ("được", "đc"), ("với", "vs"), ("mày", "m"), ("tao", "t"), ("rồi", "r"),
            ("biết", "bít"), ("gì", "j"), ("nhé", "nha"), ("bạn", "b"), ("mình", "mk"), ("chuyển khoản", "ck"), ("tài khoản", "tk")]


def fill(tpl, rng):
    link_dom = rng.choice(SCAM_DOMAINS)
    return tpl.format(
        ten=rng.choice(TEN), mon=rng.choice(MON), vat=rng.choice(VAT), xuc_pham=rng.choice(XUC_PHAM), tin_don=rng.choice(TIN_DON),
        qua=rng.choice(QUA), tien=rng.choice(TIEN), so=rng.randint(1, 9), lop=rng.choice(LOP), gio=rng.choice(GIO),
        sdt=phone(rng), stk=stk(rng), link="https://" + link_dom + "/" + rng.choice(PATHS), link_ok="https://" + rng.choice(OK_DOMAINS), link_khac="https://" + rng.choice(BENIGN_DOMAINS) + "/" + rng.choice(["bai-viet", "xem", "p/12", "shop", "tin-moi", ""]),
    )


def augment(text, rng):
    """Biến đổi bề mặt. Trả về (văn bản, có_viết_lệch)."""
    obf = False
    if rng.random() < 0.45:
        for a, b in rng.sample(TEENCODE, 4):
            if rng.random() < 0.6:
                text = text.replace(a, b)
    if rng.random() < 0.25:
        text = strip_diacritics(text)
    if rng.random() < 0.5:
        text = text.lower()
    if rng.random() < 0.10:  # kéo dài chữ: "nhaaa"
        for w in ("nha", "đi", "ơi", "nhé"):
            if w in text:
                text = text.replace(w, w + w[-1] * rng.randint(2, 3), 1)
                break
    if rng.random() < 0.03:  # viết lệch: tách chữ cái ở một từ khoá
        for w in ("chuyển", "chuyen", "ngu", "OTP", "otp", "tiền", "tien"):
            if w in text:
                text = text.replace(w, " ".join(w), 1)
                obf = True
                break
    if rng.random() < 0.12:
        text += rng.choice(["!!!", "...", " =))", " :v", " 😂", " 🙂"])
    return text, obf


def canon(t):
    """Khoá chống trùng: bỏ dấu, viết thường, chỉ giữ chữ-số. Hai câu chỉ khác dấu/hoa thường/dấu câu hoặc chỉ khác số/link/tên (sau khi che) bị coi là TRÙNG."""
    t = strip_diacritics(mask_pii(t)["masked"]).lower()  # giống góc nhìn của mô hình: sau khi che link/số/tên
    t = re.sub(r"(.)\1{2,}", r"\1\1", t)
    return " ".join(re.sub(r"[^a-z0-9]+", " ", t).split())


def build(seed=SEED):
    rng = random.Random(seed)
    rows, seen = [], set()
    for cat, (label, cores, style, hard) in CORES.items():
        close = {"neutral": CLOSE_NEUTRAL, "urgent": CLOSE_URGENT, "bully": CLOSE_BULLY}[style]
        need = TARGETS[cat]
        got, tries = 0, 0
        # lấy đều các lõi câu (xoay vòng) để mỗi lõi có số mẫu gần bằng nhau
        while got < need:
            tries += 1
            if tries > need * 80:
                raise RuntimeError(f"Không đủ biến thể độc nhất cho {cat}: {got}/{need}")
            ci = got % len(cores)
            op = rng.choice(OPEN).format(ten=rng.choice(TEN))
            text = fill(op + cores[ci] + rng.choice(close), rng)
            text, obf = augment(text, rng)
            text = " ".join(text.split())
            key = canon(text)
            if key in seen:
                continue
            seen.add(key)
            rows.append({"text": text, "label": label, "category": cat, "template_id": f"{cat}_{ci:02d}",
                         "co_link": int("http" in text), "chi_dau_link": int(cat == "link_nguy_hiem"), "do_kho": "kho" if (hard or obf) else "thuong", "nguon": "tong_hop"})
            got += 1
    # chia theo template_id: 70/15/15, phân tầng theo category
    by_cat = {}
    for r in rows:
        by_cat.setdefault(r["category"], set()).add(r["template_id"])
    split_of = {}
    for cat, tids in by_cat.items():
        tids = sorted(tids)
        rng.shuffle(tids)
        n = len(tids)
        n_test, n_val = max(1, round(n * 0.15)), max(1, round(n * 0.15))
        for i, t in enumerate(tids):
            split_of[t] = "test" if i < n_test else ("val" if i < n_test + n_val else "train")
    for r in rows:
        r["split"] = split_of[r["template_id"]]
    rng.shuffle(rows)
    for i, r in enumerate(rows, 1):
        r["id"] = f"S{i:05d}"
    return rows


def main():
    rows = build()
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    out = os.path.join(ROOT, "data", "bo_huan_luyen_10000.csv")
    cols = ["id", "text", "label", "category", "template_id", "split", "co_link", "chi_dau_link", "do_kho", "nguon"]
    with open(out, "w", encoding="utf-8-sig", newline="") as f:  # utf-8-sig để Excel mở đúng tiếng Việt
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows({c: r[c] for c in cols} for r in rows)
    from collections import Counter
    stats = {
        "tong": len(rows), "theo_nhan": dict(Counter(r["label"] for r in rows)), "theo_loai": dict(Counter(r["category"] for r in rows)),
        "theo_tap": dict(Counter(r["split"] for r in rows)), "so_template": len({r["template_id"] for r in rows}),
        "mau_kho": sum(r["do_kho"] == "kho" for r in rows), "mau_co_link": sum(r["co_link"] for r in rows),
        "theo_tap_va_nhan": {s: dict(Counter(r["label"] for r in rows if r["split"] == s)) for s in ("train", "val", "test")},
    }
    with open(os.path.join(ROOT, "data", "bo_huan_luyen_10000_thongke.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)
    print(json.dumps(stats, ensure_ascii=False, indent=1))
    print("Đã ghi", out)


if __name__ == "__main__":
    main()

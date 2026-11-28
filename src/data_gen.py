"""Sinh dữ liệu TỔNG HỢP tiếng Việt (không dùng tin nhắn thật của học sinh).

Mỗi mẫu câu (template) được điền chỗ trống và biến đổi (teencode, bỏ dấu, viết thường).
Tập kiểm thử dùng các MẪU CÂU KHÁC HẲN tập huấn luyện để tránh "học thuộc mẫu".
Tên người, số điện thoại, số tài khoản, tên miền đều là giả.
"""
import random

from pii import strip_diacritics

LABELS = ["binh_thuong", "bat_nat", "lua_dao"]

TEN = ["An", "Bình", "Chi", "Dũng", "Giang", "Hà", "Khoa", "Linh", "Minh", "Ngọc", "Phúc", "Quân", "Trang", "Vy"]
MON = ["toán", "văn", "anh", "lý", "hoá", "sinh", "sử", "địa", "tin"]
VAT = ["con bò", "con lợn", "cái thùng phi", "con heo"]
XUC_PHAM = ["vô dụng", "ngu ngốc", "đần độn", "hãm", "rác rưởi", "ăn hại"]
TIN_DON = ["hay ăn cắp vặt", "toàn nói xấu sau lưng", "bị cả lớp cũ đuổi", "bẩn lắm"]
QUA = ["iPhone 16", "xe máy điện", "voucher 5 triệu", "học bổng 10 triệu", "laptop"]
TIEN = ["200k", "500k", "1 triệu", "2tr", "300 nghìn", "50k", "5 triệu"]
# Tên miền giả dùng cho chiến dịch lừa đảo mô phỏng
SCAM_DOMAINS = [
    "nhanqua-hs.xyz", "trungthuong24h.top", "xacminh-taikhoan.vip", "ctv-tainha.club",
    "hocbong-free.site", "napthe-sieure.shop", "binhchon-anhdep.online", "nhiemvu-x2.cc",
]
OK_DOMAINS = ["thptmophong.edu.vn", "lms.truongmau.edu.vn", "classroom.google.com", "vnedu.vn", "olm.vn",
              "youtube.com", "drive.google.com", "docs.google.com", "meet.google.com", "tiktok.com"]


def _phone(rng):
    return "09" + "".join(rng.choice("0123456789") for _ in range(8))


def _stk(rng):
    return "".join(rng.choice("0123456789") for _ in range(rng.choice([10, 12, 13])))


TEMPLATES = {
    "bat_nat": [
        "mày ngu thế {ten}, học hành như {vat}",
        "nhìn mặt {ten} là thấy ghét, đừng có vào nhóm này nữa",
        "tan học tao chờ mày ở cổng trường, liệu hồn",
        "cả lớp ơi đừng chơi với con {ten} nữa, nó {tin_don}",
        "đồ {xuc_pham}, biến khỏi lớp này đi",
        "mày mà mách cô thì đừng trách tao",
        "ảnh dìm của {ten} đây, share cho cả trường cười nào",
        "béo như {vat} mà cũng đòi mặc váy, xấu hổ thay",
        "không ai ưa mày đâu, tự biết thân biết phận đi",
        "tao sẽ đăng hết bí mật của mày lên mạng cho mày hết ngóc đầu",
        "kick con {ten} khỏi nhóm đi, nhìn ngứa mắt",
        "nghe nói {ten} {tin_don}, loại đấy tránh xa ra",
        "mày còn dám ngồi cạnh tao thì tao đánh cho",
        "thứ {xuc_pham} như mày chỉ làm xấu mặt lớp",
        "ai like bài của {ten} thì cũng bị tẩy chay luôn nhé",
        "đưa tiền ăn sáng đây không thì mai đừng đi học",
        "giọng {ten} quê mùa nghe buồn cười chết, nói lại cho cả lớp cười đi",
        "mày nghĩ mày là ai hả, đồ {xuc_pham}",
        "tụi tao lập nhóm riêng rồi, cấm cho {ten} biết, cho nó ra rìa",
        "chụp màn hình tin nhắn của nó gửi khắp nơi đi cho nó nhục",
        "mai tao với mấy đứa lớp bên xử mày",
        "nhà nghèo mà cũng bày đặt, nhìn đôi giày rách của {ten} kìa",
        "đồ mách lẻo, cả lớp sẽ không ai nói chuyện với mày nữa",
        "mày xoá bài ngay không tao cho mày biết tay",
    ],
    "lua_dao": [
        "Chúc mừng bạn đã trúng thưởng {qua}! Bấm {link} để nhận trong 24h",
        "Tuyển CTV chốt đơn tại nhà, {tien}/ngày, không cần cọc, ib {sdt}",
        "Cô là giáo viên chủ nhiệm đây, em chuyển gấp {tien} tiền học phí vào stk {stk} nhé",
        "Tài khoản của bạn bị khoá, đăng nhập lại tại {link} để xác minh",
        "Bình chọn giúp mình cuộc thi ảnh tại {link}, đăng nhập facebook để vote nha",
        "Nạp thẻ game giá rẻ chiết khấu 50%, chuyển khoản trước qua stk {stk}",
        "Đầu tư {tien} nhận lãi 30% mỗi ngày, cam kết hoàn vốn, tham gia nhóm {link}",
        "Mình là nhân viên ngân hàng, bạn đọc giúp mã OTP vừa gửi về máy để huỷ giao dịch",
        "Học bổng du học toàn phần, chỉ cần đóng phí hồ sơ {tien} qua stk {stk}",
        "Bạn có bưu kiện chưa nhận, thanh toán phí ship tại {link}",
        "Việc nhẹ lương cao cho học sinh, like video nhận {tien}, đăng ký tại {link}",
        "Tặng kim cương game miễn phí, nhập tài khoản và mật khẩu tại {link}",
        "Con ơi mẹ đang dùng số mới, chuyển cho mẹ {tien} vào stk {stk} gấp",
        "Công an thông báo bạn liên quan một vụ án, cài app tại {link} để làm việc",
        "Cho vay online không cần thế chấp, giải ngân 5 phút, chụp CCCD gửi zalo {sdt}",
        "Mình bán điện thoại giá học sinh {tien}, cọc trước 50% qua stk {stk} để giữ máy",
        "Bạn được chọn nhận quà tri ân, vui lòng cung cấp họ tên, số CCCD và mã OTP",
        "Nhiệm vụ đơn hàng: nạp {tien} nhận lại gấp đôi sau 10 phút, làm tại {link}",
        "Thầy đang họp, em mua giúp thầy thẻ cào {tien} rồi gửi mã số qua đây nhé",
        "Tài khoản Zalo của bạn có đăng nhập lạ, gửi mã xác nhận cho mình để bảo vệ",
        "Quay thưởng {qua} cho học sinh, điền thông tin cá nhân tại {link}",
        "Tuyển mẫu ảnh học sinh, đóng phí hồ sơ {tien}, liên hệ {sdt}",
        "Vào nhóm kéo tài xỉu chắc thắng, admin hỗ trợ lấy lại vốn {link}",
        "Bạn ơi mình chuyển nhầm {tien} vào tài khoản bạn, chuyển lại giúp qua stk {stk}",
    ],
    "binh_thuong": [
        "mai kiểm tra {mon} đấy, ôn chương {so} nhé",
        "cô gửi link bài tập trên {link_ok}, các em nộp trước thứ 6",
        "ê {ten} cho t mượn vở {mon} với",
        "haha mày điên à, cười đau cả bụng",
        "chiều nay đá bóng không {ten} ơi",
        "lớp mình đóng quỹ lớp {tien} cho bạn thủ quỹ trước thứ 2 nhé",
        "chúc mừng {ten} được giải nhất môn {mon} nha, giỏi quá",
        "tao ngu quá làm sai câu {so} rồi huhu",
        "nhớ mang áo đồng phục thể dục mai nha cả nhà",
        "bài {so} làm thế nào vậy, chỉ t với",
        "trường thông báo nghỉ học thứ 7, xem tại {link_ok}",
        "thằng quỷ này lại quên trả sách cho tao hả haha",
        "mẹ ơi con tan học lúc 5h, mẹ đón con nhé",
        "tối nay call nhóm làm thuyết trình {mon} lúc 8h",
        "cảm ơn {ten} nhiều nha, hôm nay giúp t nhiều quá",
        "xin lỗi nha hôm qua t nóng tính quá",
        "sinh nhật {ten} cuối tuần, góp mỗi đứa {tien} mua quà nha",
        "mã OTP ngân hàng không được đưa cho ai đâu nha, cô dặn rồi",
        "đừng bấm link lạ nhé mọi người, dạo này nhiều lừa đảo lắm",
        "phim hôm qua hay điên luôn, xem chưa",
        "t đói quá, xuống căng tin không",
        "{ten} ơi cô gọi lên văn phòng nộp sổ đầu bài",
        "đội mình thua rồi, đá chán thật haha lần sau phục thù",
        "thầy nhắc đóng học phí qua cổng thanh toán chính thức của trường, không chuyển khoản cho cá nhân",
        "video này hài lắm {link_ok} xem đi rồi cười",
        "tài liệu ôn thi {mon} t để ở {link_ok} nha mọi người",
        "link họp lớp tối nay {link_ok}, 8h vào đúng giờ nhé",
        "form đăng ký câu lạc bộ ở {link_ok}, ai tham gia thì điền nha",
        "slide thuyết trình nhóm mình nè {link_ok}, góp ý giúp t",
        "{ten} ơi gửi t file đề cương {mon} với",
        "hôm nay cô {mon} cho về sớm, vui ghê",
        "t bị điểm kém bài {mon} rồi, buồn quá",
        "cuối tuần đi xem phim không, t bao nước",
        "mày làm bài nhóm chưa, mai nộp rồi đó",
        "ai nhặt được hộp bút màu xanh ở lớp thì cho mình xin lại nha",
        "bố ơi con hết tiền ăn sáng rồi, bố cho con xin {tien} nhé",
        "trận tối qua đỉnh thật, bàn thắng phút cuối luôn",
        "nhóm mình phân công: {ten} làm slide, t làm nội dung",
        "ê con hâm, đi trà sữa không, t khao",
        "cô ơi em xin phép nghỉ học hôm nay vì bị ốm ạ",
        "lớp trưởng nhắc mai chào cờ mặc áo dài nha",
        "bài hát mới hay cực, nghe thử đi",
        "tớ chuyển lại {tien} tiền trà sữa hôm qua cho cậu rồi nha, cảm ơn nhé",
        "{ten} giỏi thật đấy, chỉ t cách học {mon} với",
        "mưa to quá, mọi người về cẩn thận nha",
        "đề {mon} năm ngoái khó điên, ôn kỹ vào",
    ],
}

TEENCODE = [
    ("không", "ko"), ("không", "k"), ("được", "dc"), ("được", "đc"), ("với", "vs"),
    ("mày", "m"), ("tao", "t"), ("rồi", "r"), ("biết", "bít"), ("gì", "j"),
    ("nhé", "nha"), ("bạn", "b"), ("mình", "mk"), ("chuyển khoản", "ck"), ("tài khoản", "tk"),
]


def _fill(tpl, rng, scam_domains=None):
    doms = scam_domains or SCAM_DOMAINS
    return tpl.format(
        ten=rng.choice(TEN), mon=rng.choice(MON), vat=rng.choice(VAT),
        xuc_pham=rng.choice(XUC_PHAM), tin_don=rng.choice(TIN_DON), qua=rng.choice(QUA),
        tien=rng.choice(TIEN), so=rng.randint(1, 9), sdt=_phone(rng), stk=_stk(rng),
        link="https://" + rng.choice(doms) + "/" + rng.choice(["nhan", "dk", "vote", "login", "app"]),
        link_ok="https://" + rng.choice(OK_DOMAINS),
    )


def _augment(text, rng):
    if rng.random() < 0.5:
        for a, b in rng.sample(TEENCODE, 4):
            if rng.random() < 0.6:
                text = text.replace(a, b)
    r = rng.random()
    if r < 0.25:
        text = strip_diacritics(text)
    if rng.random() < 0.5:
        text = text.lower()
    if rng.random() < 0.15:
        text += rng.choice(["!!!", " nha", " nhé", "...", " =))", " :v"])
    return text


def generate(n_per_template=40, test_fraction=0.25, seed=42):
    """Trả về (train, test): danh sách dict {text, label, template_id}.
    Tách theo MẪU CÂU: mẫu câu trong test không xuất hiện trong train."""
    rng = random.Random(seed)
    train, test = [], []
    for label, tpls in TEMPLATES.items():
        idx = list(range(len(tpls)))
        rng.shuffle(idx)
        test_idx = set(idx[:max(1, round(len(tpls) * test_fraction))])
        for i, tpl in enumerate(tpls):
            seen = set()
            for _ in range(n_per_template):
                t = _augment(_fill(tpl, rng), rng)
                if t in seen:
                    continue
                seen.add(t)
                (test if i in test_idx else train).append(
                    {"text": t, "label": label, "template_id": f"{label}_{i:02d}"}
                )
    rng.shuffle(train)
    rng.shuffle(test)
    return train, test


if __name__ == "__main__":
    tr, te = generate()
    print(len(tr), "mẫu huấn luyện;", len(te), "mẫu kiểm thử")
    for r in te[:6]:
        print(r["label"], "|", r["text"])

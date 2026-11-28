"""BỘ DỮ LIỆU BỔ SUNG từ các thủ đoạn đã được CƠ QUAN CHỨC NĂNG, BÁO CHÍ CHÍNH THỐNG mô tả (v1.6).

Học sinh đọc các cảnh báo chính thức, rồi TỰ VIẾT LẠI lõi câu mô phỏng đúng thủ đoạn được mô tả
(không chép tin nhắn của người thật, không thu thập bình luận của ai). Mọi tên, số, link đều GIẢ.
Thêm nhiều mẫu dạng BÌNH LUẬN mạng xã hội (vì v1.6 quét cả bình luận, video trên mọi trang web)
và các mẫu "đối chứng khó": tin tuyên truyền chống lừa đảo, thông báo thu tiền chính thống, góp ý lịch sự.

Chia theo lõi câu: 60% huấn luyện, 15% kiểm định, 25% KIỂM TRA ĐỘC LẬP (doc_lap) - mô hình chưa từng thấy.
Chạy:  python src/data_bo_sung.py   -> data/bo_bo_sung_nguon_tin_cay.csv
"""
import csv
import os
import random
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_gen_10k import OPEN, CLOSE_NEUTRAL, CLOSE_URGENT, CLOSE_BULLY, fill, augment, canon, build as build10k  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = 2611

NGUON = {
    "CATTT24": "Cục An toàn thông tin: 24 hình thức lừa đảo trực tuyến (Cổng TTĐT tỉnh Hà Tĩnh)",
    "BCO": "Bộ Công an: cảnh báo 'bắt cóc online' nhắm vào học sinh, sinh viên (VOH, Nhân Dân, Tiền Phong, 2025)",
    "TSV": "ĐH Bách khoa Hà Nội: 6 hình thức lừa đảo tân sinh viên (Tiền Phong, 2025)",
    "BGD": "Bộ GD&ĐT: cảnh báo lôi kéo HSSV mở/cho thuê tài khoản ngân hàng, học bổng và cuộc thi giả mạo (2025)",
    "UNICEF": "UNICEF Việt Nam: Bắt nạt trực tuyến là gì; các hình thức chế giễu, miệt thị, bình luận ác ý, đe doạ, xuyên tạc hình ảnh",
    "TT02": "Thông tư 02/2025/TT-BGDĐT: định nghĩa bắt nạt trên mạng",
    "DOICHUNG": "Mẫu đối chứng do học sinh viết: tuyên truyền chống lừa đảo, thông báo chính thống, bình luận lành mạnh",
}

# category -> danh sách (mã nguồn, lõi câu)
SUPP = {
    # ======================= LỪA ĐẢO =======================
    "ld_de_doa": [
        ("BCO", "đây là cán bộ công an, em có liên quan đến một vụ án rửa tiền, tuyệt đối không được nói với bố mẹ"),
        ("BCO", "em đang bị điều tra, phải ở một mình trong phòng và bật camera để bên anh theo dõi liên tục"),
        ("BCO", "chúng tôi là viện kiểm sát, nếu em không hợp tác thì sẽ bị bắt và bị đuổi học"),
        ("BCO", "em phải thuê phòng khách sạn ở một mình để phục vụ điều tra, giữ bí mật với gia đình"),
        ("BCO", "hồ sơ của em dính tới đường dây ma tuý, làm đúng hướng dẫn nếu không muốn ngồi tù"),
        ("BCO", "nhắn bố mẹ chuyển tiền bảo lãnh vào tài khoản tạm giữ {stk} thì em mới được xoá tên"),
    ],
    "ld_chuyen_tien": [
        ("CATTT24", "con của chị đang cấp cứu ở bệnh viện, chuyển ngay {tien} tiền viện phí vào {stk}"),
        ("TSV", "phòng trọ giá rẻ sát trường, nhiều người hỏi lắm, cọc trước {tien} để giữ chỗ nha"),
        ("TSV", "mình là {ten} đây, đang kẹt quá cho mình vay {tien}, chuyển vào số tài khoản mới {stk} nhé"),
        ("CATTT24", "mẹ đây, điện thoại mẹ hỏng nên gọi số này, con chuyển {tien} cho người bán hàng giúp mẹ"),
        ("CATTT24", "mình lỡ chuyển nhầm {tien} vào tài khoản bạn, bạn chuyển lại giúp qua số {stk} nhé"),
        ("BGD", "anh có người quen trong hội đồng thi, đóng {tien} là đảm bảo nâng điểm, bao đỗ"),
        ("TSV", "phòng đào tạo thông báo nộp học phí vào tài khoản cá nhân {stk} trước {gio} hôm nay"),
    ],
    "ld_trung_thuong": [
        ("BGD", "quỹ học bổng hỗ trợ 80% học phí IELTS, đóng {tien} phí hồ sơ để giữ suất"),
        ("BCO", "em được chọn nhận học bổng du học, cần chứng minh tài chính bằng cách chuyển tiền vào {stk}"),
        ("CATTT24", "bé được chọn làm người mẫu nhí, đóng phí casting {tien} để vào vòng trong"),
        ("CATTT24", "bạn có bưu kiện quà tặng gửi từ nước ngoài, nộp {tien} phí hải quan để nhận"),
        ("BGD", "trang chính thức của bộ tổ chức cuộc thi vẽ tranh, đóng lệ phí {tien} để được chấm giải"),
    ],
    "ld_viec_lam": [
        ("CATTT24", "tuyển cộng tác viên đánh giá sản phẩm, làm nhiệm vụ nhận hoa hồng 30% mỗi đơn"),
        ("CATTT24", "làm nhiệm vụ thả tim video kiếm {tien} mỗi ngày, nạp trước để mở khoá nhiệm vụ cao"),
        ("TSV", "kinh doanh online thu nhập khủng không cần kinh nghiệm, chỉ cần mua gói khởi nghiệp"),
        ("CATTT24", "đầu tư tiền ảo lãi 30% mỗi tuần, cam kết hoàn vốn, vào nhóm kín ngay"),
        ("TSV", "nhận dạy gia sư lương cao, chuyển trước phí giới thiệu {tien} để được nhận lớp"),
    ],
    "ld_thong_tin": [
        ("CATTT24", "thuê bao của bạn sẽ bị khoá do chưa chuẩn hoá thông tin, gửi ảnh căn cước hai mặt để cập nhật"),
        ("CATTT24", "chụp căn cước và ảnh chân dung gửi mình để làm hồ sơ nhận quà nhé"),
        ("CATTT24", "ngân hàng thông báo tài khoản của bạn bất thường, điền họ tên và số thẻ tại {link}"),
        ("TSV", "cán bộ tuyển sinh đây, em gửi họ tên, ngày sinh và số căn cước để xác nhận nhập học"),
    ],
    "ld_otp": [
        ("CATTT24", "chụp màn hình mã đăng nhập telegram gửi mình để mình giúp bạn mở khoá"),
        ("TSV", "nhân viên trường đây, đọc giúp thầy mã otp vừa gửi về máy em để kích hoạt tài khoản học tập"),
        ("CATTT24", "dịch vụ lấy lại facebook bị hack, gửi mật khẩu cũ và mã xác nhận cho mình"),
    ],
    "ld_the_cao": [
        ("TSV", "bạn ơi nạp giúp mình thẻ cào {tien}, mai mình trả gấp đôi"),
        ("CATTT24", "mua thẻ game giúp anh, chụp mã thẻ gửi qua đây để anh tặng skin xịn"),
    ],
    "ld_khac": [
        ("BGD", "cho thuê tài khoản ngân hàng đứng tên bạn, mỗi tháng nhận {tien} không cần làm gì"),
        ("BGD", "mở giúp mình một tài khoản ngân hàng rồi đưa mình mật khẩu, trả công {tien}"),
        ("CATTT24", "app cá cược bóng đá uy tín, nạp lần đầu tặng 100%, tải tại {link}"),
        ("CATTT24", "dịch vụ lấy lại tiền đã bị lừa, chỉ cần đóng trước {tien} phí luật sư"),
        ("CATTT24", "cho số đánh đề chuẩn, chuyển {tien} để nhận số hôm nay"),
        ("TSV", "nhóm tu tập giúp em được giải thoát, hãy bỏ học và đóng góp {tien} cho quỹ"),
    ],
    # ======================= BẮT NẠT (nhiều dạng bình luận) =======================
    "bn_lang_ma": [
        ("UNICEF", "nhìn cái mặt như {vat} mà cũng đòi đăng ảnh"),
        ("UNICEF", "béo như vậy mà cũng mặc váy, tự nhìn lại mình đi"),
        ("UNICEF", "giọng hát như {vat} kêu, đừng đăng video nữa cho đỡ nhục"),
        ("UNICEF", "da đen nhẻm xấu xí, lên mạng làm gì cho chướng mắt"),
        ("TT02", "học dốt như {ten} thì bỏ học đi cho rồi, {xuc_pham}"),
        ("UNICEF", "đứa này {xuc_pham} nhất trường, nhìn là thấy ghét"),
    ],
    "bn_co_lap": [
        ("TT02", "cả nhóm unfollow con này đi, đừng ai tương tác với nó nữa"),
        ("TT02", "lập nhóm mới không có {ten}, đứa nào add nó vào là nghỉ chơi"),
        ("UNICEF", "từ mai cả lớp không ai ngồi cùng bàn với nó"),
        ("UNICEF", "block nó khỏi mọi nhóm, cho nó biết cảm giác một mình"),
    ],
    "bn_tin_don": [
        ("UNICEF", "bóc phốt: {ten} lớp {lop} {tin_don}, mọi người chia sẻ mạnh lên"),
        ("TT02", "ai có số điện thoại với địa chỉ nhà nó thì gửi vào nhóm, cho nó nổi"),
        ("UNICEF", "nghe đồn {ten} bị đuổi khỏi trường cũ vì ăn cắp, share cho cả trường biết"),
        ("TT02", "lập trang confession nói xấu {ten}, đăng hết chuyện riêng của nó lên"),
    ],
    "bn_phat_tan": [
        ("UNICEF", "ảnh ghép của nó tao làm xong rồi, tối nay tung lên group trường"),
        ("BCO", "gửi ảnh riêng tư cho anh đi, không thì anh gửi ảnh cũ của em cho cả lớp"),
        ("TT02", "clip nó bị đánh tao quay rồi, mai đăng tiktok cho nổi tiếng"),
        ("BCO", "nếu không nghe lời thì mấy tấm ảnh kia sẽ được gửi cho bố mẹ em"),
    ],
    "bn_de_doa": [
        ("UNICEF", "comment thêm câu nữa là tao tìm đến tận nhà mày"),
        ("TT02", "tan học ra cổng sau, tụi tao chờ, đứa nào báo thầy là no đòn"),
        ("UNICEF", "tao biết mày học lớp {lop}, liệu mà sống cho cẩn thận"),
    ],
    "bn_khac": [
        ("TT02", "anh em vào trang của nó spam chửi cho nó khoá nick luôn"),
        ("TT02", "report hội đồng tài khoản của {ten} đi mọi người, cho nó bay màu"),
        ("UNICEF", "đứa nào chơi với nó thì cũng bị cả trường ghét theo, nhớ đấy"),
    ],
    "bn_tran_lot": [
        ("TT02", "mỗi tuần nộp cho tao {tien} phí bảo kê, không thì đừng mong yên"),
        ("TT02", "mang điện thoại mới của mày ra đây cho tao mượn, không đưa thì biết tay"),
    ],
    # ======================= ĐỐI CHỨNG KHÓ (bình thường) =======================
    "bt_canh_bao_dung": [
        ("DOICHUNG", "công an cảnh báo thủ đoạn bắt cóc online, ai xưng công an đòi giữ bí mật với bố mẹ là lừa đảo đấy"),
        ("DOICHUNG", "nhà trường nhắc không nộp học phí vào tài khoản cá nhân nào, chỉ nộp qua cổng chính thức"),
        ("DOICHUNG", "mọi người cẩn thận, có tài khoản giả danh {ten} đi vay tiền, đừng chuyển gì nhé"),
        ("DOICHUNG", "đọc bài báo về lừa đảo việc nhẹ lương cao rồi, mọi người đừng tin mấy lời mời kiểu đó"),
        ("DOICHUNG", "ngân hàng không bao giờ hỏi mã otp, ai hỏi thì chặn luôn"),
        ("DOICHUNG", "bài tuyên truyền phòng chống bắt nạt trên mạng của đoàn trường hay lắm, xem ở {link_ok}"),
    ],
    "bt_tai_chinh_hop_le": [
        ("DOICHUNG", "quán cà phê gần trường tuyển nhân viên part-time, phỏng vấn trực tiếp tại quán, không thu phí"),
        ("DOICHUNG", "lớp mình góp quỹ {tien} mua quà tặng cô, nộp trực tiếp cho lớp trưởng nhé"),
        ("DOICHUNG", "nhà trường nhận học phí qua cổng thanh toán chính thức, phụ huynh xem hướng dẫn tại {link_ok}"),
        ("DOICHUNG", "t chuyển trả {ten} tiền trà sữa {tien} rồi nha"),
    ],
    "bt_ban_be": [
        ("DOICHUNG", "video hay quá, cảm ơn bạn đã chia sẻ"),
        ("DOICHUNG", "bạn hát hay ghê, lần sau đăng thêm nha"),
        ("DOICHUNG", "góp ý nhẹ là video hơi dài, âm thanh nhỏ, còn lại ổn"),
        ("DOICHUNG", "bài này mình không đồng ý lắm nhưng tôn trọng ý kiến của bạn"),
        ("DOICHUNG", "ảnh đẹp quá, chụp ở đâu vậy {ten}"),
        ("DOICHUNG", "chúc mừng đội tuyển {mon} của trường nha, tự hào ghê"),
    ],
    "bt_dua_gion": [
        ("DOICHUNG", "gà quá {ten} ơi, ván sau gánh tao nha haha"),
        ("DOICHUNG", "đùa thôi chứ mày là bạn thân nhất của t đó"),
        ("DOICHUNG", "nhìn hai đứa mình trong ảnh như {vat} haha, đáng yêu phết"),
    ],
    "bt_link_khac": [
        ("DOICHUNG", "xem phóng sự về an toàn trên mạng ở {link_khac}, hay phết"),
        ("DOICHUNG", "review sách hay nè mọi người {link_khac}"),
    ],
    "bt_thong_bao_truong": [
        ("DOICHUNG", "đoàn trường tổ chức buổi ngoại khoá phòng chống lừa đảo trực tuyến lúc {gio} thứ bảy"),
        ("DOICHUNG", "phòng tư vấn tâm lý của trường mở cửa mỗi chiều, bạn nào cần thì cứ đến nhé"),
        ("DOICHUNG", "giáo viên chủ nhiệm nhắc: mọi khoản thu đều có thông báo bằng văn bản của nhà trường"),
    ],
}
LABEL = {"bt": "binh_thuong", "bn": "bat_nat", "ld": "lua_dao"}
PER_CORE = 30


def build(seed=SEED):
    rng = random.Random(seed)
    seen = {canon(r["text"]) for r in build10k()}  # không trùng với bộ 10.000 cũ
    rows = []
    for cat, cores in SUPP.items():
        label = LABEL[cat[:2]]
        close = CLOSE_URGENT if label == "lua_dao" else (CLOSE_BULLY if label == "bat_nat" else CLOSE_NEUTRAL)
        for ci, (src, core) in enumerate(cores):
            got = tries = 0
            while got < PER_CORE and tries < 600:
                tries += 1
                op = rng.choice(OPEN).format(ten=rng.choice(["An", "Bình", "Chi", "Khoa", "Linh", "Minh"]))
                text, obf = augment(fill(op + core + rng.choice(close), rng), rng)
                text = " ".join(text.split())
                k = canon(text)
                if k in seen:
                    continue
                seen.add(k)
                rows.append({"text": text, "label": label, "category": cat, "template_id": f"bs_{cat}_{ci:02d}",
                             "co_link": int("http" in text), "do_kho": "kho" if (cat.startswith("bt_") or obf) else "thuong",
                             "nguon": "bo_sung", "nguon_tham_khao": src})
                got += 1
    # chia theo lõi câu, phân tầng theo loại: 25% kiểm tra độc lập, 15% kiểm định, còn lại huấn luyện
    split = {}
    for cat in SUPP:
        tids = sorted({r["template_id"] for r in rows if r["category"] == cat})
        rng.shuffle(tids)
        n = len(tids)
        n_test = max(1, round(n * 0.25))
        n_val = 1 if n >= 4 else 0
        for i, t in enumerate(tids):
            split[t] = "doc_lap" if i < n_test else ("val" if i < n_test + n_val else "train")
    for r in rows:
        r["split"] = split[r["template_id"]]
    rng.shuffle(rows)
    for i, r in enumerate(rows, 1):
        r["id"] = f"B{i:05d}"
    return rows


def main():
    rows = build()
    out = os.path.join(ROOT, "data", "bo_bo_sung_nguon_tin_cay.csv")
    cols = ["id", "text", "label", "category", "template_id", "split", "co_link", "do_kho", "nguon", "nguon_tham_khao"]
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows({c: r[c] for c in cols} for r in rows)
    with open(os.path.join(ROOT, "data", "nguon_tham_khao_bo_sung.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ma", "nguon", "so_loi_cau", "so_mau"])
        nc = Counter(src for cores in SUPP.values() for src, _ in cores)
        nm = Counter(r["nguon_tham_khao"] for r in rows)
        for k, v in NGUON.items():
            w.writerow([k, v, nc[k], nm[k]])
    print("Tổng:", len(rows), "| lõi câu:", sum(len(v) for v in SUPP.values()))
    print("Theo nhãn:", dict(Counter(r["label"] for r in rows)))
    print("Theo tập:", dict(Counter(r["split"] for r in rows)))
    print("Theo tập và nhãn:", {s: dict(Counter(r["label"] for r in rows if r["split"] == s)) for s in ("train", "val", "doc_lap")})
    print("Đã ghi", out)


if __name__ == "__main__":
    main()

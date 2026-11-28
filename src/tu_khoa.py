"""Bộ từ / cụm từ đáng chú ý theo từng nhóm nguy cơ, do học sinh tự soạn.
Dùng để CHỈ RA cụm từ đáng ngờ trong cảnh báo (giải thích), không dùng làm bộ lọc duy nhất:
thí nghiệm tn7 cho thấy chỉ dựa vào cụm từ thì bỏ sót nhiều tin nguy cơ.
"""
# Cụm từ do học sinh tự soạn từ hiểu biết về các chiêu lừa đảo, bắt nạt phổ biến (viết có dấu; máy tự bỏ dấu)
SEED = {
    "ld_otp": ["mã OTP", "OTP", "mã xác nhận", "mã xác minh", "mật khẩu", "gửi mã", "đọc mã", "mã 6 số", "mã đăng nhập", "lấy lại facebook"],
    "ld_chuyen_tien": ["chuyển khoản", "chuyển gấp", "số tài khoản", "stk", "đặt cọc", "cọc trước", "đóng phí", "phí xử lý", "chuyển nhầm", "nâng điểm", "bao đỗ", "giữ chỗ"],
    "ld_trung_thuong": ["trúng thưởng", "quà tri ân", "nhận quà", "quay thưởng", "miễn phí", "kim cương", "học bổng", "phí hồ sơ", "phí hải quan", "casting"],
    "ld_viec_lam": ["việc nhẹ lương cao", "lương cao", "cộng tác viên", "ctv", "làm tại nhà", "lãi suất", "gấp đôi", "nhiệm vụ", "thu nhập khủng", "không cần kinh nghiệm", "hoa hồng", "tiền ảo"],
    "ld_de_doa": ["bị khoá", "khoá tài khoản", "công an", "vụ án", "trong 24h", "xác minh ngay", "giữ bí mật với bố mẹ", "phục vụ điều tra", "viện kiểm sát", "thuê phòng khách sạn", "bảo lãnh"],
    "ld_thong_tin": ["cccd", "căn cước", "thông tin cá nhân", "ngày sinh", "họ tên"],
    "ld_the_cao": ["thẻ cào", "mua thẻ", "nạp thẻ", "mã thẻ"],
    "link_nguy_hiem": ["bấm vào link", "đăng nhập tại", "nhận ngay tại"],
    "bn_de_doa": ["biết tay", "đừng trách", "liệu hồn", "đánh cho", "xử mày", "chờ ở cổng"],
    "bn_phat_tan": ["tung ảnh", "đăng lên mạng", "ảnh dìm", "chụp màn hình", "bí mật của", "ảnh ghép", "ảnh riêng tư", "đăng tiktok"],
    "bn_tran_lot": ["đưa tiền", "nộp tiền", "không thì mai"],
    "bn_lang_ma": ["đồ ngu", "vô dụng", "đần độn", "rác rưởi", "ăn hại", "xấu hổ", "béo như", "chướng mắt", "cho đỡ nhục"],
    "bn_co_lap": ["tẩy chay", "đừng chơi với", "ra rìa", "không ai ưa", "biến khỏi", "kick", "unfollow", "block nó", "nghỉ chơi"],
    "ld_khac": ["cho thuê tài khoản", "mở tài khoản ngân hàng", "cá cược", "đánh đề", "lấy lại tiền"],
    "bn_khac": ["spam chửi", "report hội đồng", "bay màu"],
    "bn_tin_don": ["nghe nói", "loại đấy", "đồn là", "bóc phốt", "confession", "địa chỉ nhà"],
}

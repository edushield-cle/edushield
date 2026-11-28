# Thẻ dữ liệu: bo_huan_luyen_10000.csv

**Mục đích:** huấn luyện và đánh giá bộ phân loại bắt nạt/lừa đảo của EduShield AI. Dùng cho nghiên cứu, không dùng để giám sát người thật.

**Nguồn:** hoàn toàn TỔNG HỢP, sinh bằng `src/data_gen_10k.py` (hạt ngẫu nhiên 2026). Không chứa tin nhắn thật của ai.
Tên người, số điện thoại (dạng 0900000xxx), số tài khoản (bắt đầu 9999), tên miền lừa đảo đều là GIẢ. Một số tên miền giả có thể trùng tên miền có thật: đừng truy cập.

**Cột:** `id`, `text`, `label` (binh_thuong / bat_nat / lua_dao), `category` (24 loại chi tiết: 7 bình thường, 7 bắt nạt, 9 lừa đảo), `template_id` (lõi câu gốc, 282 lõi), `split` (train/val/test, chia THEO template_id), `co_link`, `do_kho` (mẫu khó: đùa giỡn, lời cảnh báo, tiền hợp lệ, link vô hại, viết lệch), `nguon`.

**Phân bố:** 10.000 mẫu = 4.000 bình thường + 3.000 bắt nạt + 3.000 lừa đảo. Train 6.768 / val 1.616 / test 1.616.

**Chống trùng:** không có hai mẫu giống nhau sau khi bỏ dấu, hạ chữ hoa, rút ký tự lặp và che link/số/tên. Không có template nào nằm ở hai tập khác nhau.

**Nội dung nhạy cảm:** có lời lẽ miệt thị, đe doạ mức nhẹ đến vừa để huấn luyện phát hiện. Đã loại bỏ nội dung tình dục, khuyến khích tự làm hại bản thân, kỳ thị chủng tộc/tôn giáo/khuyết tật. Nếu muốn thêm các loại này, cần chuyên gia tâm lý/đạo đức tham gia.

**Hạn chế (đọc kỹ):**
1. 282 lõi câu do một người viết, nhiều biến thể chỉ khác từ đệm và số/tên: vẫn hẹp hơn nhiều so với tin nhắn thật. Điểm đo trên bộ này không phản ánh hiệu quả ngoài đời.
2. Có thể thiên lệch theo cách viết của người soạn (giọng miền, tiếng lóng, độ dài).
3. Nhãn do người viết gán theo ý định khi soạn; chưa có nhiều người gán nhãn độc lập (chưa đo độ đồng thuận).
4. Chỉ là tin ngắn một lượt, không có hội thoại nhiều lượt, không có ngữ cảnh quan hệ giữa hai người.
5. Mẫu `bt_dua_gion` (đùa thân thiết) và `link_nguy_hiem` (tin vô hại kèm link) được thêm để bộc lộ điểm yếu: mô hình hiện báo nhầm nhiều ở nhóm đùa giỡn.

## Bộ cụm từ theo nhãn (`bo_tu_khoa.csv`)
- Gồm cụm từ 1–3 từ rút tự động từ tập huấn luyện (độ chính xác ≥ 90%, xuất hiện ≥ 6 lần) và cụm từ do học sinh tự soạn (`src/tu_khoa.py`).
- Thí nghiệm tn7 cho thấy chỉ dùng cụm từ thì bắt đúng thấp (63% và 13%), so với 97% của mô hình học từ câu. Cụm từ rút tự động có nhiều "dấu vân tay" của khuôn câu tổng hợp, nên chỉ cụm từ tự soạn được dùng để giải thích trong cảnh báo.

## Bộ phân biệt ngữ cảnh (`bo_phan_biet_ngu_canh.csv`, v1.7)
- 6.230 tin từ 154 khung câu do học sinh viết (`src/data_tuyen_truyen.py`): 4.226 tin **tuyên truyền** (nhãn `tuyen_truyen`), 820 tin thường khó (`bt_kho`), 1.184 tin nguy cơ khó (tin lừa giả dạng lời cảnh báo, xưng danh cơ quan, nhà trường).
- Văn phong dựa trên các khuyến cáo công khai của công an, Bộ GD&ĐT, Cục An toàn thông tin, UNICEF; không chép tin nhắn hay bình luận của người thật; mọi tên, số, link đều giả.
- Chia theo khung câu: 60% huấn luyện, 15% kiểm định, 25% kiểm tra độc lập (`doc_lap`). Lõi tin nguy cơ được trích lại chỉ lấy từ phần cùng tập của bộ gốc.

## Tập kiểm tra viết tay (`kiem_tra_viet_tay.csv`, v1.7)
- 208 câu học sinh tự viết, không sinh từ khuôn câu: 108 tin tuyên truyền, 50 tin thường khó, 35 tin nguy cơ trực tiếp, 15 tin lừa giả dạng lời cảnh báo.
- **Chỉ dùng để đo**, không dùng để huấn luyện hay chọn ngưỡng. `src/kiem_tra_ro_ri.py` kiểm tra rò rỉ: không câu nào giống câu huấn luyện/kiểm định từ 50% cặp từ trở lên.

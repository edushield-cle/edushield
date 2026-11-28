import SwiftUI

/// Màn hình kết quả dùng chung cho app và tiện ích chia sẻ.
struct ResultView: View {
    let text: String
    let fromImage: Bool
    let result: EduResult
    var onClose: (() -> Void)? = nil

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 10) {
                Text(result.headline).font(.title3.bold())
                Text(fromImage ? "Chữ đọc được từ ảnh (trên máy): \(String(text.prefix(220)))" : "“\(String(text.prefix(160)))”")
                    .font(.footnote).foregroundStyle(.secondary)
                if result.warn {
                    Text("🔎 " + result.reasons.joined(separator: "; ")).font(.body)
                    Text("📝 Việc nên làm").font(.headline)
                    ForEach(Array(result.todo.enumerated()), id: \.offset) { i, s in Text("\(i + 1). \(s)") }
                    Link("📞 Gọi 111 (miễn phí, 24/7)", destination: URL(string: "tel:111")!)
                } else if result.frame == "tuyen_truyen" {
                    Text("Tin này nhắc tới thủ đoạn để mọi người cảnh giác, không nhắm vào bạn. Nếu ai đó gửi riêng cho bạn kèm yêu cầu chuyển tiền, đọc mã hay giữ bí mật, hãy hỏi người lớn.")
                } else {
                    Text("AI có thể sai. Nếu vẫn thấy lo, hãy hỏi một người lớn bạn tin.")
                }
                Text("EduShield chỉ cảnh báo, bạn là người quyết định. Nội dung không được lưu hay gửi đi.").font(.footnote).foregroundStyle(.secondary)
                if let onClose { Button("Xong", action: onClose).buttonStyle(.borderedProminent) }
            }.padding()
        }
    }
}

import SwiftUI
import PhotosUI
import UserNotifications

struct ContentView: View {
    @State private var tab = 0
    var body: some View {
        TabView(selection: $tab) {
            CheckView().tabItem { Label("Kiểm tra", systemImage: "magnifyingglass") }.tag(0)
            // Nút "← Màn hình chính" trong trang diễn tập đưa học sinh về tab Kiểm tra
            DrillView(onHome: { tab = 0 }).tabItem { Label("Diễn tập", systemImage: "target") }.tag(1)
            GuideView().tabItem { Label("Hướng dẫn", systemImage: "questionmark.circle") }.tag(2)
        }
    }
}

/// Kiểm tra: dán đoạn chat, hoặc chọn ẢNH CHỤP MÀN HÌNH để đọc chữ ngay trên máy.
struct CheckView: View {
    @State private var text = ""
    @State private var result: EduResult?
    @State private var fromImage = false
    @State private var photo: PhotosPickerItem?
    @State private var busy = false

    var body: some View {
        NavigationStack {
            Form {
                Section("Tin nhắn, bình luận cần kiểm tra") {
                    TextEditor(text: $text).frame(minHeight: 110)
                    HStack {
                        Button("📋 Dán") { text = UIPasteboard.general.string ?? "" }
                        Spacer()
                        PhotosPicker("🖼️ Ảnh chụp màn hình", selection: $photo, matching: .images)
                    }
                    Button(busy ? "Đang đọc ảnh…" : "🔍 Kiểm tra") { check(text, image: false) }.disabled(text.isEmpty || busy)
                }
                if let r = result { Section { ResultView(text: text, fromImage: fromImage, result: r) } }
                Section("Độ nhạy") {
                    Picker("Mức nhạy", selection: Binding(get: { EduShieldEngine.sensitivity }, set: { EduShieldEngine.sensitivity = $0 })) {
                        Text("Ít phiền").tag("it"); Text("Cân bằng").tag("can_bang"); Text("Nhạy").tag("nhay")
                    }.pickerStyle(.segmented)
                }
            }
            .navigationTitle("EduShield AI")
            .onChange(of: photo) { _, item in
                guard let item else { return }
                busy = true
                item.loadTransferable(type: Data.self) { res in
                    guard case .success(let data?) = res, let img = UIImage(data: data) else { DispatchQueue.main.async { busy = false }; return }
                    OCR.read(img) { s in busy = false; text = s; check(s, image: true) }
                }
            }
        }
    }

    private func check(_ s: String, image: Bool) {
        fromImage = image
        result = EduShieldEngine.shared.analyze(s)
    }
}

/// Hướng dẫn bật Tiện ích chia sẻ và Bàn phím thông minh; minh bạch về "Cho phép truy cập đầy đủ".
struct GuideView: View {
    var body: some View {
        NavigationStack {
            List {
                Section("👆 Một chạm: Chia sẻ") {
                    Text("Trong Zalo, Messenger, Ảnh: chọn tin nhắn hoặc ảnh chụp màn hình → nút Chia sẻ → EduShield. Ảnh được đọc chữ ngay trên máy.")
                }
                Section("⌨️ Bàn phím thông minh") {
                    Text("Cài đặt → Cài đặt chung → Bàn phím → Bàn phím → Thêm bàn phím mới → EduShield. Khi cần, bấm 🌐 để chuyển sang EduShield:")
                    Text("• Kiểm tra trước khi gửi: nhắc bạn nếu sắp gửi mã OTP, số tài khoản hoặc lời lẽ có thể làm người khác tổn thương.")
                    Text("• Trả lời an toàn: chèn nhanh câu từ chối lịch sự.")
                    Text("• Kiểm tra tin đã sao chép: cần bật “Cho phép truy cập đầy đủ”. iOS sẽ cảnh báo rằng bàn phím có thể gửi dữ liệu đi; EduShield KHÔNG có mã gửi dữ liệu, chỉ đọc bộ nhớ tạm khi bạn bấm nút. Không bật cũng dùng được hai tính năng trên.")
                }
                Section("🔒 Quyền riêng tư") {
                    Text("Không lưu, không gửi nội dung tin nhắn. Điểm diễn tập chỉ lưu trên iPhone này.")
                }
                Section { Text("Cần giúp ngay: gọi 111 (miễn phí, 24/7). Nguy hiểm tức thời: gọi 113.") }
            }.navigationTitle("Hướng dẫn")
        }
    }
}

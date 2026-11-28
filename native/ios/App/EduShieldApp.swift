import SwiftUI
import UserNotifications

@main
struct EduShieldApp: App {
    @AppStorage("consent") private var consent = false
    var body: some Scene {
        WindowGroup {
            if consent { ContentView() } else { ConsentView() }
        }
    }
}

struct ConsentView: View {
    @AppStorage("consent") private var consent = false
    @State private var agree = false
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                Text("🛡️ EduShield AI").font(.largeTitle.bold())
                Text("Giúp bạn nhận ra tin nhắn lừa đảo, bắt nạt và luyện phản xạ an toàn.")
                Text("• Mọi phân tích diễn ra NGAY TRÊN iPHONE; nội dung không bị lưu hay gửi đi.\n• Bạn tự chọn dùng tiện ích Chia sẻ, Bàn phím thông minh, Thực chiến giả lập.\n• AI có thể sai. EduShield chỉ cảnh báo, bạn là người quyết định.")
                Toggle("Mình đã hiểu và tự nguyện dùng EduShield", isOn: $agree)
                Button("Bắt đầu") { consent = true }.buttonStyle(.borderedProminent).disabled(!agree)
            }.padding()
        }
    }
}

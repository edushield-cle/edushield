import SwiftUI
import WebKit
import UserNotifications

/// Thực chiến giả lập: dùng CHUNG trang diễn tập (drill.html) với tiện ích và app web.
struct DrillView: View {
    var onHome: () -> Void = {}
    var body: some View { DrillWeb(onHome: onHome).ignoresSafeArea(edges: .bottom) }
}

struct DrillWeb: UIViewRepresentable {
    var onHome: () -> Void
    func makeCoordinator() -> Coordinator { Coordinator(onHome: onHome) }

    func makeUIView(context: Context) -> WKWebView {
        let cfg = WKWebViewConfiguration()
        cfg.userContentController.add(context.coordinator, name: "drill")
        // Tới giờ diễn tập thì mở thẳng một tình huống
        let next = UserDefaults.standard.double(forKey: "drillNext")
        if next > 0 && Date().timeIntervalSince1970 * 1000 >= next {
            cfg.userContentController.addUserScript(WKUserScript(source: "window.__EDUSHIELD_AUTO = true;", injectionTime: .atDocumentStart, forMainFrameOnly: true))
        }
        let web = WKWebView(frame: .zero, configuration: cfg)
        if let url = Bundle.main.url(forResource: "drill", withExtension: "html", subdirectory: "drill") {
            web.loadFileURL(url, allowingReadAccessTo: url.deletingLastPathComponent())
        }
        return web
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {}

    final class Coordinator: NSObject, WKScriptMessageHandler {
        let onHome: () -> Void
        init(onHome: @escaping () -> Void) { self.onHome = onHome }

        /// Trang diễn tập báo thời điểm lần tiếp theo -> hẹn một thông báo cục bộ (không cần máy chủ).
        func userContentController(_ c: WKUserContentController, didReceive message: WKScriptMessage) {
            guard let body = message.body as? [String: Any] else { return }
            // Nút "← Màn hình chính"
            if body["home"] as? Bool == true { DispatchQueue.main.async { self.onHome() }; return }
            let next = (body["next"] as? NSNumber)?.doubleValue ?? 0
            UserDefaults.standard.set(next, forKey: "drillNext")
            let center = UNUserNotificationCenter.current()
            center.removePendingNotificationRequests(withIdentifiers: ["drill"])
            let wait = next / 1000 - Date().timeIntervalSince1970
            guard next > 0, wait > 60 else { return }
            center.requestAuthorization(options: [.alert, .sound]) { ok, _ in
                guard ok else { return }
                let content = UNMutableNotificationContent()
                content.title = "📩 Bạn có một tin nhắn mới"
                content.body = "Mở EduShield để xem và phản hồi."
                let req = UNNotificationRequest(identifier: "drill", content: content, trigger: UNTimeIntervalNotificationTrigger(timeInterval: wait, repeats: false))
                center.add(req)
            }
        }
    }
}

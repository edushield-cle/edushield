import Foundation
import JavaScriptCore

/// Kết quả phân tích (rút gọn từ EduShieldDetector.analyze của tiện ích).
struct EduResult {
    var label = "binh_thuong"
    var level = "an_toan"
    var warn = false
    var frame = ""
    var p = 0.0
    var catVi = ""
    var labelVi = ""
    var reasons: [String] = []
    var todo: [String] = []

    var headline: String {
        if warn { return (level == "khan_cap" ? "🚨 " : level == "canh_bao" ? "⚠️ " : "💡 ") + (catVi.isEmpty ? labelVi : catVi) }
        if frame == "tuyen_truyen" { return "ℹ️ Nội dung tuyên truyền, cảnh báo" }
        return "✅ Chưa thấy dấu hiệu rõ ràng"
    }
}

/// Chạy NGUYÊN VĂN model.js + detector.js của tiện ích bằng JavaScriptCore có sẵn trong iOS:
/// kết quả giống hệt tiện ích trình duyệt, mọi thứ chạy trên máy, không cần mạng.
final class EduShieldEngine {
    static let shared = EduShieldEngine()
    private let ctx: JSContext
    private let queue = DispatchQueue(label: "vn.edushield.engine")

    private init() {
        ctx = JSContext()!
        ctx.exceptionHandler = { _, ex in NSLog("EduShield JS: \(ex?.toString() ?? "?")") }
        let bundle = Bundle(for: EduShieldEngine.self)
        for name in ["model", "blocklist", "detector"] {
            if let url = bundle.url(forResource: name, withExtension: "js"),
               let src = try? String(contentsOf: url, encoding: .utf8) {
                ctx.evaluateScript(src)
            } else {
                NSLog("EduShield: thiếu \(name).js trong gói ứng dụng")
            }
        }
    }

    /// Độ nhạy dùng chung giữa app, tiện ích chia sẻ và bàn phím (App Group).
    static var sensitivity: String {
        get { UserDefaults(suiteName: "group.vn.edushield.app")?.string(forKey: "sens") ?? "can_bang" }
        set { UserDefaults(suiteName: "group.vn.edushield.app")?.set(newValue, forKey: "sens") }
    }

    func analyze(_ text: String) -> EduResult {
        queue.sync {
            var r = EduResult()
            guard let det = ctx.objectForKeyedSubscript("EduShieldDetector"),
                  let fn = det.objectForKeyedSubscript("analyze"),
                  let out = fn.call(withArguments: [text, ["sens": EduShieldEngine.sensitivity]]),
                  let d = out.toDictionary() else { return r }
            r.label = d["label"] as? String ?? r.label
            r.level = d["level"] as? String ?? r.level
            r.warn = d["warn"] as? Bool ?? false
            r.frame = d["frame"] as? String ?? ""
            r.p = (d["p"] as? NSNumber)?.doubleValue ?? 0
            r.catVi = d["cat_vi"] as? String ?? ""
            r.labelVi = d["label_vi"] as? String ?? ""
            r.reasons = d["reasons"] as? [String] ?? []
            r.todo = d["todo"] as? [String] ?? []
            return r
        }
    }

    /// v1.9: TIN MÌNH SẮP GỬI. Dùng chung hàm outgoing() của detector.js với tiện ích và app web.
    func outgoing(_ text: String) -> OutgoingResult {
        queue.sync {
            var o = OutgoingResult()
            guard let det = ctx.objectForKeyedSubscript("EduShieldDetector"),
                  let fn = det.objectForKeyedSubscript("outgoing"),
                  let out = fn.call(withArguments: [text, ["sens": EduShieldEngine.sensitivity]]),
                  let d = out.toDictionary() else { return o }
            o.nudge = d["nudge"] as? Bool ?? false
            o.kind = d["kind"] as? String ?? ""
            o.title = d["title"] as? String ?? ""
            o.body = d["body"] as? String ?? ""
            o.why = d["why"] as? String ?? ""
            o.rewrite = d["rewrite"] as? [String] ?? []
            return o
        }
    }
}

struct OutgoingResult {
    var nudge = false
    var kind = ""
    var title = ""
    var body = ""
    var why = ""
    var rewrite: [String] = []
}

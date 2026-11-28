import UIKit

/// BÀN PHÍM THÔNG MINH: không thay bàn phím gõ chữ hằng ngày, mà là "bàn phím công cụ" bấm 🌐 để chuyển sang khi cần:
///  1. Kiểm tra trước khi gửi: nhắc nếu sắp gửi mã OTP, số tài khoản, hoặc lời lẽ có thể làm người khác tổn thương.
///     v1.9: phím "➤ Gửi" tự kiểm tra trước; nếu đáng lo thì hiện lời nhắc, gợi ý viết lại và nút "Vẫn gửi" (không chặn).
///  2. Trả lời an toàn: chèn nhanh câu từ chối lịch sự.
///  3. Kiểm tra tin đã sao chép (cần "Cho phép truy cập đầy đủ"; EduShield chỉ đọc bộ nhớ tạm khi học sinh bấm nút).
/// Mọi phân tích chạy trên máy; bàn phím không có mã gửi dữ liệu đi.
final class KeyboardViewController: UIInputViewController {
    private let out = UILabel()
    private let nudgeRow = UIStackView()
    private var pendingRewrite: [String] = []
    private let replies = ["Mình sẽ gọi điện xác nhận trực tiếp nhé.", "Mình không gửi mã OTP cho ai cả.", "Mình sẽ hỏi bố mẹ, thầy cô trước đã.", "Đừng nói vậy, như thế là làm bạn ấy buồn."]

    override func viewDidLoad() {
        super.viewDidLoad()
        let h = view.heightAnchor.constraint(equalToConstant: 270)
        h.priority = .defaultHigh
        h.isActive = true

        out.numberOfLines = 0
        out.font = .preferredFont(forTextStyle: .footnote)
        out.text = "🛡️ EduShield: chọn một công cụ bên dưới."

        let row1 = stack([btn("🛡️ Kiểm tra trước khi gửi", #selector(checkOutgoing)), btn("📋 Kiểm tra tin đã sao chép", #selector(checkClipboard))])
        let row2 = stack(replies.prefix(2).enumerated().map { i, s in btn("💬 " + s, #selector(reply(_:)), tag: i) })
        let row3 = stack(replies.suffix(2).enumerated().map { i, s in btn("💬 " + s, #selector(reply(_:)), tag: i + 2) })
        let globe = btn("🌐 Đổi bàn phím", nil)
        globe.addTarget(self, action: #selector(handleInputModeList(from:with:)), for: .allTouchEvents)
        let row4 = stack([globe, btn("⌫", #selector(back)), btn("➤ Gửi (kiểm tra trước)", #selector(sendChecked))])
        nudgeRow.axis = .horizontal; nudgeRow.spacing = 6; nudgeRow.distribution = .fillEqually
        nudgeRow.isHidden = true

        let all = UIStackView(arrangedSubviews: [out, nudgeRow, row1, row2, row3, row4])
        all.axis = .vertical; all.spacing = 6
        all.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(all)
        NSLayoutConstraint.activate([
            all.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 6),
            all.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -6),
            all.topAnchor.constraint(equalTo: view.topAnchor, constant: 6),
            all.bottomAnchor.constraint(lessThanOrEqualTo: view.bottomAnchor, constant: -6),
        ])
    }

    private func btn(_ title: String, _ action: Selector?, tag: Int = 0) -> UIButton {
        let b = UIButton(type: .system)
        b.setTitle(title, for: .normal)
        b.titleLabel?.numberOfLines = 2
        b.titleLabel?.font = .preferredFont(forTextStyle: .footnote)
        b.backgroundColor = .secondarySystemBackground
        b.layer.cornerRadius = 8
        b.tag = tag
        if let action { b.addTarget(self, action: action, for: .touchUpInside) }
        return b
    }

    private func stack(_ v: [UIView]) -> UIStackView {
        let s = UIStackView(arrangedSubviews: v)
        s.axis = .horizontal; s.spacing = 6; s.distribution = .fillEqually
        s.heightAnchor.constraint(greaterThanOrEqualToConstant: 40).isActive = true
        return s
    }

    /// Nhắc TRƯỚC KHI GỬI: đọc đoạn học sinh vừa gõ (ngay trong ô đang nhập), không đọc tin của người khác.
    @objc private func checkOutgoing() {
        let typed = textDocumentProxy.documentContextBeforeInput ?? ""
        if typed.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty { out.text = "Chưa có chữ nào trong ô nhập."; return }
        if typed.range(of: #"(?<!\d)\d{4,8}(?!\d)"#, options: .regularExpression) != nil,
           typed.range(of: #"(?i)(otp|mã|ma xac|code)"#, options: .regularExpression) != nil {
            out.text = "⚠️ Bạn sắp gửi một dãy số giống mã OTP. Không ai cần mã OTP của bạn, kể cả bạn thân hay ngân hàng."; return
        }
        if typed.range(of: #"(?<!\d)\d{9,16}(?!\d)"#, options: .regularExpression) != nil {
            out.text = "⚠️ Bạn sắp gửi một dãy số dài (số tài khoản, căn cước?). Chắc chắn người nhận là người bạn tin chứ?"; return
        }
        let r = EduShieldEngine.shared.analyze(typed)
        if r.warn && r.label == "bat_nat" {
            out.text = "💭 Lời nhắn này có thể làm người nhận tổn thương (\(r.catVi)). Bạn có muốn viết lại nhẹ nhàng hơn?"
        } else if r.warn {
            out.text = "⚠️ Đoạn này giống tin \(r.catVi). Bạn đang trả lời ai vậy? Hãy kiểm tra lại trước khi gửi."
        } else {
            out.text = "✅ Không thấy điều gì đáng lo trong đoạn bạn vừa gõ."
        }
    }

    @objc private func checkClipboard() {
        guard hasFullAccess else {
            out.text = "Để đọc tin đã sao chép, hãy bật “Cho phép truy cập đầy đủ” cho EduShield trong Cài đặt → Bàn phím. Hoặc dùng nút Chia sẻ → EduShield."
            return
        }
        let s = UIPasteboard.general.string ?? ""
        if s.isEmpty { out.text = "Bộ nhớ tạm đang trống. Nhấn giữ tin nhắn → Sao chép rồi bấm lại."; return }
        let r = EduShieldEngine.shared.analyze(s)
        var t = r.headline
        if r.warn, let first = r.todo.first { t += "\n👉 " + first }
        out.text = t
    }

    /// v1.9: "➤ Gửi" = phím xuống dòng (ứng dụng chat coi là Gửi), nhưng kiểm tra trước. Chỉ nhắc, học sinh vẫn quyết định.
    @objc private func sendChecked() {
        let typed = textDocumentProxy.documentContextBeforeInput ?? ""
        let o = EduShieldEngine.shared.outgoing(typed)
        guard o.nudge else { textDocumentProxy.insertText("\n"); return }
        countNudge("shown")
        out.text = "✋ \(o.title)\n\(o.body)" + (o.why.isEmpty ? "" : " (\(o.why))")
        pendingRewrite = Array(o.rewrite.prefix(2))
        nudgeRow.arrangedSubviews.forEach { $0.removeFromSuperview() }
        for (i, s) in pendingRewrite.enumerated() { nudgeRow.addArrangedSubview(btn("💬 " + s, #selector(useRewrite(_:)), tag: i)) }
        nudgeRow.addArrangedSubview(btn("✏️ Sửa lại", #selector(dismissNudge)))
        nudgeRow.addArrangedSubview(btn("Vẫn gửi", #selector(sendAnyway)))
        nudgeRow.isHidden = false
    }
    @objc private func useRewrite(_ b: UIButton) {
        let typed = textDocumentProxy.documentContextBeforeInput ?? ""
        for _ in typed { textDocumentProxy.deleteBackward() }
        textDocumentProxy.insertText(pendingRewrite[b.tag])
        countNudge("fixed"); dismissNudge()
    }
    @objc private func dismissNudge() { nudgeRow.isHidden = true; out.text = "🛡️ EduShield: chọn một công cụ bên dưới." }
    @objc private func sendAnyway() { countNudge("sent"); dismissNudge(); textDocumentProxy.insertText("\n") }
    /// Chỉ đếm số lần (không lưu nội dung) để học sinh tự xem trong app.
    private func countNudge(_ key: String) {
        let d = UserDefaults(suiteName: "group.vn.edushield.app")
        d?.set((d?.integer(forKey: "nudge_" + key) ?? 0) + 1, forKey: "nudge_" + key)
    }

    @objc private func reply(_ b: UIButton) { textDocumentProxy.insertText(replies[b.tag]) }
    @objc private func back() { textDocumentProxy.deleteBackward() }
    @objc private func newline() { textDocumentProxy.insertText("\n") }
}

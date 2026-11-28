import UIKit
import SwiftUI
import UniformTypeIdentifiers

/// Tiện ích CHIA SẺ: từ Zalo, Messenger, Ảnh... bấm Chia sẻ → EduShield.
/// Nhận chữ, link hoặc ẢNH CHỤP MÀN HÌNH (đọc chữ ngay trên máy) rồi hiện kết quả. Không lưu, không gửi đi.
final class ShareViewController: UIViewController {
    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground
        let wait = UILabel()
        wait.text = "🔎 EduShield đang kiểm tra…"
        wait.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(wait)
        NSLayoutConstraint.activate([wait.centerXAnchor.constraint(equalTo: view.centerXAnchor), wait.centerYAnchor.constraint(equalTo: view.centerYAnchor)])
        load()
    }

    private func load() {
        let items = (extensionContext?.inputItems as? [NSExtensionItem]) ?? []
        let providers = items.flatMap { $0.attachments ?? [] }
        if let p = providers.first(where: { $0.hasItemConformingToTypeIdentifier(UTType.image.identifier) }) {
            p.loadItem(forTypeIdentifier: UTType.image.identifier, options: nil) { [weak self] item, _ in
                var img: UIImage?
                if let url = item as? URL, let d = try? Data(contentsOf: url) { img = UIImage(data: d) }
                else if let d = item as? Data { img = UIImage(data: d) }
                else if let i = item as? UIImage { img = i }
                guard let img else { self?.show("", image: true); return }
                OCR.read(img) { text in self?.show(text, image: true) }
            }
        } else if let p = providers.first(where: { $0.hasItemConformingToTypeIdentifier(UTType.plainText.identifier) }) {
            p.loadItem(forTypeIdentifier: UTType.plainText.identifier, options: nil) { [weak self] item, _ in
                self?.show((item as? String) ?? "", image: false)
            }
        } else if let p = providers.first(where: { $0.hasItemConformingToTypeIdentifier(UTType.url.identifier) }) {
            p.loadItem(forTypeIdentifier: UTType.url.identifier, options: nil) { [weak self] item, _ in
                self?.show((item as? URL)?.absoluteString ?? "", image: false)
            }
        } else {
            show("", image: false)
        }
    }

    private func show(_ text: String, image: Bool) {
        DispatchQueue.main.async {
            let r = EduShieldEngine.shared.analyze(text)
            let host = UIHostingController(rootView: ResultView(text: text.isEmpty ? "(không đọc được chữ)" : text, fromImage: image, result: r) { [weak self] in
                self?.extensionContext?.completeRequest(returningItems: nil, completionHandler: nil)
            })
            self.addChild(host)
            host.view.frame = self.view.bounds
            host.view.autoresizingMask = [.flexibleWidth, .flexibleHeight]
            self.view.subviews.forEach { $0.removeFromSuperview() }
            self.view.addSubview(host.view)
            host.didMove(toParent: self)
        }
    }
}

import Foundation
import Vision
import UIKit

/// Đọc chữ trong ảnh chụp màn hình NGAY TRÊN MÁY bằng Vision của Apple (tiếng Việt từ iOS 17).
enum OCR {
    static func read(_ image: UIImage, done: @escaping (String) -> Void) {
        guard let cg = image.cgImage else { done(""); return }
        let req = VNRecognizeTextRequest { req, _ in
            let lines = (req.results as? [VNRecognizedTextObservation] ?? []).compactMap { $0.topCandidates(1).first?.string }
            DispatchQueue.main.async { done(lines.joined(separator: "\n")) }
        }
        req.recognitionLevel = .accurate
        req.usesLanguageCorrection = true
        let supported = (try? req.supportedRecognitionLanguages()) ?? []
        // Ưu tiên tiếng Việt nếu máy hỗ trợ; nếu không, để Vision tự nhận dạng
        let want = ["vi-VT", "vi-VN", "en-US"].filter { supported.contains($0) }
        if !want.isEmpty { req.recognitionLanguages = want }
        DispatchQueue.global(qos: .userInitiated).async {
            do { try VNImageRequestHandler(cgImage: cg, orientation: .up).perform([req]) }
            catch { DispatchQueue.main.async { done("") } }
        }
    }
}

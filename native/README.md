# EduShield AI – ứng dụng gốc Android và iOS (v1.8)

Hai ứng dụng dùng **chung mô hình** với tiện ích trình duyệt, nên cho kết quả giống hệt:

| | Android | iOS |
|---|---|---|
| Bộ phát hiện | `EduShieldCore.java` (dịch 1-1 từ `detector.js`, đọc `model.json`) | chạy **nguyên văn** `model.js` + `detector.js` bằng JavaScriptCore có sẵn trong iOS |
| Tự động cảnh báo | **Đọc thông báo tin nhắn** (Notification Listener) và **quét màn hình nâng cao** (Accessibility, tuỳ chọn) | không có (iOS không cho ứng dụng đọc tin của ứng dụng khác) |
| Một chạm | **Chia sẻ** chữ hoặc ảnh chụp màn hình → EduShield; ô **Cài đặt nhanh** “Kiểm tra tin đã sao chép” | **Tiện ích Chia sẻ** (chữ, link, ảnh chụp màn hình) và **Bàn phím thông minh** |
| Đọc chữ trong ảnh | ML Kit Text Recognition (mô hình chữ Latin, có tiếng Việt), trên máy | Vision của Apple (tiếng Việt từ iOS 17), trên máy |
| Thực chiến giả lập | WebView chạy chung `drill.html`; hẹn giờ bằng AlarmManager | WKWebView chạy chung `drill.html`; thông báo cục bộ |
| Gửi dữ liệu | **Không có quyền Internet** (đã gỡ trong manifest) | không có mã gửi dữ liệu |

> Trạng thái: mã nguồn hoàn chỉnh nhưng **chưa được biên dịch trong môi trường của dự án** (không có Android SDK, Xcode).
> Đã kiểm chứng: lõi Java cho kết quả trùng khớp 563/563 mẫu với bản JavaScript; mã Android biên dịch được với các lớp giả lập API (chỉ kiểm tra cú pháp và kiểu dữ liệu).
> Lần đầu mở trong Android Studio / Xcode có thể cần sửa nhỏ theo phiên bản công cụ.

## 1. Cập nhật mô hình cho ứng dụng gốc

Sau mỗi lần huấn luyện lại (`python export_extension.py`):

```
node native/tools/export_native.js
javac -encoding UTF-8 -d build_test native/android/app/src/main/java/vn/edushield/core/*.java native/tools/CoreTest.java
java -Dstdout.encoding=UTF-8 -cp build_test CoreTest .
```
Kết quả mong đợi: `lệch chuẩn hoá 0, lệch nhãn 0, lệch cảnh báo 0 ... OK`.

## 2. Android (Android Studio, máy Windows được)

1. Cài Android Studio (bản mới), chọn **Open** → thư mục `native/android`. Android Studio tự tải Gradle 8.7, Android Gradle Plugin 8.5.2 và ML Kit.
2. Cắm điện thoại Android (bật *Tuỳ chọn nhà phát triển → Gỡ lỗi USB*) → bấm **Run**. Hoặc **Build → Build APK(s)** rồi chép tệp APK sang điện thoại để cài.
3. Trong app: đồng ý → **Bật trong Cài đặt** (Truy cập thông báo) → chọn ứng dụng chat được đọc.
4. Tuỳ chọn: **Quét màn hình nâng cao** – app hiện màn hình giải thích rõ quyền Hỗ trợ tiếp cận dùng để làm gì trước khi mở Cài đặt.
5. Thêm ô **Kiểm tra tin đã sao chép** vào bảng Cài đặt nhanh (kéo thanh thông báo → bút chì).

**Lưu ý chính sách:** Google Play chỉ cho ứng dụng hỗ trợ người khuyết tật khai báo `isAccessibilityTool`; ứng dụng khác dùng Accessibility phải có màn hình công khai mục đích, xin đồng ý rõ ràng và được Google duyệt. EduShield khai báo `isAccessibilityTool="false"`, có màn hình công khai, và để chế độ này **tắt mặc định**; cách nhẹ hơn (đọc thông báo) là cách khuyên dùng. Bản dự thi được cài trực tiếp bằng tệp APK.

## 3. iOS (cần máy Mac có Xcode 15 trở lên)

1. `brew install xcodegen` → `cd native/ios` → `xcodegen` (tạo `EduShield.xcodeproj` từ `project.yml`).
2. Mở dự án, chọn **Team** (tài khoản Apple ID miễn phí cũng được) cho cả 3 target, đổi tiền tố bundle id nếu bị trùng, giữ App Group `group.vn.edushield.app` (hoặc đổi đồng loạt).
3. Cắm iPhone (iOS 17 trở lên) → **Run**.
4. Bật bàn phím: Cài đặt → Cài đặt chung → Bàn phím → Bàn phím → Thêm bàn phím mới → EduShield. “Cho phép truy cập đầy đủ” chỉ cần cho nút *Kiểm tra tin đã sao chép*.
5. Dùng tiện ích chia sẻ: trong Zalo, Messenger, Ảnh → **Chia sẻ** → EduShield.

## 4. Cấu trúc

```
native/
  tools/export_native.js   xuất model.json, ui.json (Android) và chép model.js, detector.js, drill.* (iOS)
  tools/CoreTest.java      kiểm tra lõi Java khớp bản JavaScript (core_expected.json)
  android/                 dự án Android Studio (Java, không cần AndroidX)
    app/src/main/java/vn/edushield/core/   EduShieldCore.java, MiniJson.java (không phụ thuộc Android)
    app/src/main/java/vn/edushield/app/    MainActivity, EduNotificationListener, EduAccessibilityService,
                                           ShareActivity (ML Kit), ClipboardActivity + ClipboardTileService,
                                           ResultActivity, DrillActivity + DrillReceiver, Engine, Ui
  ios/                     project.yml (XcodeGen), App/ (SwiftUI), ShareExtension/, Keyboard/, Shared/ (Swift, js, drill)
```

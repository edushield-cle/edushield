package vn.edushield.app;

import android.app.Notification;
import android.os.Bundle;
import android.os.Parcelable;
import android.service.notification.NotificationListenerService;
import android.service.notification.StatusBarNotification;

import java.util.ArrayList;
import java.util.List;

/**
 * Đọc PHẦN XEM TRƯỚC của thông báo tin nhắn mới (chỉ ở ứng dụng học sinh đã chọn) và cảnh báo nếu có dấu hiệu nguy cơ.
 * Học sinh tự cấp quyền trong Cài đặt → Truy cập thông báo. Không lưu, không gửi nội dung đi đâu.
 */
public class EduNotificationListener extends NotificationListenerService {
    @Override
    public void onNotificationPosted(StatusBarNotification sbn) {
        try {
            if (!Engine.consented(this)) return;
            String pkg = sbn.getPackageName();
            if (getPackageName().equals(pkg) || !Engine.watched(this).contains(pkg)) return;
            Notification n = sbn.getNotification();
            if ((n.flags & Notification.FLAG_GROUP_SUMMARY) != 0) return;
            String app = Engine.APPS.containsKey(pkg) ? Engine.APPS.get(pkg) : pkg;
            for (String t : texts(n.extras)) Engine.check(this, t, app);
        } catch (Exception e) {
            // không bao giờ làm hỏng hệ thống thông báo vì lỗi phân tích
        }
    }

    /** Lấy các đoạn chữ: từng tin trong kiểu hội thoại (MessagingStyle), nếu không có thì lấy nội dung chính. */
    static List<String> texts(Bundle ex) {
        List<String> out = new ArrayList<>();
        if (ex == null) return out;
        // Thông báo kiểu hội thoại: mỗi tin là một Bundle có khoá "text"
        Parcelable[] arr = ex.getParcelableArray(Notification.EXTRA_MESSAGES);
        if (arr != null) {
            for (Parcelable p : arr) {
                if (p instanceof Bundle) {
                    CharSequence t = ((Bundle) p).getCharSequence("text");
                    if (t != null) out.add(t.toString());
                }
            }
        }
        if (out.isEmpty()) {
            CharSequence big = ex.getCharSequence(Notification.EXTRA_BIG_TEXT);
            CharSequence txt = ex.getCharSequence(Notification.EXTRA_TEXT);
            if (big != null) out.add(big.toString()); else if (txt != null) out.add(txt.toString());
        }
        return out;
    }
}

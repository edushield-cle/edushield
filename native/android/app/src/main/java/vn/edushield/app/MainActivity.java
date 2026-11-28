package vn.edushield.app;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ComponentName;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.text.TextUtils;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.RadioButton;
import android.widget.RadioGroup;
import android.widget.ScrollView;

import java.util.Map;
import java.util.Set;

/** Màn hình chính: đồng ý minh bạch, bật từng cách bảo vệ, kiểm tra thủ công, diễn tập, nhật ký. */
public class MainActivity extends Activity {
    @Override protected void onResume() {
        super.onResume();
        Engine.channels(this);
        if (Build.VERSION.SDK_INT >= 33 && !Engine.prefs(this).getBoolean("askedNotif", false)) {
            Engine.prefs(this).edit().putBoolean("askedNotif", true).apply(); // chỉ hỏi một lần
            requestPermissions(new String[]{"android.permission.POST_NOTIFICATIONS"}, 1);
        }
        if (!Engine.consented(this)) showConsent(); else showMain();
    }

    private void setPage(LinearLayout root) {
        ScrollView sv = new ScrollView(this);
        sv.setBackgroundColor(Color.parseColor("#F4F7FB"));
        sv.addView(root);
        setContentView(sv);
    }

    private void showConsent() {
        LinearLayout root = Ui.col(this);
        LinearLayout c = Ui.card(this);
        c.addView(Ui.title(this, "🛡️ EduShield AI giúp bạn nhận ra tin nhắn xấu"));
        c.addView(Ui.text(this, "Trước khi dùng, bạn cần biết rõ:", 15));
        c.addView(Ui.text(this, "• Mọi phân tích diễn ra NGAY TRÊN ĐIỆN THOẠI. Ứng dụng không có quyền Internet nên không thể gửi tin nhắn của bạn đi đâu.\n"
                + "• EduShield không lưu nội dung tin nhắn; nhật ký chỉ ghi giờ và loại nguy cơ.\n"
                + "• Bạn tự chọn bật từng tính năng, tắt được bất cứ lúc nào.\n"
                + "• AI có thể sai. EduShield chỉ cảnh báo, bạn là người quyết định.", 15));
        CheckBox agree = new CheckBox(this);
        agree.setText("Mình đã hiểu và tự nguyện dùng EduShield");
        c.addView(agree);
        c.addView(Ui.button(this, "Bắt đầu", v -> {
            if (!agree.isChecked()) { agree.setError("Hãy tích ô đồng ý"); return; }
            Engine.prefs(this).edit().putBoolean("consent", true).apply();
            showMain();
        }));
        root.addView(c);
        setPage(root);
    }

    private boolean listenerOn() {
        String flat = Settings.Secure.getString(getContentResolver(), "enabled_notification_listeners");
        return flat != null && flat.contains(new ComponentName(this, EduNotificationListener.class).flattenToString());
    }

    private boolean a11yOn() {
        String flat = Settings.Secure.getString(getContentResolver(), Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES);
        return flat != null && flat.contains(new ComponentName(this, EduAccessibilityService.class).flattenToString());
    }

    private void showMain() {
        LinearLayout root = Ui.col(this);
        SharedPreferences p = Engine.prefs(this);

        // 1. Đọc thông báo tin nhắn (khuyên dùng)
        LinearLayout c1 = Ui.card(this);
        c1.addView(Ui.title(this, "🔔 Đọc thông báo tin nhắn " + (listenerOn() ? "· ĐANG BẬT" : "· đang tắt")));
        c1.addView(Ui.small(this, "Khi có tin nhắn mới từ ứng dụng bạn chọn bên dưới, EduShield đọc phần xem trước trong thông báo và cảnh báo nếu có dấu hiệu nguy cơ. Cách này nhẹ, không đọc màn hình."));
        c1.addView(Ui.button(this, listenerOn() ? "Mở cài đặt để tắt" : "Bật trong Cài đặt", v ->
                startActivity(new Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS))));
        root.addView(c1);

        // 2. Chế độ nâng cao: Accessibility (công khai rõ ràng trước khi bật)
        LinearLayout c2 = Ui.card(this);
        c2.addView(Ui.title(this, "🧩 Quét màn hình nâng cao (tuỳ chọn) " + (a11yOn() ? "· ĐANG BẬT" : "· đang tắt")));
        c2.addView(Ui.small(this, "Đọc chữ đang hiển thị (tin nhắn, bình luận) trong ứng dụng chat bạn chọn, kể cả tin cũ khi bạn cuộn. Dùng quyền Hỗ trợ tiếp cận, nên cần bạn đọc kỹ trước khi bật."));
        c2.addView(Ui.button(this, a11yOn() ? "Mở cài đặt để tắt" : "Tìm hiểu và bật", v -> showA11yDisclosure()));
        root.addView(c2);

        // 3. Ứng dụng được theo dõi
        LinearLayout c3 = Ui.card(this);
        c3.addView(Ui.title(this, "📱 Ứng dụng EduShield được đọc"));
        Set<String> sel = Engine.watched(this);
        for (Map.Entry<String, String> e : Engine.APPS.entrySet()) {
            CheckBox cb = new CheckBox(this);
            cb.setText(e.getValue());
            cb.setChecked(sel.contains(e.getKey()));
            cb.setOnCheckedChangeListener((b, on) -> {
                Set<String> s = Engine.watched(this);
                if (on) s.add(e.getKey()); else s.remove(e.getKey());
                Engine.prefs(this).edit().putStringSet("apps", s).apply();
            });
            c3.addView(cb);
        }
        c3.addView(Ui.small(this, "Ngân hàng, ví điện tử, email không bao giờ có trong danh sách."));
        root.addView(c3);

        // 4. Một chạm: chia sẻ / sao chép
        LinearLayout c4 = Ui.card(this);
        c4.addView(Ui.title(this, "👆 Kiểm tra một chạm"));
        c4.addView(Ui.small(this, "• Ảnh chụp màn hình hoặc đoạn chat: bấm Chia sẻ → EduShield (đọc chữ trong ảnh ngay trên máy).\n• Tin đã sao chép: kéo thanh thông báo, thêm ô “Kiểm tra tin đã sao chép”.\n• Hoặc dán vào ô dưới đây."));
        EditText et = new EditText(this);
        et.setHint("Dán tin nhắn cần kiểm tra…");
        et.setMinLines(3);
        c4.addView(et);
        c4.addView(Ui.button(this, "🔍 Kiểm tra", v -> {
            if (TextUtils.isEmpty(et.getText())) return;
            startActivity(new Intent(this, ResultActivity.class).putExtra("text", et.getText().toString()).putExtra("app", "ô kiểm tra"));
        }));
        root.addView(c4);

        // 5. Độ nhạy
        LinearLayout c5 = Ui.card(this);
        c5.addView(Ui.title(this, "🎚️ Mức nhạy"));
        RadioGroup rg = new RadioGroup(this);
        String[][] opts = {{"it", "Ít phiền"}, {"can_bang", "Cân bằng"}, {"nhay", "Nhạy"}};
        for (String[] o : opts) {
            RadioButton rb = new RadioButton(this);
            rb.setText(o[1]); rb.setTag(o[0]);
            rg.addView(rb);
            if (o[0].equals(Engine.sens(this))) rb.setChecked(true);
        }
        rg.setOnCheckedChangeListener((g, id) -> {
            RadioButton rb = g.findViewById(id);
            if (rb != null) Engine.prefs(this).edit().putString("sens", (String) rb.getTag()).apply();
        });
        c5.addView(rg);
        root.addView(c5);

        // 6. Thực chiến giả lập
        LinearLayout c6 = Ui.card(this);
        c6.addView(Ui.title(this, "🎯 Thực chiến giả lập"));
        c6.addView(Ui.small(this, "Luyện phản xạ với tình huống lừa đảo, bắt nạt GIẢ ĐỊNH và theo dõi Chỉ số miễn dịch số của bạn."));
        c6.addView(Ui.button(this, "Mở diễn tập", v -> startActivity(new Intent(this, DrillActivity.class))));
        root.addView(c6);

        // 7. Nhật ký
        LinearLayout c7 = Ui.card(this);
        c7.addView(Ui.title(this, "🗒️ Cảnh báo gần đây"));
        String log = p.getString("log", "");
        c7.addView(Ui.small(this, log.isEmpty() ? "Chưa có cảnh báo nào." : log));
        c7.addView(Ui.small(this, "Chỉ lưu giờ, loại nguy cơ và tên ứng dụng; không lưu nội dung."));
        c7.addView(Ui.button(this, "🧹 Xoá nhật ký", v -> { p.edit().remove("log").apply(); showMain(); }));
        root.addView(c7);

        root.addView(Ui.small(this, "Cần giúp ngay: gọi 111 (miễn phí, 24/7). Nguy hiểm tức thời: gọi 113."));
        setPage(root);
    }

    /** Công khai rõ ràng (prominent disclosure) trước khi đưa học sinh tới màn hình bật Hỗ trợ tiếp cận. */
    private void showA11yDisclosure() {
        new AlertDialog.Builder(this)
                .setTitle("Quyền Hỗ trợ tiếp cận dùng để làm gì?")
                .setMessage("EduShield sẽ ĐỌC CHỮ ĐANG HIỂN THỊ trên màn hình, CHỈ trong các ứng dụng chat, mạng xã hội bạn đã chọn, để phát hiện dấu hiệu lừa đảo, bắt nạt và cảnh báo bạn.\n\n"
                        + "• Không đọc ô mật khẩu, không đọc ứng dụng ngân hàng, ví điện tử.\n"
                        + "• Không lưu nội dung, không gửi đi đâu (ứng dụng không có quyền Internet).\n"
                        + "• Không tự bấm, tự gõ hay điều khiển điện thoại thay bạn.\n"
                        + "• Tắt bất cứ lúc nào: Cài đặt → Hỗ trợ tiếp cận → EduShield.\n\n"
                        + "Nếu chỉ cần nhẹ nhàng hơn, hãy dùng “Đọc thông báo tin nhắn”.")
                .setPositiveButton("Tôi đồng ý, mở Cài đặt", (d, w) -> {
                    Engine.prefs(this).edit().putBoolean("a11yConsent", true).apply();
                    startActivity(new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS));
                })
                .setNegativeButton("Không, cảm ơn", null)
                .show();
    }
}

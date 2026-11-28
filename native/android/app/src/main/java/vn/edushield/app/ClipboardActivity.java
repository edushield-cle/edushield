package vn.edushield.app;

import android.app.Activity;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Intent;
import android.os.Bundle;

/** Đọc tin VỪA SAO CHÉP (Android chỉ cho đọc khi ứng dụng đang hiện trên màn hình) rồi mở kết quả. */
public class ClipboardActivity extends Activity {
    private boolean done;

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        setContentView(Ui.text(this, "📋 Đang đọc tin bạn vừa sao chép…", 16));
    }

    @Override public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (!hasFocus || done) return;
        done = true;
        ClipboardManager cm = getSystemService(ClipboardManager.class);
        ClipData cd = cm == null ? null : cm.getPrimaryClip();
        CharSequence t = (cd != null && cd.getItemCount() > 0) ? cd.getItemAt(0).coerceToText(this) : null;
        if (t == null || t.toString().trim().isEmpty()) {
            setContentView(Ui.text(this, "Bộ nhớ tạm đang trống. Hãy nhấn giữ tin nhắn → Sao chép, rồi bấm lại ô EduShield.", 16));
            return;
        }
        startActivity(new Intent(this, ResultActivity.class).putExtra("text", t.toString()).putExtra("app", "tin đã sao chép"));
        finish();
    }
}

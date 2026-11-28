package vn.edushield.app;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.webkit.JavascriptInterface;
import android.webkit.WebSettings;
import android.webkit.WebView;

/** Thực chiến giả lập: dùng CHUNG giao diện diễn tập với tiện ích và app web (assets/drill). */
public class DrillActivity extends Activity {
    @SuppressLint("SetJavaScriptEnabled")
    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        WebView w = new WebView(this);
        WebSettings s = w.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true); // điểm diễn tập lưu trong máy (localStorage)
        w.addJavascriptInterface(new Bridge(), "EduShieldAndroid");
        String q = getIntent().getBooleanExtra("auto", false) ? "?auto=1" : "";
        w.loadUrl("file:///android_asset/drill/drill.html" + q);
        setContentView(w);
    }

    final class Bridge {
        /** Trang diễn tập báo thời điểm lần diễn tập tiếp theo (mili giây), 0 = tắt. */
        @JavascriptInterface public void schedule(String next) {
            long t = 0;
            try { t = (long) Double.parseDouble(next); } catch (Exception ignored) { }
            DrillReceiver.schedule(DrillActivity.this, t);
        }

        /** Nút "← Màn hình chính": về màn hình chính của app. Mở từ thông báo thì chưa có màn hình chính phía sau, nên mở nó. */
        @JavascriptInterface public void home() {
            runOnUiThread(() -> {
                if (isTaskRoot()) startActivity(new Intent(DrillActivity.this, MainActivity.class));
                finish();
            });
        }
    }
}

package vn.edushield.app;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.widget.TextView;

import com.google.mlkit.vision.common.InputImage;
import com.google.mlkit.vision.text.TextRecognition;
import com.google.mlkit.vision.text.TextRecognizer;
import com.google.mlkit.vision.text.latin.TextRecognizerOptions;

/**
 * Nhận nội dung CHIA SẺ từ ứng dụng khác chỉ với một chạm:
 *  - chữ (đoạn chat, bình luận, link) -> kiểm tra ngay;
 *  - ẢNH (ảnh chụp màn hình đoạn chat) -> đọc chữ bằng ML Kit NGAY TRÊN MÁY rồi kiểm tra.
 */
public class ShareActivity extends Activity {
    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        Intent in = getIntent();
        if (!Intent.ACTION_SEND.equals(in.getAction())) { finish(); return; }
        String type = in.getType() == null ? "" : in.getType();
        if (type.startsWith("text/")) {
            String t = in.getStringExtra(Intent.EXTRA_TEXT);
            open(t == null ? "" : t, null);
            return;
        }
        Uri uri = in.getParcelableExtra(Intent.EXTRA_STREAM);
        if (uri == null) { finish(); return; }
        TextView wait = Ui.text(this, "🔎 Đang đọc chữ trong ảnh (ngay trên máy)…", 16);
        wait.setPadding(40, 40, 40, 40);
        setContentView(wait);
        try {
            InputImage img = InputImage.fromFilePath(this, uri);
            TextRecognizer rec = TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS);
            rec.process(img)
                    .addOnSuccessListener(res -> open(res.getText(), "anh"))
                    .addOnFailureListener(e -> { wait.setText("Không đọc được chữ trong ảnh. Hãy thử sao chép đoạn chat rồi dán vào EduShield."); });
        } catch (Exception e) {
            wait.setText("Không mở được ảnh này.");
        }
    }

    private void open(String text, String from) {
        Intent i = new Intent(this, ResultActivity.class).putExtra("text", text).putExtra("app", "nội dung chia sẻ");
        if (from != null) i.putExtra("from", from);
        startActivity(i);
        finish();
    }
}

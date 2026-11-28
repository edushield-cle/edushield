package vn.edushield.app;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.widget.LinearLayout;
import android.widget.ScrollView;

import vn.edushield.core.EduShieldCore;

/** Kết quả kiểm tra: loại nguy cơ, lý do, việc nên làm. Nội dung chỉ hiển thị trên máy, không lưu. */
public class ResultActivity extends Activity {
    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        String text = getIntent().getStringExtra("text");
        String app = getIntent().getStringExtra("app");
        String from = getIntent().getStringExtra("from"); // "anh" nếu chữ được đọc từ ảnh
        if (text == null) text = "";
        EduShieldCore.Result r = Engine.core(this).analyze(text, Engine.sens(this));
        LinearLayout root = Ui.col(this);
        String head;
        if (r.warn) head = ("khan_cap".equals(r.level) ? "🚨 " : "canh_bao".equals(r.level) ? "⚠️ " : "💡 ") + r.catVi;
        else if ("tuyen_truyen".equals(r.frame)) head = "ℹ️ Nội dung tuyên truyền, cảnh báo";
        else head = "✅ Chưa thấy dấu hiệu rõ ràng";
        root.addView(Ui.title(this, head));
        if (from != null) root.addView(Ui.small(this, "Chữ đọc được từ ảnh (trên máy): " + shorten(text, 220)));
        else root.addView(Ui.small(this, "“" + shorten(text, 160) + "”" + (app != null ? " · " + app : "")));
        if (r.warn) {
            root.addView(Ui.text(this, "🔎 " + String.join("; ", r.reasons), 15));
            root.addView(Ui.text(this, "📝 Việc nên làm:", 15));
            int k = 1;
            for (String s : r.todo) root.addView(Ui.text(this, (k++) + ". " + s, 15));
            root.addView(Ui.button(this, "📞 Gọi 111 (miễn phí, 24/7)", v -> startActivity(new Intent(Intent.ACTION_DIAL, Uri.parse("tel:111")))));
            root.addView(Ui.button(this, "🙅 Không phải nguy cơ", v -> { Engine.log(this, "Học sinh bấm \"không phải nguy cơ\""); finish(); }));
        } else if ("tuyen_truyen".equals(r.frame)) {
            root.addView(Ui.small(this, "Tin này nhắc tới thủ đoạn để mọi người cảnh giác, không nhắm vào bạn. Nếu ai đó gửi riêng cho bạn kèm yêu cầu chuyển tiền, đọc mã hay giữ bí mật, hãy hỏi người lớn."));
        } else {
            root.addView(Ui.small(this, "AI có thể sai. Nếu vẫn thấy lo, hãy hỏi một người lớn bạn tin."));
        }
        root.addView(Ui.small(this, "EduShield chỉ cảnh báo, bạn là người quyết định."));
        root.addView(Ui.button(this, "Đóng", v -> finish()));
        ScrollView sv = new ScrollView(this);
        sv.addView(root);
        setContentView(sv);
    }

    static String shorten(String s, int n) { return s.length() <= n ? s : s.substring(0, n) + "…"; }
}

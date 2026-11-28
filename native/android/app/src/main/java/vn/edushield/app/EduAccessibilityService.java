package vn.edushield.app;

import android.accessibilityservice.AccessibilityService;
import android.graphics.Rect;
import android.os.Handler;
import android.os.Looper;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;

import java.util.ArrayList;
import java.util.List;

/**
 * Chế độ quét màn hình NÂNG CAO (tuỳ chọn): đọc chữ ĐANG HIỂN THỊ trong ứng dụng chat học sinh đã chọn.
 * Chỉ đọc, KHÔNG bấm, không gõ, không điều khiển máy. Bỏ qua ô mật khẩu. Không lưu, không gửi đi đâu.
 */
public class EduAccessibilityService extends AccessibilityService {
    private final Handler h = new Handler(Looper.getMainLooper());
    private String pendingPkg;
    private final Runnable scan = this::scanNow;

    @Override
    public void onAccessibilityEvent(AccessibilityEvent e) {
        if (e == null || e.getPackageName() == null) return;
        if (!Engine.consented(this) || !Engine.prefs(this).getBoolean("a11yConsent", false)) return;
        String pkg = e.getPackageName().toString();
        if (!Engine.watched(this).contains(pkg)) return;
        pendingPkg = pkg;
        h.removeCallbacks(scan);
        h.postDelayed(scan, 1200); // gom các thay đổi liên tiếp khi đang cuộn, quét một lần
    }

    private void scanNow() {
        AccessibilityNodeInfo root = getRootInActiveWindow();
        if (root == null || pendingPkg == null) return;
        if (root.getPackageName() == null || !pendingPkg.equals(root.getPackageName().toString())) return;
        List<String> found = new ArrayList<>();
        collect(root, found, 0);
        String app = Engine.APPS.containsKey(pendingPkg) ? Engine.APPS.get(pendingPkg) : pendingPkg;
        int warned = 0;
        for (String t : found) {
            if (warned >= 2) break; // tối đa 2 cảnh báo mỗi lần quét để không làm phiền
            if (Engine.check(this, t, app)) warned++;
        }
    }

    private void collect(AccessibilityNodeInfo n, List<String> out, int depth) {
        if (n == null || depth > 40 || out.size() > 80) return;
        if (n.isPassword()) return;
        if (n.isVisibleToUser()) {
            CharSequence t = n.getText();
            if (t != null && t.length() >= 12) {
                Rect r = new Rect();
                n.getBoundsInScreen(r);
                if (r.height() > 0) out.add(t.toString());
            }
        }
        for (int i = 0; i < n.getChildCount(); i++) collect(n.getChild(i), out, depth + 1);
    }

    @Override public void onInterrupt() { h.removeCallbacks(scan); }
}

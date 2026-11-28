package vn.edushield.app;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import vn.edushield.core.EduShieldCore;

/** Dùng chung: nạp mô hình (một lần), cài đặt của học sinh, thông báo cảnh báo và nhật ký (chỉ loại nguy cơ, không có nội dung). */
public final class Engine {
    public static final String CH_ALERT = "alerts", CH_DRILL = "drill";
    /** Ứng dụng chat, mạng xã hội có thể theo dõi (học sinh tự chọn). */
    public static final LinkedHashMap<String, String> APPS = new LinkedHashMap<>();
    static {
        APPS.put("com.zing.zalo", "Zalo");
        APPS.put("com.facebook.orca", "Messenger");
        APPS.put("com.facebook.katana", "Facebook");
        APPS.put("com.facebook.lite", "Facebook Lite");
        APPS.put("com.instagram.android", "Instagram");
        APPS.put("com.zhiliaoapp.musically", "TikTok");
        APPS.put("com.ss.android.ugc.trill", "TikTok (bản khác)");
        APPS.put("org.telegram.messenger", "Telegram");
        APPS.put("com.google.android.apps.messaging", "Tin nhắn (Google)");
        APPS.put("com.samsung.android.messaging", "Tin nhắn (Samsung)");
        APPS.put("com.discord", "Discord");
    }
    private static EduShieldCore core;

    public static synchronized EduShieldCore core(Context c) {
        if (core == null) {
            core = new EduShieldCore(asset(c, "model.json"), asset(c, "ui.json"), asset(c, "blocklist.json"));
        }
        return core;
    }

    static String asset(Context c, String name) {
        try (InputStream in = c.getAssets().open(name)) {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            byte[] buf = new byte[65536];
            int n;
            while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
            return new String(out.toByteArray(), StandardCharsets.UTF_8);
        } catch (Exception e) {
            throw new RuntimeException("Không đọc được " + name, e);
        }
    }

    public static SharedPreferences prefs(Context c) { return c.getSharedPreferences("edushield", Context.MODE_PRIVATE); }

    public static boolean consented(Context c) { return prefs(c).getBoolean("consent", false); }

    public static Set<String> watched(Context c) {
        Set<String> def = new HashSet<>(Arrays.asList("com.zing.zalo", "com.facebook.orca", "com.facebook.katana", "com.google.android.apps.messaging"));
        return new HashSet<>(prefs(c).getStringSet("apps", def));
    }

    public static String sens(Context c) { return prefs(c).getString("sens", "can_bang"); }

    public static void channels(Context c) {
        NotificationManager nm = c.getSystemService(NotificationManager.class);
        NotificationChannel a = new NotificationChannel(CH_ALERT, "Cảnh báo nguy cơ", NotificationManager.IMPORTANCE_HIGH);
        a.setDescription("Chỉ hiện loại nguy cơ, không hiện nội dung tin nhắn");
        nm.createNotificationChannel(a);
        nm.createNotificationChannel(new NotificationChannel(CH_DRILL, "Thực chiến giả lập", NotificationManager.IMPORTANCE_DEFAULT));
    }

    /** Hiện cảnh báo. Thông báo chỉ có LOẠI nguy cơ; nội dung chỉ nằm trong ý định mở màn hình kết quả, trên chính máy này. */
    public static void alert(Context c, String text, EduShieldCore.Result r, String app) {
        channels(c);
        Intent i = new Intent(c, ResultActivity.class).putExtra("text", text).putExtra("app", app)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent pi = PendingIntent.getActivity(c, (int) (System.currentTimeMillis() & 0xffff), i,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        String icon = "khan_cap".equals(r.level) ? "🚨 " : "canh_bao".equals(r.level) ? "⚠️ " : "💡 ";
        Notification n = new Notification.Builder(c, CH_ALERT)
                .setSmallIcon(R.drawable.ic_shield)
                .setContentTitle(icon + r.catVi)
                .setContentText("Tin trong " + app + " có dấu hiệu nguy cơ. Chạm để xem việc nên làm, bạn là người quyết định.")
                .setStyle(new Notification.BigTextStyle().bigText("Tin trong " + app + " có dấu hiệu: " + String.join(", ", r.reasons)
                        + ". Chạm để xem việc nên làm. Mô hình có thể sai, bạn là người quyết định."))
                .setContentIntent(pi).setAutoCancel(true).build();
        NotificationManager nm = c.getSystemService(NotificationManager.class);
        try { nm.notify((int) (System.currentTimeMillis() % 100000), n); } catch (SecurityException e) { /* chưa cấp quyền thông báo */ }
        log(c, r.catVi + " · " + app);
    }

    /** Nhật ký: chỉ thời gian, loại nguy cơ, ứng dụng. Không bao giờ lưu nội dung tin nhắn. */
    public static void log(Context c, String what) {
        SharedPreferences p = prefs(c);
        List<String> L = new ArrayList<>(Arrays.asList(p.getString("log", "").split("\n")));
        L.removeIf(String::isEmpty);
        L.add(0, android.text.format.DateFormat.format("dd/MM HH:mm", System.currentTimeMillis()) + " · " + what);
        while (L.size() > 30) L.remove(L.size() - 1);
        p.edit().putString("log", String.join("\n", L)).apply();
    }

    /** Chống báo trùng: nhớ mã băm của những đoạn đã phân tích gần đây (chỉ mã băm, không nhớ nội dung). */
    private static final Map<Integer, Long> SEEN = new LinkedHashMap<Integer, Long>(256, 0.75f, true) {
        @Override protected boolean removeEldestEntry(Map.Entry<Integer, Long> e) { return size() > 400; }
    };

    public static synchronized boolean firstTime(String text) {
        int h = text.hashCode();
        if (SEEN.containsKey(h)) return false;
        SEEN.put(h, System.currentTimeMillis());
        return true;
    }

    /** Phân tích và cảnh báo nếu cần. Trả về true nếu đã cảnh báo. */
    public static boolean check(Context c, String text, String app) {
        if (text == null) return false;
        text = text.trim();
        if (text.length() < 12 || text.length() > 2000 || !firstTime(text)) return false;
        EduShieldCore.Result r = core(c).analyze(text, sens(c));
        if (r.warn) { alert(c, text, r, app); return true; }
        return false;
    }
}

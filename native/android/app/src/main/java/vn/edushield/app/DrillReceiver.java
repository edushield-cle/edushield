package vn.edushield.app;

import android.app.AlarmManager;
import android.app.Notification;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** Hẹn giờ và hiện "tin nhắn mới" của bài diễn tập. Thông báo luôn mang tên EduShield, không giả làm ứng dụng khác. */
public class DrillReceiver extends BroadcastReceiver {
    static PendingIntent alarmIntent(Context c) {
        return PendingIntent.getBroadcast(c, 7, new Intent(c, DrillReceiver.class), PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }

    static void schedule(Context c, long when) {
        AlarmManager am = c.getSystemService(AlarmManager.class);
        if (am == null) return;
        am.cancel(alarmIntent(c));
        if (when > System.currentTimeMillis()) am.set(AlarmManager.RTC_WAKEUP, when, alarmIntent(c)); // không cần giờ chính xác
    }

    @Override public void onReceive(Context c, Intent intent) {
        Engine.channels(c);
        Intent open = new Intent(c, DrillActivity.class).putExtra("auto", true).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        PendingIntent pi = PendingIntent.getActivity(c, 8, open, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Notification n = new Notification.Builder(c, Engine.CH_DRILL)
                .setSmallIcon(R.drawable.ic_shield)
                .setContentTitle("📩 Bạn có một tin nhắn mới")
                .setContentText("Chạm để xem và phản hồi.")
                .setContentIntent(pi).setAutoCancel(true).build();
        try { c.getSystemService(NotificationManager.class).notify(4242, n); } catch (SecurityException ignored) { }
    }
}

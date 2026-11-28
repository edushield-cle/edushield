package vn.edushield.app;

import android.app.PendingIntent;
import android.content.Intent;
import android.os.Build;
import android.service.quicksettings.TileService;

/** Ô trong bảng Cài đặt nhanh: một chạm để kiểm tra tin vừa sao chép. */
public class ClipboardTileService extends TileService {
    @Override public void onClick() {
        Intent i = new Intent(this, ClipboardActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        if (Build.VERSION.SDK_INT >= 34) {
            startActivityAndCollapse(PendingIntent.getActivity(this, 0, i, PendingIntent.FLAG_IMMUTABLE));
        } else {
            startActivityAndCollapse(i);
        }
    }
}

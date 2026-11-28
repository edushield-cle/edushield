package vn.edushield.app;

import android.content.Context;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

/** Giao diện dựng bằng mã (không cần tệp bố cục) để dự án gọn, dễ đọc. */
final class Ui {
    static int dp(Context c, int v) { return Math.round(v * c.getResources().getDisplayMetrics().density); }

    static LinearLayout col(Context c) {
        LinearLayout l = new LinearLayout(c);
        l.setOrientation(LinearLayout.VERTICAL);
        int p = dp(c, 14);
        l.setPadding(p, p, p, p);
        return l;
    }

    static LinearLayout card(Context c) {
        LinearLayout l = col(c);
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(Color.WHITE); bg.setCornerRadius(dp(c, 14)); bg.setStroke(dp(c, 1), Color.parseColor("#D0D7DE"));
        l.setBackground(bg);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        lp.setMargins(0, 0, 0, dp(c, 12));
        l.setLayoutParams(lp);
        return l;
    }

    static TextView title(Context c, String s) {
        TextView t = text(c, s, 17);
        t.setTypeface(Typeface.DEFAULT_BOLD);
        return t;
    }

    static TextView text(Context c, String s, int sp) {
        TextView t = new TextView(c);
        t.setText(s); t.setTextSize(sp); t.setTextColor(Color.parseColor("#1F2328"));
        t.setPadding(0, dp(c, 4), 0, dp(c, 4));
        return t;
    }

    static TextView small(Context c, String s) {
        TextView t = text(c, s, 14);
        t.setTextColor(Color.parseColor("#57606A"));
        return t;
    }

    static Button button(Context c, String s, View.OnClickListener on) {
        Button b = new Button(c);
        b.setText(s); b.setAllCaps(false); b.setOnClickListener(on);
        return b;
    }
}

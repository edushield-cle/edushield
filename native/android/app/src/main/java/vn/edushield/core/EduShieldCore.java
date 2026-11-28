package vn.edushield.core;

import java.text.Normalizer;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Lõi phát hiện của EduShield cho ứng dụng Android: dịch 1-1 từ extension/detector.js,
 * đọc CÙNG tệp mô hình (model.json) nên cho kết quả giống hệt tiện ích trình duyệt
 * (kiểm chứng bằng native/tools/CoreTest.java). Mọi phép tính chạy trên máy, không gửi dữ liệu đi đâu.
 */
public final class EduShieldCore {
    public static final class Result {
        public String label, labelVi, level = "an_toan", cat = "", catVi = "", frame = "";
        public double p;
        public double[] probs;
        public boolean warn;
        public int sev;
        public final List<String> reasons = new ArrayList<>();
        public List<String> todo = new ArrayList<>();
    }

    private static final class Signal {
        String label, desc, cat; Pattern re; int sev; boolean isUrl;
    }

    private final String[] classes;
    private final double[] intercept;
    private final Map<String, double[]> weights = new HashMap<>();
    private final Pattern rxUrl, rxPhone, rxNum, rxQuote, rxDirect, rxAct, rxQspan;
    private final List<String> frameNames = new ArrayList<>();
    private final List<Pattern> frameRx = new ArrayList<>();
    private final List<Signal> signals = new ArrayList<>();
    private final double pWarn, pWarnSignal; private final int sevSignal;
    private final String[] fineClasses; private final double[] fineIntercept;
    private final Map<String, double[]> fineWeights = new HashMap<>();
    private final List<String> allowDomains = new ArrayList<>(), allowSuffixes = new ArrayList<>();
    private final Map<String, Object> ui;

    @SuppressWarnings("unchecked")
    public EduShieldCore(String modelJson, String uiJson, String blocklistJson) {
        Map<String, Object> m = (Map<String, Object>) MiniJson.parse(modelJson);
        ui = (Map<String, Object>) MiniJson.parse(uiJson);
        classes = toStrings((List<Object>) m.get("classes"));
        intercept = toDoubles((List<Object>) m.get("intercept"));
        for (Map.Entry<String, Object> e : ((Map<String, Object>) m.get("weights")).entrySet())
            weights.put(e.getKey(), toDoubles((List<Object>) e.getValue()));
        Map<String, Object> rx = (Map<String, Object>) m.get("regex");
        rxUrl = Pattern.compile((String) rx.get("url"));
        rxPhone = Pattern.compile((String) rx.get("phone"));
        rxNum = Pattern.compile((String) rx.get("num"));
        for (Object o : (List<Object>) m.get("frame")) {
            List<Object> f = (List<Object>) o;
            frameNames.add((String) f.get(0)); frameRx.add(Pattern.compile((String) f.get(1)));
        }
        rxQuote = m.get("quote") != null ? Pattern.compile((String) m.get("quote")) : null;
        rxDirect = m.get("direct") != null ? Pattern.compile((String) m.get("direct")) : null;
        rxAct = m.get("act") != null ? Pattern.compile((String) m.get("act")) : null;
        rxQspan = m.get("qspan") != null ? Pattern.compile((String) m.get("qspan")) : null;
        for (Object o : (List<Object>) m.get("signals")) {
            List<Object> a = (List<Object>) o;
            Signal s = new Signal();
            s.label = (String) a.get(0); s.re = Pattern.compile((String) a.get(1)); s.desc = (String) a.get(2);
            s.sev = ((Double) a.get(3)).intValue(); s.cat = (String) a.get(4); s.isUrl = "urltoken".equals(a.get(1));
            signals.add(s);
        }
        Map<String, Object> rule = (Map<String, Object>) m.get("rule");
        pWarn = (Double) rule.get("p_warn"); pWarnSignal = (Double) rule.get("p_warn_with_signal");
        sevSignal = ((Double) rule.get("sev_signal")).intValue();
        Map<String, Object> fine = (Map<String, Object>) m.get("fine");
        fineClasses = toStrings((List<Object>) fine.get("classes"));
        fineIntercept = toDoubles((List<Object>) fine.get("intercept"));
        for (Map.Entry<String, Object> e : ((Map<String, Object>) fine.get("weights")).entrySet())
            fineWeights.put(e.getKey(), toDoubles((List<Object>) e.getValue()));
        if (blocklistJson != null) {
            Map<String, Object> bl = (Map<String, Object>) MiniJson.parse(blocklistJson);
            Map<String, Object> al = (Map<String, Object>) bl.get("allow");
            if (al != null) {
                for (Object d : (List<Object>) al.get("domains")) allowDomains.add((String) d);
                for (Object d : (List<Object>) al.get("suffixes")) allowSuffixes.add((String) d);
            }
        }
    }

    private static String[] toStrings(List<Object> a) { String[] r = new String[a.size()]; for (int k = 0; k < r.length; k++) r[k] = (String) a.get(k); return r; }
    private static double[] toDoubles(List<Object> a) { double[] r = new double[a.size()]; for (int k = 0; k < r.length; k++) r[k] = (Double) a.get(k); return r; }

    // ---------- chuẩn hoá: giống hàm norm() của detector.js ----------
    static String strip(String s) {
        s = s.replace('đ', 'd').replace('Đ', 'D');
        s = Normalizer.normalize(s, Normalizer.Form.NFD);
        StringBuilder b = new StringBuilder(s.length());
        for (int k = 0; k < s.length(); k++) { char c = s.charAt(k); if (c < '̀' || c > 'ͯ') b.append(c); }
        return b.toString();
    }

    private static String hostOf(String u) {
        String h = u.toLowerCase().replaceFirst("^https?://", "").replaceFirst("^www\\.", "").split("[/?#]", -1)[0];
        return h.replaceFirst("[.,;:!)]+$", "");
    }

    private boolean trustedHost(String h) {
        for (String s : allowSuffixes) if (h.endsWith(s)) return true;
        for (String d : allowDomains) if (h.equals(d) || h.endsWith("." + d)) return true;
        return false;
    }

    public String norm(String t) {
        t = strip(t).toLowerCase();
        Matcher mu = rxUrl.matcher(t);
        boolean any = false, all = true;
        while (mu.find()) { any = true; if (!trustedHost(hostOf(mu.group()))) all = false; }
        String tok = any && all ? " linkoktoken " : " urltoken ";
        t = rxUrl.matcher(t).replaceAll(Matcher.quoteReplacement(tok));
        t = rxPhone.matcher(t).replaceAll(" phonetoken ");
        t = rxNum.matcher(t).replaceAll(" numtoken ");
        t = t.replaceAll("[^a-z0-9]+", " ").trim();
        return t.isEmpty() ? "" : String.join(" ", t.split("\\s+"));
    }

    private Set<String> feats(String n, String text) {
        Set<String> s = new LinkedHashSet<>();
        String[] toks = n.isEmpty() ? new String[0] : n.split(" ");
        s.addAll(Arrays.asList(toks));
        for (int k = 0; k + 1 < toks.length; k++) s.add(toks[k] + " " + toks[k + 1]);
        for (int k = 0; k < frameRx.size(); k++) if (frameRx.get(k).matcher(n).find()) s.add(frameNames.get(k));
        if (rxQuote != null && text != null) {
            Matcher q = rxQuote.matcher(text); int c = 0;
            while (q.find()) c++;
            if (c >= 2) s.add("__trich");
        }
        return s;
    }

    private static double[] softmax(double[] z) {
        double mx = Double.NEGATIVE_INFINITY; for (double v : z) mx = Math.max(mx, v);
        double sum = 0; double[] e = new double[z.length];
        for (int k = 0; k < z.length; k++) { e[k] = Math.exp(z[k] - mx); sum += e[k]; }
        for (int k = 0; k < z.length; k++) e[k] /= sum;
        return e;
    }

    public double[] predict(String n, String text) {
        double[] z = intercept.clone();
        for (String f : feats(n, text)) { double[] w = weights.get(f); if (w != null) for (int c = 0; c < z.length; c++) z[c] += w[c]; }
        return softmax(z);
    }

    private int idx(String c) { for (int k = 0; k < classes.length; k++) if (classes[k].equals(c)) return k; return -1; }

    private List<String> fineCats(String n, String label, String text) {
        String pre = "lua_dao".equals(label) ? "ld_" : "bn_";
        List<Integer> ids = new ArrayList<>();
        for (int k = 0; k < fineClasses.length; k++) if (fineClasses[k].startsWith(pre)) ids.add(k);
        double[] z = fineIntercept.clone();
        for (String f : feats(n, text)) { double[] w = fineWeights.get(f); if (w != null) for (int k = 0; k < z.length; k++) z[k] += w[k]; }
        double mx = Double.NEGATIVE_INFINITY; for (int k : ids) mx = Math.max(mx, z[k]);
        double sum = 0; double[] e = new double[ids.size()];
        for (int j = 0; j < ids.size(); j++) { e[j] = Math.exp(z[ids.get(j)] - mx); sum += e[j]; }
        Integer[] order = new Integer[ids.size()];
        for (int j = 0; j < order.length; j++) { order[j] = j; e[j] /= sum; }
        final double[] ee = e;
        Arrays.sort(order, (a, b) -> Double.compare(ee[b], ee[a]));
        List<String> out = new ArrayList<>();
        for (int r = 0; r < order.length && out.size() < 2; r++) {
            double p = e[order[r]];
            if (r == 0 ? p >= 0.4 : p >= 0.3) out.add(fineClasses[ids.get(order[r])]);
        }
        if (out.isEmpty()) out.add("lua_dao".equals(label) ? "ld_khac" : "bn_khac");
        return out;
    }

    @SuppressWarnings("unchecked")
    private String uiStr(String table, String key) {
        Object t = ui.get(table);
        if (!(t instanceof Map)) return null;
        Object v = ((Map<String, Object>) t).get(key);
        return v instanceof String ? (String) v : null;
    }

    @SuppressWarnings("unchecked")
    private List<String> uiList(String table, String key) {
        Object t = ui.get(table);
        if (!(t instanceof Map)) return null;
        Object v = ((Map<String, Object>) t).get(key);
        if (!(v instanceof List)) return null;
        List<String> r = new ArrayList<>(); for (Object o : (List<Object>) v) r.add((String) o); return r;
    }

    private boolean isHarm(String l) { return "bat_nat".equals(l) || "lua_dao".equals(l); }

    /** Phân tích một đoạn chữ. sens: "it" | "can_bang" | "nhay" (độ nhạy do học sinh chọn). */
    public Result analyze(String text, String sens) {
        Result r = new Result();
        String n = norm(text);
        double[] probs = predict(n, text);
        int ci = 0; for (int c = 1; c < probs.length; c++) if (probs[c] > probs[ci]) ci = c;
        String label = classes[ci]; double p = probs[ci];
        boolean override = false;
        if ("tuyen_truyen".equals(label) && rxDirect != null && rxAct != null) {
            String nq = rxQspan != null ? norm(rxQspan.matcher(text).replaceAll(" ")) : n;
            int neg = frameNames.indexOf("__phu_dinh");
            if (rxDirect.matcher(nq).find() && rxAct.matcher(nq).find() && !(neg >= 0 && frameRx.get(neg).matcher(nq).find())) {
                String hl = probs[idx("lua_dao")] > probs[idx("bat_nat")] ? "lua_dao" : "bat_nat";
                label = hl; p = probs[idx(hl)]; override = true;
            }
        }
        int sev = 0; Set<String> cats = new LinkedHashSet<>();
        if (isHarm(label)) {
            sev = 1;
            for (Signal s : signals) {
                if (s.label.equals(label) && s.re.matcher(n).find()) {
                    r.reasons.add(s.desc); sev = Math.max(sev, s.sev); if (s.cat != null) cats.add(s.cat);
                }
            }
        }
        double dl = "it".equals(sens) ? 0.15 : "nhay".equals(sens) ? -0.15 : 0;
        boolean warn = isHarm(label) && (override || p >= pWarn + dl || (p >= pWarnSignal + dl && sev >= sevSignal));
        r.label = label; r.p = p; r.probs = probs; r.sev = sev; r.warn = warn;
        r.labelVi = uiStr("VI", label);
        r.level = !warn ? "an_toan" : sev >= 4 ? "khan_cap" : (p >= 0.85 || sev >= 3) ? "canh_bao" : "luu_y";
        r.frame = "tuyen_truyen".equals(label) ? "tuyen_truyen" : "";
        if (warn) {
            List<String> fine = fineCats(n, label, text);
            String main = cats.isEmpty() ? fine.get(0) : cats.iterator().next();
            r.cat = main;
            String cv = uiStr("CAT_VI", main);
            r.catVi = cv != null ? cv : r.labelVi;
            List<String> td = uiList("TODO_CAT", main);
            r.todo = td != null ? td : uiList("TODO", label);
            if (r.reasons.isEmpty()) r.reasons.add("Giống các mẫu nguy cơ mô hình đã học");
        }
        return r;
    }

    public String getHelpMessage() { Object h = ui.get("HELP_MSG"); return h instanceof String ? (String) h : ""; }
}

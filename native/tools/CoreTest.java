import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import vn.edushield.core.EduShieldCore;
import vn.edushield.core.MiniJson;

/** Kiểm tra lõi Java cho kết quả giống bản JavaScript (tiện ích). Chạy: xem native/README.md */
public class CoreTest {
    static String read(String p) throws Exception { return new String(Files.readAllBytes(Path.of(p)), StandardCharsets.UTF_8); }

    @SuppressWarnings("unchecked")
    public static void main(String[] a) throws Exception {
        String root = a.length > 0 ? a[0] : ".";
        String as = root + "/native/android/app/src/main/assets/";
        long t0 = System.nanoTime();
        EduShieldCore core = new EduShieldCore(read(as + "model.json"), read(as + "ui.json"), read(as + "blocklist.json"));
        long tLoad = System.nanoTime() - t0;
        List<Object> exp = (List<Object>) MiniJson.parse(read(root + "/native/tools/core_expected.json"));
        int normBad = 0, labelBad = 0, warnBad = 0, levelBad = 0, catBad = 0; double maxDiff = 0;
        t0 = System.nanoTime();
        for (Object o : exp) {
            Map<String, Object> e = (Map<String, Object>) o;
            String text = (String) e.get("text");
            if (!core.norm(text).equals(e.get("norm"))) { normBad++; if (normBad < 4) System.out.println("Lệch chuẩn hoá: " + text + "\n  java: " + core.norm(text) + "\n  js:   " + e.get("norm")); }
            EduShieldCore.Result r = core.analyze(text, "can_bang");
            List<Object> pj = (List<Object>) e.get("probs");
            for (int k = 0; k < pj.size(); k++) maxDiff = Math.max(maxDiff, Math.abs(r.probs[k] - (Double) pj.get(k)));
            if (!r.label.equals(e.get("label"))) labelBad++;
            if (r.warn != (Boolean) e.get("warn")) warnBad++;
            if (!r.level.equals(e.get("level"))) levelBad++;
            if (!r.cat.equals(e.get("cat"))) { catBad++; if (catBad < 4) System.out.println("Lệch nhóm: " + text + " java=" + r.cat + " js=" + e.get("cat")); }
        }
        double ms = (System.nanoTime() - t0) / 1e6 / exp.size();
        System.out.printf("So khớp %d mẫu: lệch chuẩn hoá %d, lệch nhãn %d, lệch cảnh báo %d, lệch mức %d, lệch nhóm %d, sai lệch xác suất lớn nhất %.4f%n",
            exp.size(), normBad, labelBad, warnBad, levelBad, catBad, maxDiff);
        System.out.printf("Nạp mô hình %.0f ms; phân tích trung bình %.3f ms/tin (JVM máy tính)%n", tLoad / 1e6, ms);
        EduShieldCore.Result r = core.analyze("Cô chủ nhiệm đây, em chuyển gấp 500k tiền học phí vào stk 190355667788 nhé", "can_bang");
        System.out.println("Ví dụ: " + r.level + " | " + r.catVi + " | " + r.reasons + " | " + r.todo.get(0));
        if (normBad + labelBad + warnBad + levelBad + catBad > 0 || maxDiff > 0.002) { System.out.println("THẤT BẠI"); System.exit(1); }
        System.out.println("OK");
    }
}

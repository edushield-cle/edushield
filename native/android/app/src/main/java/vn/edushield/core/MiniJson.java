package vn.edushield.core;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Bộ đọc JSON tối giản (không cần thư viện ngoài) để lõi EduShield chạy được cả trên Android lẫn máy tính khi kiểm thử. */
public final class MiniJson {
    private final String s;
    private int i;

    private MiniJson(String s) { this.s = s; }

    public static Object parse(String text) {
        MiniJson p = new MiniJson(text);
        p.ws();
        Object v = p.value();
        p.ws();
        if (p.i != p.s.length()) throw new IllegalArgumentException("JSON thừa ký tự ở vị trí " + p.i);
        return v;
    }

    private void ws() { while (i < s.length() && Character.isWhitespace(s.charAt(i))) i++; }

    private Object value() {
        char c = s.charAt(i);
        if (c == '{') return object();
        if (c == '[') return array();
        if (c == '"') return string();
        if (s.startsWith("true", i)) { i += 4; return Boolean.TRUE; }
        if (s.startsWith("false", i)) { i += 5; return Boolean.FALSE; }
        if (s.startsWith("null", i)) { i += 4; return null; }
        return number();
    }

    private Map<String, Object> object() {
        Map<String, Object> m = new LinkedHashMap<>();
        i++; ws();
        if (s.charAt(i) == '}') { i++; return m; }
        while (true) {
            ws(); String k = string(); ws();
            if (s.charAt(i) != ':') throw new IllegalArgumentException("Thiếu ':' ở vị trí " + i);
            i++; ws();
            m.put(k, value()); ws();
            char c = s.charAt(i++);
            if (c == '}') return m;
            if (c != ',') throw new IllegalArgumentException("Thiếu ',' ở vị trí " + (i - 1));
        }
    }

    private List<Object> array() {
        List<Object> a = new ArrayList<>();
        i++; ws();
        if (s.charAt(i) == ']') { i++; return a; }
        while (true) {
            ws(); a.add(value()); ws();
            char c = s.charAt(i++);
            if (c == ']') return a;
            if (c != ',') throw new IllegalArgumentException("Thiếu ',' trong mảng ở vị trí " + (i - 1));
        }
    }

    private String string() {
        StringBuilder b = new StringBuilder();
        i++;
        while (true) {
            char c = s.charAt(i++);
            if (c == '"') return b.toString();
            if (c != '\\') { b.append(c); continue; }
            char e = s.charAt(i++);
            switch (e) {
                case 'n': b.append('\n'); break;
                case 't': b.append('\t'); break;
                case 'r': b.append('\r'); break;
                case 'b': b.append('\b'); break;
                case 'f': b.append('\f'); break;
                case 'u': b.append((char) Integer.parseInt(s.substring(i, i + 4), 16)); i += 4; break;
                default: b.append(e);
            }
        }
    }

    private Double number() {
        int st = i;
        while (i < s.length() && "+-0123456789.eE".indexOf(s.charAt(i)) >= 0) i++;
        return Double.parseDouble(s.substring(st, i));
    }
}

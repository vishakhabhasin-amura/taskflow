package com.taskflow;

import java.util.LinkedHashMap;
import java.util.Map;

/** Minimal JSON support for TaskFlow's flat, fixed-shape request/response bodies. */
final class Json {
    private Json() {}

    static String escape(String s) {
        StringBuilder sb = new StringBuilder();
        for (char c : s.toCharArray()) {
            switch (c) {
                case '"': sb.append("\\\""); break;
                case '\\': sb.append("\\\\"); break;
                case '\n': sb.append("\\n"); break;
                default: sb.append(c);
            }
        }
        return sb.toString();
    }

    /** Parses a single flat JSON object (string/number/boolean/null values only). */
    static Map<String, Object> parseObject(String json) {
        Map<String, Object> result = new LinkedHashMap<>();
        String body = json == null ? "" : json.trim();
        if (body.length() < 2) return result;
        body = body.substring(1, body.length() - 1); // strip { }
        int i = 0;
        int n = body.length();
        while (i < n) {
            while (i < n && (body.charAt(i) == ' ' || body.charAt(i) == ',' || body.charAt(i) == '\n')) i++;
            if (i >= n) break;
            int keyStart = body.indexOf('"', i) + 1;
            int keyEnd = body.indexOf('"', keyStart);
            String key = body.substring(keyStart, keyEnd);
            i = body.indexOf(':', keyEnd) + 1;
            while (i < n && body.charAt(i) == ' ') i++;
            Object value;
            if (body.charAt(i) == '"') {
                int valStart = i + 1;
                int valEnd = body.indexOf('"', valStart);
                value = body.substring(valStart, valEnd);
                i = valEnd + 1;
            } else {
                int valEnd = i;
                while (valEnd < n && body.charAt(valEnd) != ',') valEnd++;
                String raw = body.substring(i, valEnd).trim();
                if (raw.equals("true")) value = Boolean.TRUE;
                else if (raw.equals("false")) value = Boolean.FALSE;
                else if (raw.equals("null")) value = null;
                else value = Integer.parseInt(raw);
                i = valEnd;
            }
            result.put(key, value);
        }
        return result;
    }
}

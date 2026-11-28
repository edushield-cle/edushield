"""Hợp nhất điểm văn bản (LLM / mô hình cục bộ) và điểm đồ thị thành mức cảnh báo.

Nguyên tắc "con người quyết định": hệ thống chỉ đưa ra MỨC CẢNH BÁO và lời khuyên.
Khi không chắc chắn, kết quả là "cần người xem xét", không tự kết luận.
"""

LEVELS = ["an_toan", "luu_y", "canh_bao", "khan_cap"]
LEVEL_VI = {"an_toan": "An toàn", "luu_y": "Cần lưu ý", "canh_bao": "Cảnh báo", "khan_cap": "Khẩn cấp"}


def fuse(text_result: dict, graph_result: dict | None = None, w_graph=0.9) -> dict:
    probs = text_result.get("probs")
    if probs:
        p_harm_text = 1 - probs["binh_thuong"]
    else:
        c = text_result["confidence"]
        p_harm_text = c if text_result["label"] != "binh_thuong" else 1 - c
    g = (graph_result or {}).get("risk", 0.0)
    # noisy-OR: chỉ cần một nguồn chắc chắn là điểm tổng cao
    score = 1 - (1 - p_harm_text) * (1 - w_graph * g)

    label = text_result["label"]
    if label == "binh_thuong" and g >= 0.6:
        label = "lua_dao"  # văn bản trông vô hại nhưng chỉ dấu thuộc chiến dịch đã biết
    sev = text_result.get("severity", 0)

    if score < 0.35:
        level = "an_toan"
    elif score < 0.6:
        level = "luu_y"
    elif sev >= 4 and score >= 0.75:
        level = "khan_cap"
    else:
        level = "canh_bao"

    need_review = 0.35 <= score < 0.75 or text_result["confidence"] < 0.6
    text_reason = text_result.get("reason", "")
    if label != text_result["label"]:  # đồ thị đã nâng mức: bỏ lý do "không thấy dấu hiệu" của văn bản
        text_reason = "Nội dung chữ trông bình thường, nhưng link hoặc số liên lạc trong tin nhắn đã bị báo cáo"
    reasons = [text_reason] + (graph_result or {}).get("why", [])
    return {
        "label": label, "score": round(score, 3), "level": level, "level_vi": LEVEL_VI[level],
        "need_human_review": bool(need_review and level != "an_toan"),
        "reasons": [r for r in reasons if r],
        "p_text": round(p_harm_text, 3), "p_graph": round(g, 3),
    }

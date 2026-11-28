"""Luồng xử lý đầy đủ cho MỘT tin nhắn: che PII -> LLM/mô hình cục bộ -> Graph -> hợp nhất."""
from fusion import fuse
from graph_module import ReportGraph, simulate_reports
from llm_client import ADVICE_FALLBACK, analyze
from pii import hash_id, mask_pii
from text_model import train_default


class EduShield:
    def __init__(self, demo_graph=True, seed=7):
        self.model = train_default()
        self.graph = ReportGraph()
        self.demo_truth = None
        if demo_graph:  # nạp sẵn báo cáo MÔ PHỎNG để demo, không phải dữ liệu thật
            reports, self.demo_truth = simulate_reports(seed=seed)
            self.graph.add_reports(reports)
        self.graph.build()

    def check(self, text: str) -> dict:
        m = mask_pii(text)
        text_res = analyze(text, self.model)
        graph_res = self.graph.indicator_risk(m["indicators"])
        final = fuse(text_res, graph_res)
        if final["label"] != text_res["label"]:
            text_res["advice"] = ADVICE_FALLBACK[final["label"]]
        return {"masked": m["masked"], "pii_counts": m["counts"], "indicators": m["indicators"],
                "text": text_res, "graph": graph_res, "final": final,
                "advice": text_res.get("advice", "")}

    def check_masked(self, masked: str, domains: list) -> dict:
        """Dùng cho tiện ích trình duyệt: chỉ nhận văn bản ĐÃ CHE và danh sách tên miền."""
        text_res = analyze(masked, self.model)
        graph_res = self.graph.indicator_risk({"domains": list(domains or [])})
        final = fuse(text_res, graph_res)
        if final["label"] != text_res["label"]:
            text_res["advice"] = ADVICE_FALLBACK[final["label"]]
        return {"masked": masked, "final": final, "advice": text_res.get("advice", ""),
                "source": text_res.get("source"), "note": text_res.get("note", "")}

    def report_masked(self, masked: str, domains: list, label: str):
        if label not in ("bat_nat", "lua_dao", "binh_thuong"):
            label = self.check_masked(masked, domains)["final"]["label"]
        rec = {"sender": hash_id(masked, "acc_"), "target": None, "label": label, "masked_text": masked,
               "indicators": {"domains": list(domains or []), "phones": [], "accounts": []}, "t": 0.0}
        self.graph.add_reports([rec]).build()
        return rec

    def report(self, text: str, result: dict, sender_name: str = "", about_me: bool = False,
               reporter_name: str = "", t: float = 0.0):
        """Lưu báo cáo ẩn danh: CHỈ lưu văn bản đã che và mã băm. Không lưu tên, không lưu bản gốc."""
        rec = {
            "sender": hash_id(sender_name.strip().lower(), "acc_") if sender_name.strip() else hash_id(result["masked"], "acc_"),
            "target": hash_id(reporter_name.strip().lower(), "acc_") if (about_me and reporter_name.strip()) else None,
            "label": result["final"]["label"], "masked_text": result["masked"],
            "indicators": result["indicators"], "t": t,
        }
        self.graph.add_reports([rec]).build()
        return rec

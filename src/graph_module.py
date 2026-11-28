"""Module Graph AI: phát hiện CHIẾN DỊCH lừa đảo và BẮT NẠT TẬP THỂ.

Đồ thị chỉ chứa:
  - nút tài khoản đã băm (acc_xxx), không biết đó là ai;
  - nút chỉ dấu: tên miền, số điện thoại băm, số tài khoản băm;
  - cạnh "tài khoản dùng chỉ dấu" và "hai tài khoản gửi cùng kịch bản".
Không lưu nội dung tin nhắn gốc, không lập hồ sơ cá nhân, không xếp hạng học sinh.
Dữ liệu vào là các BÁO CÁO do học sinh chủ động gửi.
"""
import math
import random
from collections import defaultdict

import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Danh sách tên miền TIN CẬY: không bao giờ bị đưa vào danh sách chặn, dù có bị báo cáo hàng loạt.
# Mục đích: chống bị "đầu độc" (kẻ xấu báo cáo hàng loạt để chặn một trang hợp pháp) và tránh gán nhãn oan cho tổ chức.
# Đây chỉ là VÍ DỤ khởi đầu; nhà trường nên tự bổ sung. Một nguồn duy nhất: export_extension.py xuất danh sách này sang JS.
from trust import TRUSTED_DOMAINS, TRUSTED_SUFFIXES, is_trusted  # noqa: E402,F401
BLOCK_MIN_ACCOUNTS = 3  # một tên miền cần được ít nhất 3 tài khoản ẩn danh khác nhau báo cáo mới bị đưa vào danh sách chặn


class ReportGraph:
    """reports: list dict {sender, target (tuỳ chọn), label, masked_text, indicators, t (giờ)}"""

    def __init__(self, sim_threshold=0.75, min_campaign_accounts=3):
        self.sim_threshold = sim_threshold
        self.min_accounts = min_campaign_accounts
        self.reports = []
        self.G = nx.Graph()
        self.campaigns = []
        self._ind_campaign = {}

    def add_reports(self, reports):
        self.reports.extend(reports)
        return self

    # ---------- xây đồ thị ----------
    def build(self):
        G = nx.Graph()
        for r in self.reports:
            a = r["sender"]
            G.add_node(a, kind="account")
            G.nodes[a].setdefault("n_reports", 0)
            G.nodes[a]["n_reports"] += 1
            G.nodes[a].setdefault("n_scam", 0)
            G.nodes[a]["n_scam"] += int(r["label"] == "lua_dao")
            inds = r.get("indicators", {})
            for kind in ("domains", "phones", "accounts"):
                for ind in inds.get(kind, []):
                    if kind == "domains" and is_trusted(ind):
                        continue
                    node = f"{kind[:3]}:{ind}"
                    G.add_node(node, kind="indicator")
                    G.nodes[node].setdefault("n_scam", 0)
                    G.nodes[node]["n_scam"] += int(r["label"] == "lua_dao")
                    w = G.get_edge_data(a, node, {}).get("weight", 0) + 1
                    G.add_edge(a, node, weight=w, etype="uses")
        # Cạnh "cùng kịch bản": các báo cáo lừa đảo có văn bản (đã che) rất giống nhau
        scam = [r for r in self.reports if r["label"] == "lua_dao" and r.get("masked_text")]
        if len(scam) >= 2:
            X = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5)).fit_transform(
                [r["masked_text"].lower() for r in scam])
            S = cosine_similarity(X)
            for i in range(len(scam)):
                for j in range(i + 1, len(scam)):
                    a, b = scam[i]["sender"], scam[j]["sender"]
                    if a != b and S[i, j] >= self.sim_threshold:
                        G.add_edge(a, b, weight=float(S[i, j]), etype="same_script")
        self.G = G
        self._detect_campaigns()
        return self

    # ---------- phát hiện chiến dịch lừa đảo ----------
    def _detect_campaigns(self):
        self.campaigns, self._ind_campaign = [], {}
        if self.G.number_of_edges() == 0:
            return
        comms = nx.community.louvain_communities(self.G, weight="weight", seed=0)
        for c in comms:
            accs = [n for n in c if self.G.nodes[n]["kind"] == "account"]
            inds = [n for n in c if self.G.nodes[n]["kind"] == "indicator"]
            if len(accs) < self.min_accounts:
                continue
            n_rep = sum(self.G.nodes[a]["n_reports"] for a in accs)
            n_scam = sum(self.G.nodes[a]["n_scam"] for a in accs)
            if n_rep == 0 or n_scam / n_rep < 0.6:
                continue
            cid = len(self.campaigns)
            self.campaigns.append({
                "id": cid, "accounts": sorted(accs), "indicators": sorted(inds),
                "n_reports": n_rep, "scam_ratio": round(n_scam / n_rep, 2),
            })
            for i in inds:
                self._ind_campaign[i] = cid

    # ---------- điểm rủi ro cho tin nhắn mới ----------
    def indicator_risk(self, indicators: dict) -> dict:
        """Rủi ro 0..1 dựa trên các chỉ dấu trong tin nhắn (không dùng danh tính người gửi)."""
        best, why = 0.0, []
        for kind in ("domains", "phones", "accounts"):
            for ind in indicators.get(kind, []):
                if kind == "domains" and is_trusted(ind):
                    why.append(f"Tên miền {ind} thuộc danh sách tin cậy")
                    continue
                node = f"{kind[:3]}:{ind}"
                if node not in self.G:
                    continue
                n_scam = self.G.nodes[node].get("n_scam", 0)
                risk = 1 - math.exp(-0.5 * n_scam)  # 1 báo cáo: 0.39; 3 báo cáo: 0.78
                if node in self._ind_campaign:
                    risk = max(risk, 0.9)
                    why.append(f"Chỉ dấu thuộc chiến dịch lừa đảo #{self._ind_campaign[node]} đã được nhiều bạn báo cáo")
                elif n_scam:
                    why.append(f"Chỉ dấu từng bị báo cáo lừa đảo {n_scam} lần")
                best = max(best, risk)
        return {"risk": round(best, 3), "why": why}

    def risky_domains(self, min_accounts=BLOCK_MIN_ACCOUNTS, overrides=None):
        """Tên miền đủ điều kiện đưa vào danh sách chặn:
        (a) thuộc một chiến dịch đã phát hiện, hoặc (b) được >= min_accounts tài khoản ẩn danh KHÁC NHAU báo cáo lừa đảo.
        Loại bỏ tên miền tin cậy. `overrides` do người kiểm duyệt (thầy cô/tư vấn viên) đặt: {"allow": [...], "deny": [...]}."""
        out = set()
        for c in self.campaigns:
            out |= {i[4:] for i in c["indicators"] if i.startswith("dom:")}
        for n, d in self.G.nodes(data=True):
            if n.startswith("dom:") and d.get("n_scam", 0) >= min_accounts:
                accs = [x for x in self.G.neighbors(n) if self.G.nodes[x]["kind"] == "account"]
                if len(accs) >= min_accounts:
                    out.add(n[4:])
        out = {d for d in out if not is_trusted(d)}
        if overrides:
            out -= {str(x).lower() for x in overrides.get("allow", [])}
            out |= {str(x).lower() for x in overrides.get("deny", []) if not is_trusted(str(x).lower())}
        return sorted(out)

    def domain_evidence(self, domain: str) -> dict:
        """Số tài khoản và số báo cáo liên quan tới một tên miền (cho trang kiểm duyệt)."""
        node = f"dom:{domain}"
        if node not in self.G:
            return {"accounts": 0, "scam_reports": 0}
        accs = [x for x in self.G.neighbors(node) if self.G.nodes[x]["kind"] == "account"]
        return {"accounts": len(accs), "scam_reports": self.G.nodes[node].get("n_scam", 0)}

    def top_indicators(self, k=10):
        """PageRank cá nhân hoá: lan truyền 'nghi ngờ' từ các chỉ dấu đã bị báo cáo."""
        if self.G.number_of_nodes() == 0:
            return []
        pers = {n: float(self.G.nodes[n].get("n_scam", 0)) for n in self.G}
        if sum(pers.values()) == 0:
            return []
        pr = nx.pagerank(self.G, personalization=pers, weight="weight")
        inds = [(n, s) for n, s in pr.items() if self.G.nodes[n]["kind"] == "indicator"]
        return sorted(inds, key=lambda x: -x[1])[:k]

    # ---------- bắt nạt tập thể ----------
    def mob_bullying(self, min_senders=3, window_hours=48):
        """Một người (ẩn danh) bị >= min_senders tài khoản khác nhau nhắm tới trong window_hours.
        Chỉ trả về mã băm của nạn nhân để chuyên viên tư vấn chủ động hỗ trợ, không nêu tên ai."""
        by_target = defaultdict(list)
        for r in self.reports:
            if r["label"] == "bat_nat" and r.get("target"):
                by_target[r["target"]].append((r.get("t", 0), r["sender"]))
        alerts = []
        for tgt, evs in by_target.items():
            evs.sort()
            best, lo = set(), 0
            for hi in range(len(evs)):
                while evs[hi][0] - evs[lo][0] > window_hours:
                    lo += 1
                senders = {s for _, s in evs[lo:hi + 1]}
                if len(senders) > len(best):
                    best = senders
            if len(best) >= min_senders:
                alerts.append({"target": tgt, "n_senders": len(best), "n_messages": len(evs)})
        return sorted(alerts, key=lambda a: -a["n_senders"])

    def summary(self):
        kinds = nx.get_node_attributes(self.G, "kind")
        return {
            "so_bao_cao": len(self.reports),
            "so_tai_khoan_an_danh": sum(1 for k in kinds.values() if k == "account"),
            "so_chi_dau": sum(1 for k in kinds.values() if k == "indicator"),
            "so_chien_dich": len(self.campaigns),
        }


# ---------- dữ liệu đồ thị MÔ PHỎNG có đáp án để đánh giá ----------
def simulate_reports(n_campaigns=5, accounts_per_campaign=6, n_lone_scam=15, n_bully_mobs=3,
                     n_bully_single=20, n_benign=120, seed=7):
    """Trả về (reports, truth). truth chứa đáp án: tài khoản nào thuộc chiến dịch nào,
    nạn nhân nào bị bắt nạt tập thể."""
    from data_gen import OK_DOMAINS, TEMPLATES, _augment, _fill
    from pii import hash_id, mask_pii
    rng = random.Random(seed)
    reports, truth = [], {"campaign_of": {}, "mob_targets": set(), "campaign_domains": {}}
    t = 0.0

    def rep(sender, text, label, target=None):
        nonlocal t
        t += rng.random() * 2
        m = mask_pii(text)
        reports.append({"sender": sender, "target": target, "label": label,
                        "masked_text": m["masked"], "indicators": m["indicators"], "t": t})

    link_tpls = [x for x in TEMPLATES["lua_dao"] if "{link}" in x]
    for c in range(n_campaigns):
        doms = [f"chiendich{c}-{k}.{rng.choice(['xyz', 'top', 'vip', 'club'])}" for k in range(2)]
        truth["campaign_domains"][c] = doms
        tpl = rng.choice(link_tpls)
        for a in range(accounts_per_campaign):
            acc = hash_id(f"camp{c}_acc{a}", "acc_")
            truth["campaign_of"][acc] = c
            for _ in range(rng.randint(2, 4)):
                rep(acc, _augment(_fill(tpl, rng, doms), rng), "lua_dao")
    for i in range(n_lone_scam):  # kẻ lừa đảo đơn lẻ, tên miền riêng
        acc = hash_id(f"lone{i}", "acc_")
        rep(acc, _fill(rng.choice(TEMPLATES["lua_dao"]), rng, [f"le{i}.site"]), "lua_dao")
    for m in range(n_bully_mobs):
        tgt = hash_id(f"victim{m}", "acc_")
        truth["mob_targets"].add(tgt)
        t0 = t
        for s in range(rng.randint(4, 6)):
            acc = hash_id(f"mob{m}_s{s}", "acc_")
            for _ in range(rng.randint(1, 3)):
                rep(acc, _fill(rng.choice(TEMPLATES["bat_nat"]), rng), "bat_nat", tgt)
        t = t0 + 30
    for i in range(n_bully_single):  # xích mích 1-1, không phải tập thể
        rep(hash_id(f"sb{i}", "acc_"), _fill(rng.choice(TEMPLATES["bat_nat"]), rng), "bat_nat",
            hash_id(f"sv{i % 12}", "acc_"))
        t += 60
    for i in range(n_benign):
        rep(hash_id(f"ok{i % 40}", "acc_"), _fill(rng.choice(TEMPLATES["binh_thuong"]), rng), "binh_thuong")
    rng.shuffle(reports)
    return reports, truth


def evaluate_graph(seed=7):
    reports, truth = simulate_reports(seed=seed)
    g = ReportGraph().add_reports(reports).build()
    flagged = {a for c in g.campaigns for a in c["accounts"]}
    true_acc = set(truth["campaign_of"])
    tp = len(flagged & true_acc)
    prec = tp / len(flagged) if flagged else 0.0
    rec = tp / len(true_acc) if true_acc else 0.0
    mobs = {a["target"] for a in g.mob_bullying()}
    mtp = len(mobs & truth["mob_targets"])
    return {
        "campaign_precision": round(prec, 3), "campaign_recall": round(rec, 3),
        "campaigns_found": len(g.campaigns), "campaigns_true": len(truth["campaign_domains"]),
        "mob_precision": round(mtp / len(mobs), 3) if mobs else 0.0,
        "mob_recall": round(mtp / len(truth["mob_targets"]), 3),
        "summary": g.summary(),
    }


if __name__ == "__main__":
    print(evaluate_graph())

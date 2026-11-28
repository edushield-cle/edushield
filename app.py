"""Giao diện demo EduShield AI.  Chạy:  streamlit run app.py"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import streamlit as st

from llm_client import GEMINI_MODEL, llm_available
from pipeline import EduShield
from text_model import LABEL_VI

st.set_page_config(page_title="EduShield AI", page_icon="🛡️", layout="wide")


@st.cache_resource
def get_system():
    return EduShield(demo_graph=True)


sys_ = get_system()
COLORS = {"an_toan": "green", "luu_y": "orange", "canh_bao": "red", "khan_cap": "red"}

st.title("🛡️ EduShield AI")
st.caption("Hệ thống phòng vệ chủ động và cảnh báo sớm nguy cơ lừa đảo trực tuyến, bạo lực mạng cho học sinh ứng dụng học máy đa tầng. "
           "AI chỉ gợi ý, con người quyết định. Dữ liệu demo là dữ liệu mô phỏng.")

tab1, tab2, tab3, tab4 = st.tabs(["Kiểm tra tin nhắn", "Bảng tổng hợp (thầy cô, tư vấn)", "Đồ thị", "Quyền riêng tư và giới hạn"])

with tab1:
    st.subheader("Dán tin nhắn bạn thấy nghi ngờ")
    st.write("Bạn là người chủ động gửi nội dung. Hệ thống không đọc tin nhắn của bạn ở bất kỳ đâu khác.")
    examples = {
        "(tự nhập)": "",
        "Lừa đảo tuyển CTV": "Tuyển CTV chốt đơn tại nhà 500k/ngày không cần cọc, ib zalo 0912345678",
        "Bắt nạt, đe doạ": "mày mà mách cô thì đừng trách tao, tan học tao chờ ở cổng",
        "Bạn bè trêu đùa": "haha thằng quỷ này lại quên trả sách cho tao hả",
        "Mồi ngắn có link chiến dịch": "xem cái này đi https://" + (
            sys_.demo_truth["campaign_domains"][0][0] if sys_.demo_truth else "vidu.xyz") + "/x",
    }
    pick = st.selectbox("Ví dụ mẫu", list(examples))
    text = st.text_area("Nội dung tin nhắn", value=examples[pick], height=120)

    if st.button("Kiểm tra", type="primary") and text.strip():
        st.session_state["last"] = (text, sys_.check(text))

    if "last" in st.session_state:
        text0, res = st.session_state["last"]
        f = res["final"]
        st.markdown(f"### Kết quả: :{COLORS[f['level']]}[{f['level_vi']}] · {LABEL_VI[f['label']]}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Điểm tổng hợp", f["score"])
        c2.metric("Điểm văn bản", f["p_text"])
        c3.metric("Điểm đồ thị", f["p_graph"])
        if f["need_human_review"]:
            st.warning("Hệ thống chưa chắc chắn. Bạn nên nhờ thầy cô hoặc cha mẹ xem giúp tin nhắn này.")
        st.write("**Vì sao?**")
        for r in f["reasons"]:
            st.write("•", r)
        st.info(res["advice"])
        if res["text"].get("note"):
            st.caption(res["text"]["note"])
        with st.expander("Hệ thống đã nhìn thấy gì? (văn bản sau khi che thông tin cá nhân)"):
            st.code(res["masked"])
            st.write("Số thông tin đã che:", res["pii_counts"])

        st.divider()
        st.write("**Báo cáo ẩn danh** (tuỳ chọn). Chỉ lưu văn bản đã che và mã băm, không lưu tên.")
        sender = st.text_input("Tên tài khoản người gửi (sẽ được băm ngay, có thể bỏ trống)")
        about_me = st.checkbox("Tin nhắn này nhắm vào tôi và tôi muốn được phòng tư vấn hỗ trợ")
        nick = st.text_input("Biệt danh của bạn (sẽ được băm, chỉ để nhận biết nhiều báo cáo về cùng một người)") if about_me else ""
        if st.button("Gửi báo cáo ẩn danh"):
            sys_.report(text0, res, sender, about_me, nick, t=time.time() / 3600)
            st.success("Đã ghi nhận. Cảm ơn bạn đã giúp bảo vệ các bạn khác.")

with tab2:
    st.subheader("Thống kê tổng hợp, không hiển thị danh tính")
    s = sys_.graph.summary()
    a, b, c, d = st.columns(4)
    a.metric("Báo cáo", s["so_bao_cao"])
    b.metric("Tài khoản ẩn danh", s["so_tai_khoan_an_danh"])
    c.metric("Chỉ dấu", s["so_chi_dau"])
    d.metric("Chiến dịch lừa đảo", s["so_chien_dich"])
    labels = pd.Series([LABEL_VI[r["label"]] for r in sys_.graph.reports]).value_counts()
    st.bar_chart(labels)
    st.write("**Chiến dịch lừa đảo phát hiện được** (nhiều tài khoản dùng chung link hoặc kịch bản)")
    st.dataframe(pd.DataFrame([{
        "Chiến dịch": c_["id"], "Số tài khoản": len(c_["accounts"]), "Số báo cáo": c_["n_reports"],
        "Chỉ dấu": ", ".join(i.split(":", 1)[1] for i in c_["indicators"] if i.startswith("dom:")),
    } for c_ in sys_.graph.campaigns]), use_container_width=True)
    st.write("**Cảnh báo bắt nạt tập thể** (một bạn bị từ 3 tài khoản trở lên nhắm tới trong 48 giờ)")
    mobs = sys_.graph.mob_bullying()
    if mobs:
        st.dataframe(pd.DataFrame(mobs).rename(columns={
            "target": "Mã ẩn danh của bạn cần hỗ trợ", "n_senders": "Số tài khoản", "n_messages": "Số tin nhắn"}),
            use_container_width=True)
        st.caption("Việc liên hệ hỗ trợ do chuyên viên tư vấn quyết định theo quy trình của trường. Hệ thống không tự xử lý ai.")
    else:
        st.write("Chưa có.")
    st.write("**Chỉ dấu đáng ngờ nhất** (PageRank cá nhân hoá)")
    st.dataframe(pd.DataFrame(sys_.graph.top_indicators(10), columns=["Chỉ dấu", "Điểm"]), use_container_width=True)

with tab3:
    st.subheader("Đồ thị báo cáo (tài khoản đã băm và chỉ dấu)")
    G = sys_.graph.G
    sub = G.subgraph([n for n in G if G.degree(n) > 0])
    if sub.number_of_nodes():
        camp = {n: c_["id"] for c_ in sys_.graph.campaigns for n in c_["accounts"] + c_["indicators"]}
        fig, ax = plt.subplots(figsize=(10, 7))
        pos = nx.spring_layout(sub, seed=1, k=0.6)
        nx.draw_networkx_edges(sub, pos, alpha=0.25, ax=ax)
        nx.draw_networkx_nodes(
            sub, pos, ax=ax, node_size=[160 if sub.nodes[n]["kind"] == "indicator" else 60 for n in sub],
            node_color=[camp.get(n, -1) for n in sub], cmap="tab10",
            node_shape="o")
        nx.draw_networkx_labels(sub, pos, ax=ax, font_size=7,
                                labels={n: n.split(":", 1)[1] for n in sub if n.startswith("dom:")})
        ax.set_axis_off()
        st.pyplot(fig)
        st.caption("Nút lớn: tên miền, số điện thoại hoặc số tài khoản (đã băm). Nút nhỏ: tài khoản ẩn danh. Cùng màu: cùng một chiến dịch.")
    else:
        st.write("Chưa có dữ liệu.")

with tab4:
    st.markdown(f"""
**EduShield làm gì**
- Phân tích tin nhắn do chính học sinh chủ động dán vào.
- Che số điện thoại, số tài khoản, link, tên trước khi phân tích và lưu trữ.
- Chỉ lưu văn bản đã che và mã băm một chiều.
- Đưa ra cảnh báo, lý do và lời khuyên. Quyết định thuộc về học sinh, thầy cô, cha mẹ.

**EduShield không làm gì**
- Không đọc, quét hay theo dõi tin nhắn riêng tư.
- Không lập hồ sơ, không chấm điểm, không xếp hạng học sinh.
- Không tự kết tội hay xử phạt ai.
- Không dùng dữ liệu thật của học sinh để huấn luyện.

**Giới hạn**
- Mô hình được huấn luyện và đánh giá trên dữ liệu tổng hợp; với tin nhắn thật có thể sai.
- Đồ thị chỉ nhận ra chỉ dấu đã từng được báo cáo; chiêu lừa đảo mới hoàn toàn có thể lọt.
- Việc che tên riêng dùng luật đơn giản, có thể sót.

**Trạng thái LLM:** {"đang bật, model " + GEMINI_MODEL if llm_available() else "chưa có khoá API, đang dùng mô hình cục bộ"}

**Cần giúp ngay?** Tổng đài quốc gia bảo vệ trẻ em **111** (miễn phí, 24/7).
""")

"""Kiểm thử nhanh.  Chạy:  python tests/test_basic.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
os.environ.pop("GEMINI_API_KEY", None)  # kiểm thử ở chế độ cục bộ

from llm_client import _parse_json, _validate
from pii import mask_pii
from pipeline import EduShield


def test_pii():
    r = mask_pii("gọi 0912 345 678 hoặc +84912345678, stk 190355667788, vào http://abc.xyz/a, mail a.b@gmail.com")
    m = r["masked"]
    assert "0912" not in m and "1903" not in m and "abc.xyz" not in m and "gmail" not in m, m
    assert r["indicators"]["domains"] == ["abc.xyz"]
    assert len(r["indicators"]["phones"]) == 1  # hai cách viết cùng một số -> cùng mã băm


def test_llm_json():
    ok = _validate(_parse_json('```json\n{"label":"lua_dao","severity":3,"confidence":0.9,"reason":"x","advice":"y"}\n```'))
    assert ok["label"] == "lua_dao"
    for bad in ['{"label":"khac","severity":1,"confidence":0.5}', '{"label":"lua_dao","severity":9,"confidence":0.5}']:
        try:
            _validate(_parse_json(bad))
            raise AssertionError("phải báo lỗi")
        except ValueError:
            pass


def test_pipeline():
    s = EduShield()
    cases = [
        ("Chúc mừng bạn trúng thưởng xe máy điện, bấm http://qua.top/nhan để nhận trong 24h", "lua_dao"),
        ("mày mà mách cô thì đừng trách tao", "bat_nat"),
        ("tối nay call nhóm làm thuyết trình văn lúc 8h", "binh_thuong"),
    ]
    for text, want in cases:
        r = s.check(text)
        assert r["final"]["label"] == want, (text, r["final"])
        assert r["advice"]
    # Mồi ngắn: văn bản vô hại nhưng tên miền thuộc chiến dịch đã bị báo cáo
    dom = s.demo_truth["campaign_domains"][0][0]
    r = s.check(f"coi thử đi https://{dom}/x")
    assert r["final"]["p_graph"] >= 0.6 and r["final"]["level"] in ("canh_bao", "khan_cap"), r["final"]
    # Link trường học không bị cảnh báo
    r = s.check("coi thử đi https://thptmophong.edu.vn/tb")
    assert r["final"]["level"] in ("an_toan", "luu_y"), r["final"]
    # Báo cáo chỉ lưu bản đã che
    res = s.check("thằng Nam số 0912345678 doạ đánh tao")
    rec = s.report("x", res, sender_name="nam123", about_me=True, reporter_name="toi")
    assert "0912345678" not in str(rec) and "nam123" not in str(rec)


def test_privacy_stats():
    import random
    from datetime import date
    from privacy_stats import CAT_CODES, Aggregator, estimate, randomize, validate_packet
    ok = {"school": "THPT_A", "grade": "11", "day": "2026-11-10", "eps": 2.0, "bits": {c: 0 for c in CAT_CODES}}
    validate_packet(ok, today=date(2026, 11, 15))
    for bad in ({**ok, "bits": {"ld_otp": 1}}, {**ok, "school": "x y"}, {**ok, "eps": 9}, {**ok, "day": "2026-12-01"}):
        try:
            validate_packet(bad, today=date(2026, 11, 15)); raise AssertionError("phải từ chối")
        except ValueError:
            pass
    # Gói có trường thừa (vd nội dung tin nhắn) thì trường thừa bị bỏ, không được lưu
    clean = validate_packet({**ok, "noi_dung": "bí mật"}, today=date(2026, 11, 15))
    assert "noi_dung" not in clean
    # Ước lượng không chệch: 2000 học sinh, 10% gặp nguy cơ thật
    rng = random.Random(1)
    n, true_k = 2000, 200
    s = sum(randomize({"x": int(i < true_k)}, 2.0, rng)["x"] for i in range(n))
    e = estimate(n, s, 2.0)
    assert e["lo"] <= true_k <= e["hi"] and abs(e["est"] - true_k) < 60, e
    # Nhóm nhỏ bị ẩn
    agg = Aggregator()
    agg.add(clean, save=False)
    assert agg.report("THPT_A", "day")[0]["hidden"]


if __name__ == "__main__":
    for fn in (test_pii, test_llm_json, test_pipeline, test_privacy_stats):
        fn()
        print("OK", fn.__name__)

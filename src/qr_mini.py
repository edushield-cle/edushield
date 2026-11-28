"""Bộ mã hoá QR tối giản, KHÔNG cần cài thêm thư viện (chỉ dùng thư viện chuẩn của Python).
Chế độ byte (UTF-8), mức sửa lỗi M, phiên bản 1-10 (đủ cho đường link tới khoảng 213 ký tự).
Dùng:  m = encode("https://...")   ->  danh sách các hàng (True = ô đen)
       save_png(m, "qr.png", box=14, border=4)
"""
import struct
import zlib

# (số từ mã tổng, từ mã sửa lỗi mỗi khối, [(số khối, từ mã dữ liệu mỗi khối), ...]) cho mức M
_M = {1: (26, 10, [(1, 16)]), 2: (44, 16, [(1, 28)]), 3: (70, 26, [(1, 44)]), 4: (100, 18, [(2, 32)]), 5: (134, 24, [(2, 43)]),
      6: (172, 16, [(4, 27)]), 7: (196, 18, [(4, 31)]), 8: (242, 22, [(2, 38), (2, 39)]), 9: (292, 22, [(3, 36), (2, 37)]), 10: (346, 26, [(4, 43), (1, 44)])}
_ALIGN = {1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30], 6: [6, 34], 7: [6, 22, 38], 8: [6, 24, 42], 9: [6, 26, 46], 10: [6, 28, 50]}

_EXP, _LOG = [0] * 512, [0] * 256
_x = 1
for _i in range(255):
    _EXP[_i] = _x
    _LOG[_x] = _i
    _x <<= 1
    if _x & 0x100:
        _x ^= 0x11D
for _i in range(255, 512):
    _EXP[_i] = _EXP[_i - 255]


def _mul(a, b):
    return 0 if a == 0 or b == 0 else _EXP[_LOG[a] + _LOG[b]]


def _rs(data, n):
    gen = [1]
    for i in range(n):
        nxt = [0] * (len(gen) + 1)
        for j, g in enumerate(gen):
            nxt[j] ^= g
            nxt[j + 1] ^= _mul(g, _EXP[i])
        gen = nxt
    rem = [0] * n
    for b in data:
        f = b ^ rem[0]
        rem = rem[1:] + [0]
        for i in range(n):
            rem[i] ^= _mul(gen[i + 1], f)
    return rem


def _bch(v, poly, bits_data, bits_total):
    r = v << (bits_total - bits_data)
    for i in range(bits_data - 1, -1, -1):
        if r >> (i + bits_total - bits_data) & 1:
            r ^= poly << i
    return (v << (bits_total - bits_data)) | r


def _codewords(data: bytes, ver: int):
    total, ecn, groups = _M[ver]
    cap = sum(n * k for n, k in groups)
    bits = "0100" + format(len(data), "08b" if ver < 10 else "016b") + "".join(format(b, "08b") for b in data)
    bits += "0" * min(4, cap * 8 - len(bits))
    bits += "0" * (-len(bits) % 8)
    cw = [int(bits[i:i + 8], 2) for i in range(0, len(bits), 8)]
    pad = [0xEC, 0x11]
    while len(cw) < cap:
        cw.append(pad[(len(cw) - len(bits) // 8) % 2])
    blocks, pos = [], 0
    for n, k in groups:
        for _ in range(n):
            blocks.append(cw[pos:pos + k]); pos += k
    ecs = [_rs(b, ecn) for b in blocks]
    out = []
    for i in range(max(len(b) for b in blocks)):
        for b in blocks:
            if i < len(b):
                out.append(b[i])
    for i in range(ecn):
        for e in ecs:
            out.append(e[i])
    return out


def _build(cw, ver, mask):
    n = 17 + 4 * ver
    m = [[None] * n for _ in range(n)]
    def setm(r, c, v):
        if 0 <= r < n and 0 <= c < n:
            m[r][c] = v
    def finder(r, c):
        for dr in range(-1, 8):
            for dc in range(-1, 8):
                v = 0 <= dr <= 6 and 0 <= dc <= 6 and (dr in (0, 6) or dc in (0, 6) or (2 <= dr <= 4 and 2 <= dc <= 4))
                setm(r + dr, c + dc, v)
    finder(0, 0); finder(0, n - 7); finder(n - 7, 0)
    ap = _ALIGN[ver]
    for r in ap:
        for c in ap:
            if (r < 8 and c < 8) or (r < 8 and c > n - 9) or (r > n - 9 and c < 8):
                continue
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    m[r + dr][c + dc] = max(abs(dr), abs(dc)) != 1
    for i in range(8, n - 8):
        m[6][i] = m[i][6] = (i % 2 == 0)
    m[n - 8][8] = True  # ô đen cố định
    reserved = [[m[r][c] is not None for c in range(n)] for r in range(n)]
    for i in range(9):
        reserved[8][i] = reserved[i][8] = True
    for i in range(8):
        reserved[8][n - 1 - i] = reserved[n - 1 - i][8] = True
    if ver >= 7:
        for i in range(6):
            for j in range(3):
                reserved[i][n - 11 + j] = reserved[n - 11 + j][i] = True
    # dữ liệu theo đường zigzag
    bits = [(b >> (7 - k)) & 1 for b in cw for k in range(8)]
    idx, up, c = 0, True, n - 1
    while c > 0:
        if c == 6:
            c -= 1
        rng = range(n - 1, -1, -1) if up else range(n)
        for r in rng:
            for cc in (c, c - 1):
                if not reserved[r][cc]:
                    bit = bits[idx] if idx < len(bits) else 0
                    idx += 1
                    inv = [(r + cc) % 2 == 0, r % 2 == 0, cc % 3 == 0, (r + cc) % 3 == 0, (r // 2 + cc // 3) % 2 == 0,
                           (r * cc) % 2 + (r * cc) % 3 == 0, ((r * cc) % 2 + (r * cc) % 3) % 2 == 0, ((r + cc) % 2 + (r * cc) % 3) % 2 == 0][mask]
                    m[r][cc] = bool(bit) != bool(inv)
        up = not up
        c -= 2
    # thông tin định dạng (mức M = 00)
    f = _bch((0b00 << 3) | mask, 0b10100110111, 5, 15) ^ 0b101010000010010
    fb = [bool((f >> i) & 1) for i in range(15)]
    for i in range(6):
        m[i][8] = fb[i]
    m[7][8] = fb[6]
    m[8][8] = fb[7]
    m[8][7] = fb[8]
    for i in range(9, 15):
        m[8][14 - i] = fb[i]
    for i in range(8):
        m[8][n - 1 - i] = fb[i]
    for i in range(8, 15):
        m[n - 15 + i][8] = fb[i]
    m[n - 8][8] = True
    if ver >= 7:
        v = _bch(ver, 0b1111100100101, 6, 18)
        for i in range(18):
            bit = bool((v >> i) & 1)
            m[i // 3][n - 11 + i % 3] = bit
            m[n - 11 + i % 3][i // 3] = bit
    return [[bool(x) for x in row] for row in m]


def _penalty(m):
    n = len(m)
    p = 0
    for g in (m, [list(r) for r in zip(*m)]):
        for row in g:
            run = 1
            for i in range(1, n):
                if row[i] == row[i - 1]:
                    run += 1
                else:
                    p += run - 2 if run >= 5 else 0; run = 1
            p += run - 2 if run >= 5 else 0
            s = "".join("1" if x else "0" for x in row)
            p += 40 * (s.count("10111010000") + s.count("00001011101"))
    for r in range(n - 1):
        for c in range(n - 1):
            if m[r][c] == m[r][c + 1] == m[r + 1][c] == m[r + 1][c + 1]:
                p += 3
    dark = sum(sum(r) for r in m) * 100 / (n * n)
    return p + 10 * int(abs(dark - 50) / 5)


def encode(text: str):
    data = text.encode("utf-8")
    for ver in range(1, 11):
        cap = sum(n * k for n, k in _M[ver][2])
        if len(data) + (2 if ver < 10 else 3) <= cap:
            break
    else:
        raise ValueError("Đường link quá dài (tối đa khoảng 213 ký tự)")
    cw = _codewords(data, ver)
    return min((_build(cw, ver, k) for k in range(8)), key=_penalty)


def save_png(matrix, path, box=14, border=4):
    n = len(matrix) + 2 * border
    rows = []
    for r in range(n):
        line = bytearray()
        for c in range(n):
            inside = border <= r < n - border and border <= c < n - border
            dark = inside and matrix[r - border][c - border]
            line += (b"\x00" if dark else b"\xff") * box
        for _ in range(box):
            rows.append(b"\x00" + bytes(line))
    raw = b"".join(rows)
    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", n * box, n * box, 8, 0, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)

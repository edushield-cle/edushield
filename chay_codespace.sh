#!/usr/bin/env bash
# Chạy máy chủ thống kê EduShield trong GitHub Codespaces và in ra link HTTPS (đuôi .app.github.dev).
# Chỉ cần gõ:   bash chay_codespace.sh
# - Trang được phép gửi số liệu: tự lấy https://<tên-GitHub-của-bạn>.github.io (đổi được bằng EDUSHIELD_ALLOW_ORIGIN).
# - Khoá xem thống kê: tự tạo một lần, lưu trong tệp .edushield_view_key (đổi được bằng EDUSHIELD_VIEW_KEY).
set -e
cd "$(dirname "$0")"
if [ -z "$CODESPACE_NAME" ]; then
  echo "Script này dùng trong GitHub Codespaces. Trên máy tính của bạn hãy chạy: py -3.15 server.py"; exit 1
fi
if [ ! -f server.py ]; then echo "Không thấy server.py. Hãy upload đầy đủ thư mục dự án lên kho rồi tạo lại codespace."; exit 1; fi

# Thư viện (lần đầu codespace tự cài; nếu thiếu thì cài lại)
python -c "import sklearn, networkx" 2>/dev/null || { echo "[EduShield] Đang cài thư viện (1-3 phút)..."; pip install -q -r requirements.txt; }

if [ -z "$EDUSHIELD_ALLOW_ORIGIN" ] || [ "$EDUSHIELD_ALLOW_ORIGIN" = "*" ]; then
  export EDUSHIELD_ALLOW_ORIGIN="https://$(echo "${GITHUB_USER}" | tr '[:upper:]' '[:lower:]').github.io"
fi
if [ -z "$EDUSHIELD_VIEW_KEY" ]; then
  [ -f .edushield_view_key ] || python -c "import secrets;print(secrets.token_urlsafe(12))" > .edushield_view_key
  export EDUSHIELD_VIEW_KEY="$(cat .edushield_view_key)"
fi
SCHOOL="${EDUSHIELD_SCHOOL:-THPT_DEMO}"
URL="https://${CODESPACE_NAME}-8765.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-app.github.dev}"
cat <<INFO

==============================================================================
 1) LINK MÁY CHỦ THỐNG KÊ (chép lại):
      $URL

 2) Kiểm tra máy chủ (mở bằng trình duyệt, thấy "ok": true là được):
      $URL/health

 3) Lệnh tạo app có gửi thống kê (chạy trên MÁY TÍNH của bạn, trong CMD):
      py -3.15 build_public.py --collect --server $URL --school $SCHOOL

 4) Nhà trường xem thống kê:
      $URL/truong?school=$SCHOOL&key=$EDUSHIELD_VIEW_KEY

 5) Yêu cầu hỗ trợ có tên - lớp (chỉ khi học sinh tự chọn gửi):
      $URL/hotro?school=$SCHOOL&key=$EDUSHIELD_VIEW_KEY

 Khoá xem:            $EDUSHIELD_VIEW_KEY   (lưu trong tệp .edushield_view_key)
 Trang được gửi về:   $EDUSHIELD_ALLOW_ORIGIN
 GIỮ CỬA SỔ NÀY MỞ. Đóng tab hoặc codespace tự dừng thì máy chủ cũng dừng.
==============================================================================

INFO
# Học sinh gửi gói từ trình duyệt nên cổng phải ở chế độ Public (không cần đăng nhập GitHub).
( sleep 20; gh codespace ports visibility 8765:public -c "$CODESPACE_NAME" >/dev/null 2>&1 \
    && echo "[EduShield] ✅ Đã chuyển cổng 8765 sang Public." \
    || echo "[EduShield] ⚠️ Chưa tự chuyển được cổng sang Public: mở tab PORTS, chuột phải dòng 8765 → Port Visibility → Public."
  # Tự kiểm tra như một máy học sinh: gọi link công khai, KHÔNG kèm đăng nhập GitHub
  sleep 5
  for i in 1 2 3 4 5 6; do
    BODY="$(curl -s -m 10 "$URL/health" 2>/dev/null)"; CODE="$(curl -s -o /dev/null -m 10 -w '%{http_code}' "$URL/health" 2>/dev/null)"
    if echo "$BODY" | grep -q '"ok": *true'; then
      echo "[EduShield] ✅ TỰ KIỂM TRA: link công khai hoạt động, học sinh gửi được thống kê."; break
    fi
    if [ "$i" = 6 ]; then
      case "$CODE" in
        302|401|403) echo "[EduShield] ❌ TỰ KIỂM TRA: cổng 8765 vẫn đang Private (mã $CODE). Tab PORTS → chuột phải 8765 → Port Visibility → Public, rồi mở $URL/health để thử." ;;
        *) echo "[EduShield] ❌ TỰ KIỂM TRA: chưa gọi được $URL/health (mã $CODE). Xem lại tab PORTS có dòng 8765 chưa." ;;
      esac
    fi
    sleep 10
  done ) &
exec python server.py

// Mở sẵn phần hướng dẫn đúng với thiết bị của bạn (không gửi dữ liệu đi đâu).
(function () {
  var ua = navigator.userAgent || "";
  var ios = /iPhone|iPad|iPod/.test(ua) || (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1);
  var android = /Android/.test(ua);
  var mobile = ios || android;
  var d = function (id) { return document.getElementById(id); };
  if (ios && d("d-ios")) d("d-ios").open = true;
  if (android && d("d-android")) d("d-android").open = true;
  if (mobile && d("pc")) { var h = d("pc").querySelector(".small"); if (h) h.textContent = "Dành cho máy tính. Nếu bạn đang dùng điện thoại, hãy dùng Cách 1 ở trên."; }
})();

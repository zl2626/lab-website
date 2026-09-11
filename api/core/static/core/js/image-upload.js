/**
 * 后台图片上传的客户端处理。
 *
 * 手机拍的照片动辄 4~8MB，而 Vercel 的请求体上限约 4.5MB，
 * 直接上传会被拒。所以选图后先在浏览器里用 canvas 等比压缩到长边 1600px，
 * 再塞回 file input 提交 —— 用户完全无感。
 */
(function () {
  var MAX_EDGE = 1600;
  var QUALITY = 0.85;
  var HARD_LIMIT = 4 * 1024 * 1024;
  var SKIP_BELOW = 1.5 * 1024 * 1024;

  function downscale(file) {
    return new Promise(function (resolve) {
      // 非图片或动图原样上传，交给服务端处理
      if (!/^image\//.test(file.type) || file.type === 'image/gif') return resolve(file);

      var url = URL.createObjectURL(file);
      var img = new Image();

      img.onload = function () {
        var w = img.naturalWidth;
        var h = img.naturalHeight;
        var scale = Math.min(1, MAX_EDGE / Math.max(w, h));

        if (scale === 1 && file.size <= SKIP_BELOW) {
          URL.revokeObjectURL(url);
          return resolve(file);
        }

        var cw = Math.max(1, Math.round(w * scale));
        var ch = Math.max(1, Math.round(h * scale));
        var canvas = document.createElement('canvas');
        canvas.width = cw;
        canvas.height = ch;
        canvas.getContext('2d').drawImage(img, 0, 0, cw, ch);

        canvas.toBlob(
          function (blob) {
            URL.revokeObjectURL(url);
            if (!blob) return resolve(file);
            var name = (file.name || 'photo').replace(/\.[^.]+$/, '') + '.jpg';
            resolve(new File([blob], name, { type: 'image/jpeg' }));
          },
          'image/jpeg',
          QUALITY
        );
      };

      img.onerror = function () {
        URL.revokeObjectURL(url);
        resolve(file);
      };

      img.src = url;
    });
  }

  function attach(input) {
    input.addEventListener('change', function () {
      var file = input.files && input.files[0];
      if (!file) return;

      var box = input.closest('.lab-img');
      if (box) box.classList.add('is-busy');

      downscale(file).then(function (out) {
        try {
          var dt = new DataTransfer();
          dt.items.add(out);
          input.files = dt.files;
        } catch (e) {
          /* 老浏览器不支持 DataTransfer，就传原图，由服务端校验 */
        }
        if (out.size > HARD_LIMIT) {
          window.alert('图片压缩后仍然超过 4MB，请换一张尺寸更小的图片。');
        }
        if (box) box.classList.remove('is-busy');
      });
    });
  }

  function boot() {
    var inputs = document.querySelectorAll('.lab-img__file');
    for (var i = 0; i < inputs.length; i++) attach(inputs[i]);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();

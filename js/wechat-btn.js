// 微信按钮点击复制微信号并弹出提示
window.addEventListener('DOMContentLoaded', function() {
  var btn = document.getElementById('wechat-btn');
  if (!btn) return;
  btn.addEventListener('click', function(e) {
    e.preventDefault();
    var wechatId = 'valkjin';
    if (navigator.clipboard) {
      navigator.clipboard.writeText(wechatId).then(function() {
        showWechatToast('微信号已复制：' + wechatId + '，请在微信中搜索添加');
      });
    } else {
      // 兼容旧浏览器
      var input = document.createElement('input');
      input.value = wechatId;
      document.body.appendChild(input);
      input.select();
      document.execCommand('copy');
      document.body.removeChild(input);
      showWechatToast('微信号已复制：' + wechatId + '，请在微信中搜索添加');
    }
  });
});
function showWechatToast(msg) {
  var toast = document.createElement('div');
  toast.className = 'wechat-toast';
  toast.innerText = msg;
  document.body.appendChild(toast);
  setTimeout(function() { toast.classList.add('show'); }, 10);
  setTimeout(function() {
    toast.classList.remove('show');
    setTimeout(function() { document.body.removeChild(toast); }, 350);
  }, 2200);
}

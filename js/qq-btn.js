// QQ按钮点击复制QQ号并弹出提示
window.addEventListener('DOMContentLoaded', function() {
  var btn = document.getElementById('qq-btn');
  if (!btn) return;
  btn.addEventListener('click', function(e) {
    e.preventDefault();
    var qqId = '1247903536';
    if (navigator.clipboard) {
      navigator.clipboard.writeText(qqId).then(function() {
        showQQToast('QQ号已复制：' + qqId + '，请在QQ中搜索添加');
      });
    } else {
      // 兼容旧浏览器
      var input = document.createElement('input');
      input.value = qqId;
      document.body.appendChild(input);
      input.select();
      document.execCommand('copy');
      document.body.removeChild(input);
      showQQToast('QQ号已复制：' + qqId + '，请在QQ中搜索添加');
    }
  });
});
function showQQToast(msg) {
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

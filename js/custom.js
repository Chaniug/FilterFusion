// 自定义动画或交互JS（如需扩展动画、滚动、点击等效果可在此添加）

document.addEventListener('DOMContentLoaded', function() {
  // 让.fade-in类的元素在页面加载后渐现
  const fadeEls = document.querySelectorAll('.fade-in');
  fadeEls.forEach(el => {
    el.style.opacity = 1;
    el.style.transform = 'scale(1)';
  });
  // 可在此添加更多交互
});

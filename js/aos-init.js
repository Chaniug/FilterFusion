// 使用AOS.js实现滚动时内容淡入淡出等高级动效，采用非线性缓动
// 文档：https://michalsnik.github.io/aos/

document.addEventListener('DOMContentLoaded', function() {
  if (window.AOS) {
    AOS.init({
      duration: 1100,
      easing: 'cubic-bezier(.77,0,.175,1)', // 非线性缓动，更自然
      once: false, // 回滚时也有动画
      mirror: true, // 回滚时反向动画
      offset: 80 // 触发点更贴合人眼运动
    });
  }
});

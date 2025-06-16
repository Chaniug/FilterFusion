// hero-split-anim.js: 分屏动画控制
window.addEventListener('DOMContentLoaded', function() {
  const hero = document.querySelector('.hero-split');
  setTimeout(() => {
    if(hero) hero.classList.add('split-animate');
  }, 400); // 图片加载后分屏动画
});

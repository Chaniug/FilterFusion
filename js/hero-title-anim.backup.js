// 备份原 hero-title-anim.js
// hero-title-anim.js: 主标题三行动画控制
function showHeroLinesSequential() {
  const lines = document.querySelectorAll('.hero-title-line');
  lines.forEach((line, i) => {
    line.style.opacity = '0';
    setTimeout(() => {
      line.style.opacity = '1';
      line.classList.remove('out');
    }, 400 + i * 500);
  });
}
function hideHeroLinesSequential() {
  const lines = document.querySelectorAll('.hero-title-line');
  lines.forEach((line, i) => {
    setTimeout(() => {
      line.classList.add('out');
    }, i * 300);
  });
}
function fadeOutHero() {
  const hero = document.querySelector('.hero');
  if(hero) hero.classList.add('hero-fade-out');
}
function fadeInHero() {
  const hero = document.querySelector('.hero');
  if(hero) hero.classList.remove('hero-fade-out');
}
window.addEventListener('DOMContentLoaded', function() {
  showHeroLinesSequential();
  setTimeout(hideHeroLinesSequential, 3200);
  // 滚动触发整体淡出动画，回滚时恢复
  let faded = false;
  window.addEventListener('scroll', function() {
    if(window.scrollY > window.innerHeight * 0.3) {
      if(!faded) {
        fadeOutHero();
        faded = true;
      }
    } else {
      if(faded) {
        fadeInHero();
        faded = false;
      }
    }
  });
});

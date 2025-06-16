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
  if(hero) {
    hero.classList.remove('hero-fade-out');
    hero.style.opacity = '1';
    hero.style.transform = 'none';
  }
}
function isHeroShouldFade() {
  // 只在hero底部完全离开视口时才触发淡出
  const hero = document.querySelector('.hero');
  if(!hero) return false;
  const rect = hero.getBoundingClientRect();
  return rect.bottom <= 0;
}
window.addEventListener('DOMContentLoaded', function() {
  showHeroLinesSequential();
  setTimeout(hideHeroLinesSequential, 3200);
  // 滚动触发整体淡出动画，回滚时恢复
  let faded = false;
  window.addEventListener('scroll', function() {
    if(isHeroShouldFade()) {
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

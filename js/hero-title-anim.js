// hero-title-anim.js: 主标题三行动画控制
function hideHeroLinesSequential() {
  const lines = document.querySelectorAll('.hero-title-line');
  if(lines[0]) setTimeout(()=>lines[0].classList.add('hide'), 0);
  if(lines[1]) setTimeout(()=>lines[1].classList.add('hide'), 600);
}
window.addEventListener('DOMContentLoaded', function() {
  setTimeout(hideHeroLinesSequential, 2600);
  // 滚动触发消散
  let hidden = false;
  window.addEventListener('scroll', function() {
    if(!hidden && window.scrollY > 40) {
      hideHeroLinesSequential();
      hidden = true;
    }
  });
});

// about-glide.js: 初始化Glide.js轮播
window.addEventListener('DOMContentLoaded', function() {
  if(window.Glide) {
    new Glide('.about-glide', {
      type: 'carousel',
      autoplay: 5000,
      hoverpause: true,
      animationDuration: 900,
      perView: 1,
      gap: 0,
      swipeThreshold: 40,
      dragThreshold: 40
    }).mount();
  }
});

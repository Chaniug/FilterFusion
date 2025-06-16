// about-swiper.js: 初始化about部分轮播
window.addEventListener('DOMContentLoaded', function() {
  if(window.Swiper) {
    new Swiper('.about-swiper', {
      direction: 'horizontal',
      loop: false,
      slidesPerView: 1,
      spaceBetween: 24,
      pagination: { el: '.swiper-pagination', clickable: true },
      navigation: { nextEl: '.swiper-button-next', prevEl: '.swiper-button-prev' },
      allowTouchMove: true,
      keyboard: { enabled: true },
      on: {
        reachEnd: function() {
          // 轮播到最后一页后允许页面继续向下滚动
          document.body.style.overflowY = 'auto';
        },
        slideChange: function(swiper) {
          // 非最后一页时锁定页面滚动
          if(swiper.isEnd) {
            document.body.style.overflowY = 'auto';
          } else {
            document.body.style.overflowY = 'hidden';
          }
        }
      }
    });
  }
});

// 视频背景兼容性与动画增强脚本
// 1. 自适应大小，2. 支持播放速度调节，3. 淡入淡出动画，4. 移动端降级

(function() {
  const video = document.querySelector('.hero-bg-video');
  if (!video) return;

  // 1. 自适应高度（防止拉伸/黑边）
  function resizeVideo() {
    if (window.innerWidth / window.innerHeight > 1.2) {
      video.style.objectFit = 'cover';
    } else {
      video.style.objectFit = 'cover';
    }
  }
  window.addEventListener('resize', resizeVideo);
  resizeVideo();

  // 2. 播放速度调节（默认0.85倍速，更有氛围感）
  video.playbackRate = 0.85;

  // 3. 淡入动画
  video.style.opacity = 0;
  video.addEventListener('canplay', function() {
    setTimeout(() => {
      video.style.transition = 'opacity 1.2s cubic-bezier(.77,0,.175,1)';
      video.style.opacity = window.innerWidth < 600 ? 0.38 : 0.55;
    }, 120);
  });

  // 4. 移动端降级（如需可自动暂停/隐藏视频，节省流量）
  if (/Mobi|Android|iPhone/i.test(navigator.userAgent)) {
    // video.pause();
    // video.style.display = 'none';
    // 可根据需求选择是否降级
  }
})();

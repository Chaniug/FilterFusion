// hero-bg-waves.js: 使用VANTA.WAVES实现水面涟漪动画
window.addEventListener('DOMContentLoaded', function() {
  if(window.VANTA && window.VANTA.WAVES) {
    window.VANTA.WAVES({
      el: ".hero-bg-wave-wrap",
      mouseControls: false,
      touchControls: false,
      minHeight: 200.00,
      minWidth: 200.00,
      scale: 1.0,
      scaleMobile: 1.0,
      color: 0x1e293b,
      shininess: 60.0,
      waveHeight: 18.0,
      waveSpeed: 0.7,
      zoom: 1.1,
      backgroundColor: 0x0a1020
    });
  }
});

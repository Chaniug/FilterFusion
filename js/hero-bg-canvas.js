// 动态科技感粒子背景（canvas）
// 适用于.hero头部，兼容移动端，性能友好

(function() {
  const canvas = document.createElement('canvas');
  canvas.className = 'hero-bg-canvas';
  canvas.style.position = 'absolute';
  canvas.style.left = 0;
  canvas.style.top = 0;
  canvas.style.width = '100%';
  canvas.style.height = '100%';
  canvas.style.zIndex = 2;
  canvas.style.pointerEvents = 'none';
  canvas.style.opacity = 0.7;
  document.querySelector('.hero').prepend(canvas);

  const ctx = canvas.getContext('2d');
  let dpr = window.devicePixelRatio || 1;
  let width = 0, height = 0;
  let particles = [];
  const PARTICLE_NUM = window.innerWidth < 600 ? 32 : 56;
  const COLOR1 = '#38bdf8', COLOR2 = '#fbbf24';

  function resize() {
    width = canvas.offsetWidth;
    height = canvas.offsetHeight;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.scale(dpr, dpr);
  }

  function randomColor() {
    return Math.random() > 0.5 ? COLOR1 : COLOR2;
  }

  function createParticles() {
    particles = [];
    for (let i = 0; i < PARTICLE_NUM; i++) {
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        r: 1.2 + Math.random() * 2.2,
        dx: (Math.random() - 0.5) * 0.7,
        dy: (Math.random() - 0.5) * 0.7,
        color: randomColor()
      });
    }
  }

  function draw() {
    ctx.clearRect(0, 0, width, height);
    // 画粒子
    for (let i = 0; i < particles.length; i++) {
      const p = particles[i];
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, 2 * Math.PI);
      ctx.fillStyle = p.color;
      ctx.shadowColor = p.color;
      ctx.shadowBlur = 8;
      ctx.globalAlpha = 0.85;
      ctx.fill();
      ctx.globalAlpha = 1;
      ctx.shadowBlur = 0;
    }
    // 画连线
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const p1 = particles[i], p2 = particles[j];
        const dist = Math.hypot(p1.x - p2.x, p1.y - p2.y);
        if (dist < 88) {
          ctx.beginPath();
          ctx.moveTo(p1.x, p1.y);
          ctx.lineTo(p2.x, p2.y);
          ctx.strokeStyle = p1.color;
          ctx.globalAlpha = 0.18 + 0.18 * (1 - dist / 88);
          ctx.lineWidth = 1.1;
          ctx.stroke();
          ctx.globalAlpha = 1;
        }
      }
    }
  }

  function animate() {
    for (let p of particles) {
      p.x += p.dx;
      p.y += p.dy;
      if (p.x < 0 || p.x > width) p.dx *= -1;
      if (p.y < 0 || p.y > height) p.dy *= -1;
    }
    draw();
    requestAnimationFrame(animate);
  }

  function init() {
    resize();
    createParticles();
    animate();
  }

  window.addEventListener('resize', () => {
    resize();
    createParticles();
  });

  setTimeout(init, 200); // 等待hero渲染
})();

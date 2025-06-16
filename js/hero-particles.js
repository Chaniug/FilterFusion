// hero-particles.js: hero粒子特效（使用tsParticles）
window.addEventListener('DOMContentLoaded', function() {
  if(window.tsParticles) {
    window.tsParticles.load('hero-particles', {
      background: { color: 'transparent' },
      fpsLimit: 60,
      particles: {
        number: { value: 48, density: { enable: true, area: 800 } },
        color: { value: ['#38bdf8', '#7c3aed', '#fff'] },
        shape: { type: 'circle' },
        opacity: { value: 0.7 },
        size: { value: 2.8, random: true },
        move: { enable: true, speed: 1.2, direction: 'none', outModes: 'out' },
        links: { enable: true, distance: 120, color: '#38bdf8', opacity: 0.25, width: 1 }
      },
      detectRetina: true
    });
  }
});

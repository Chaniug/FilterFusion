document.addEventListener('DOMContentLoaded', () => {
    // 平滑滚动
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // 滚动动画触发
    const animateOnScroll = () => {
        const elements = document.querySelectorAll('.animate');
        const windowHeight = window.innerHeight;
        
        elements.forEach(element => {
            const elementPosition = element.getBoundingClientRect().top;
            const animationPoint = windowHeight - 100;
            
            if (elementPosition < animationPoint) {
                element.classList.add('animated');
            }
        });
    };

    // 初始化观察器
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animated');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    // 观察所有需要动画的元素
    document.querySelectorAll('.animate').forEach(el => {
        observer.observe(el);
    });

    // 初始加载时触发一次
    animateOnScroll();
    window.addEventListener('scroll', animateOnScroll);
});

// 项目卡片交互
function setupProjectCards() {
    const cards = document.querySelectorAll('.project-card');
    
    cards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-5px)';
            card.style.boxShadow = '0 10px 20px rgba(0,0,0,0.2)';
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translateY(0)';
            card.style.boxShadow = '0 5px 15px rgba(0,0,0,0.1)';
        });
    });
}

// 当项目卡片加载后调用
document.addEventListener('DOMContentLoaded', setupProjectCards);
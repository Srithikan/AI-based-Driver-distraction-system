// Smooth Scroll for Navigation Links
document.querySelectorAll('nav ul li a').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        const targetId = this.getAttribute('href').substring(1);
        const targetElement = document.getElementById(targetId);
        window.scrollTo({
            top: targetElement.offsetTop - 50,
            behavior: 'smooth'
        });
    });
});

document.querySelector('.menu-toggle').addEventListener('click', function () {
    document.querySelector('.nav-links').classList.toggle('show');
});


window.onload = function() {
    setTimeout(() => {
        document.querySelector('.car-left').style.transform = 'translateX(75vw)';
        document.querySelector('.car-right').style.transform = 'translateX(-75vw)';

        setTimeout(() => {
            document.querySelector('.crash-effect').style.opacity = '1';
        },1800 );
    }, 500);
};

// Smooth Scroll for Navigation Links 
document.querySelectorAll('nav ul li a').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        const targetId = this.getAttribute('href').substring(1);
        const targetElement = document.getElementById(targetId);
        window.scrollTo({
            top: targetElement.offsetTop - 50,
            behavior: 'smooth'
        });
    });
});

// Responsive Menu Toggle
document.querySelector('.menu-toggle').addEventListener('click', function () {
    document.querySelector('.nav-links').classList.toggle('show');
});

// GSAP Animations for Smooth Entrance Effects
document.addEventListener("DOMContentLoaded", function () {
    gsap.from(".hero .overlay h1", { duration: 1, opacity: 0, y: -30, ease: "power2.out" });
    gsap.from(".hero .overlay p", { duration: 1, opacity: 0, y: 30, delay: 0.5, ease: "power2.out" });
    
    // Scroll-triggered animations
    gsap.registerPlugin(ScrollTrigger);

    gsap.to(".overview-container", {
        duration: 1,
        opacity: 1,
        y: 0,
        ease: "power2.out",
        scrollTrigger: {
            trigger: ".overview-container",
            start: "top 80%",
            toggleActions: "play none none none"
        }
    });

    document.querySelectorAll(".feature").forEach((feature, index) => {
        gsap.to(feature, {
            duration: 1,
            opacity: 1,
            scale: 1,
            delay: index * 0.2,
            ease: "power2.out",
            scrollTrigger: {
                trigger: feature,
                start: "top 90%",
                toggleActions: "play none none none"
            }
        });
    });

    gsap.to(".footer", {
        duration: 1.5,
        opacity: 1,
        y: 0,
        ease: "power2.out",
        scrollTrigger: {
            trigger: ".footer",
            start: "top 85%",
            toggleActions: "play none none none"
        }
    });
});

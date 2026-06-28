import { useEffect, useRef } from 'react';

const testimonials = [
  {
    quote: "We used to spend 20 minutes arguing over what to order. Now someone tags @EasyOrder and we're done in 3 minutes. The shared canvas is genius.",
    author: "Priya Sharma",
    role: "Host, Friday office lunch group",
  },
  {
    quote: "As a vegetarian, I always worried about mixed orders. The dietary tagging caught a chicken kebab in our veg session before checkout. Lifesaver.",
    author: "Rahul Menon",
    role: "Guest, college friend group",
  },
  {
    quote: "Managing drinks from Instamart and food from restaurants in one place? Chef's kiss. The budget meter kept us honest when everyone kept adding desserts.",
    author: "Ananya Gupta",
    role: "Host, birthday party planning",
  },
  {
    quote: "The degraded state handling is surprisingly smooth. When Instamart timed out, we still got our food recommendations and added drinks manually later.",
    author: "Vikram Patel",
    role: "Host, cricket watch party",
  },
  {
    quote: "I love that checkout stays with the host. No more 'who's paying?' confusion. I just click validate, log into Swiggy, and done.",
    author: "Deepika Nair",
    role: "Host, weekend brunch crew",
  },
];

export function Testimonials() {
  const carouselRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = carouselRef.current;
    if (!el) return;

    let paused = false;
    let animId: number;

    const step = () => {
      if (!paused && el) {
        el.scrollLeft += 0.5;
        if (el.scrollLeft >= el.scrollWidth - el.clientWidth) {
          el.scrollLeft = 0;
        }
      }
      animId = requestAnimationFrame(step);
    };

    animId = requestAnimationFrame(step);

    const pause = () => { paused = true; };
    const resume = () => { paused = false; };

    el.addEventListener('mouseenter', pause);
    el.addEventListener('mouseleave', resume);
    el.addEventListener('touchstart', pause, { passive: true });
    el.addEventListener('touchend', resume);

    return () => {
      cancelAnimationFrame(animId);
      el.removeEventListener('mouseenter', pause);
      el.removeEventListener('mouseleave', resume);
      el.removeEventListener('touchstart', pause);
      el.removeEventListener('touchend', resume);
    };
  }, []);

  return (
    <section className="testimonials" id="testimonials" aria-label="Testimonials">
      <div className="section-container">
        <p className="section-eyebrow fade-up">What Users Say</p>
        <h2 className="section-title fade-up">Trusted by group order hosts</h2>
      </div>

      <div className="testimonials-carousel" ref={carouselRef}>
        {testimonials.map((t) => (
          <div className="testimonial-card" key={t.author}>
            <p className="testimonial-quote">{t.quote}</p>
            <p className="testimonial-author">{t.author}</p>
            <p className="testimonial-role">{t.role}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

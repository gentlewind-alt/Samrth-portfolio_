import React, { useCallback, useEffect, useRef, useState } from 'react';
import Head from 'next/head';
import PORTFOLIO_CSS from './portfolioCss';

const SECTIONS = ['home', 'projects', 'about', 'skills', 'education', 'interests', 'contact'];

const TICKER = [
  'Building AI-driven applications',
  'Merging machine learning, IoT and web',
  'Shipping firmware on 400KB of RAM',
  'Taking on freelance work'
];

// Frames shipped with the design: an idle loop, a slap sequence and a
// faster one for rapid clicks.
const CHIYO_FRAMES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 19, 20, 21, 22, 23];
const CHIYO_IDLE = [1, 2, 3, 4];
const CHIYO_SLAP = [5, 6, 7, 8, 9, 10, 11];
const CHIYO_FAST = [19, 20, 21, 22, 23];

export default function PortfolioV2({
  accent = '#22c55e',
  motion = 'confident',
  cursor = true,
  startChiyoOn = true,
  fastClickWindowMs = 290,
  veilOpacity = 0,
  scrimOpacity = 0,
  slapSound = true,
  slapAudioDelayMs = 90,
  slapVolume = 0.6
}) {
  const [open, setOpen] = useState(null);
  const [active, setActive] = useState(0);
  const [clock, setClock] = useState('');
  const [clockFull, setClockFull] = useState('');
  const [ticker, setTicker] = useState(TICKER[0]);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [chiyoMode, setChiyoMode] = useState(false);
  const [chiyoFrame, setChiyoFrame] = useState(1);
  const [chiyoSlapCount, setChiyoSlapCount] = useState(0);

  const fieldRef = useRef(null);
  const ringRef = useRef(null);
  const dotRef = useRef(null);
  const progressRef = useRef(null);
  const chiyoLayerRef = useRef(null);

  const chiyoReady = useRef(false);
  const chiyoBusy = useRef(false);
  const lastChiyoClick = useRef(0);
  const seqTimer = useRef(null);
  const watchdog = useRef(null);
  const slapPool = useRef(null);
  const slapIdx = useRef(0);
  const slapTimers = useRef([]);

  // The app-wide stylesheet paints a dark background for the admin pages, so
  // the portfolio's light ground is scoped to this class rather than to `body`.
  useEffect(() => {
    document.body.classList.add('pv2');
    return () => document.body.classList.remove('pv2');
  }, []);

  // Mirrors the design's componentDidMount: Chiyo starts after mount so the
  // server-rendered markup and the first client render agree.
  useEffect(() => {
    const stored = parseInt(window.localStorage.getItem('chiyoSlapCount') || '0', 10);
    if (stored) setChiyoSlapCount(stored);
    if (startChiyoOn) setChiyoMode(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const opts = { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit', hour12: false };
    const tick = () => {
      const now = new Date();
      setClock(new Intl.DateTimeFormat('en-GB', opts).format(now));
      setClockFull(
        new Intl.DateTimeFormat('en-GB', Object.assign({ second: '2-digit' }, opts)).format(now) + ' IST'
      );
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    let i = 0;
    const id = setInterval(() => {
      i = (i + 1) % TICKER.length;
      setTicker(TICKER[i]);
    }, 4200);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    const onScroll = () => {
      const h = document.documentElement;
      const max = h.scrollHeight - h.clientHeight;
      const p = max > 0 ? Math.min(1, h.scrollTop / max) : 0;
      if (progressRef.current) progressRef.current.style.transform = 'scaleX(' + p + ')';
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  // Reveal-on-scroll, with a safety net so nothing stays invisible if the
  // observer never fires.
  useEffect(() => {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const els = Array.from(document.querySelectorAll('[data-reveal]'));
    const show = (el) => {
      el.style.opacity = '1';
      el.style.transform = 'none';
    };
    if (reduced) {
      els.forEach(show);
      return undefined;
    }
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            show(e.target);
            obs.unobserve(e.target);
          }
        });
      },
      { threshold: 0.08, rootMargin: '0px 0px -60px 0px' }
    );
    els.forEach((el) => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(22px)';
      el.style.transition = 'opacity .9s cubic-bezier(.16,1,.3,1), transform .9s cubic-bezier(.16,1,.3,1)';
      obs.observe(el);
    });
    const safety = setTimeout(() => els.forEach(show), 2600);
    return () => {
      clearTimeout(safety);
      obs.disconnect();
    };
  }, []);

  useEffect(() => {
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            const i = SECTIONS.indexOf(e.target.id);
            if (i >= 0) setActive(i);
          }
        });
      },
      { rootMargin: '-45% 0px -50% 0px' }
    );
    SECTIONS.forEach((id) => {
      const el = document.getElementById(id);
      if (el) obs.observe(el);
    });
    return () => obs.disconnect();
  }, []);

  // Trailing ring + dot that replaces the system cursor on fine pointers.
  useEffect(() => {
    if (!cursor) return undefined;
    if (window.matchMedia('(pointer: coarse)').matches) return undefined;
    const ring = ringRef.current;
    const dot = dotRef.current;
    if (!ring || !dot) return undefined;

    let mx = window.innerWidth / 2;
    let my = window.innerHeight / 2;
    let rx = mx;
    let ry = my;
    let shown = false;
    let raf = 0;

    const onMove = (e) => {
      mx = e.clientX;
      my = e.clientY;
      dot.style.transform = 'translate3d(' + (mx - 2.5) + 'px,' + (my - 2.5) + 'px,0)';
      if (!shown) {
        shown = true;
        ring.style.opacity = '1';
        dot.style.opacity = '1';
      }
      const t = e.target;
      const grow = !!(
        t &&
        t.closest &&
        (t.closest('a,button,[role=button],[data-nav]') || t.closest('div[style*="cursor:pointer"]'))
      );
      ring.style.width = grow ? '54px' : '34px';
      ring.style.height = grow ? '54px' : '34px';
      ring.style.backgroundColor = grow ? 'rgba(26,28,25,.07)' : 'transparent';
      ring.style.borderColor = grow ? 'rgba(26,28,25,.75)' : 'rgba(26,28,25,.45)';
    };

    const loop = () => {
      const w = parseFloat(ring.style.width || '34');
      rx += (mx - rx) * 0.16;
      ry += (my - ry) * 0.16;
      ring.style.transform = 'translate3d(' + (rx - w / 2) + 'px,' + (ry - w / 2) + 'px,0)';
      raf = requestAnimationFrame(loop);
    };

    window.addEventListener('mousemove', onMove, { passive: true });
    loop();
    return () => {
      window.removeEventListener('mousemove', onMove);
      cancelAnimationFrame(raf);
    };
  }, [cursor]);

  // Drifting particle field behind the content.
  useEffect(() => {
    const cv = fieldRef.current;
    if (!cv) return undefined;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return undefined;
    const intensity = motion || 'confident';
    if (intensity === 'calm') return undefined;

    const ctx = cv.getContext('2d');
    const density = intensity === 'showpiece' ? 13000 : 22000;
    const speed = intensity === 'showpiece' ? 0.22 : 0.13;
    const mouse = { x: -999, y: -999 };
    let w = 0;
    let h = 0;
    let pts = [];
    let raf = 0;

    const setup = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = cv.clientWidth;
      h = cv.clientHeight;
      cv.width = w * dpr;
      cv.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const n = Math.min(150, Math.round((w * h) / density));
      pts = [];
      for (let i = 0; i < n; i += 1) {
        pts.push({
          x: Math.random() * w,
          y: Math.random() * h,
          vx: (Math.random() - 0.5) * speed,
          vy: (Math.random() - 0.5) * speed,
          r: Math.random() * 1.1 + 0.5
        });
      }
    };

    const onResize = () => setup();
    const onMove = (e) => {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
    };

    const draw = () => {
      ctx.clearRect(0, 0, w, h);
      for (let i = 0; i < pts.length; i += 1) {
        const p = pts[i];
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < -20) p.x = w + 20;
        if (p.x > w + 20) p.x = -20;
        if (p.y < -20) p.y = h + 20;
        if (p.y > h + 20) p.y = -20;
        const dx = p.x - mouse.x;
        const dy = p.y - mouse.y;
        const d2 = dx * dx + dy * dy;
        const glow = d2 < 26000 ? 1 - d2 / 26000 : 0;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r + glow * 1.4, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(26,28,25,' + (0.1 + glow * 0.35) + ')';
        ctx.fill();
      }
      raf = requestAnimationFrame(draw);
    };

    setup();
    window.addEventListener('resize', onResize);
    window.addEventListener('mousemove', onMove, { passive: true });
    draw();
    return () => {
      window.removeEventListener('resize', onResize);
      window.removeEventListener('mousemove', onMove);
      cancelAnimationFrame(raf);
    };
  }, [motion]);

  // Hold the idle loop until every frame has decoded, so the first slap
  // doesn't flash a half-loaded image.
  useEffect(() => {
    if (!chiyoMode) {
      chiyoReady.current = false;
      return undefined;
    }
    let cancelled = false;
    const layer = chiyoLayerRef.current;
    const imgs = layer ? Array.from(layer.children) : [];
    Promise.all(
      imgs.map((img) => (img.decode ? img.decode().catch(() => {}) : Promise.resolve()))
    ).then(() => {
      if (!cancelled) chiyoReady.current = true;
    });
    return () => {
      cancelled = true;
    };
  }, [chiyoMode]);

  useEffect(() => {
    if (!chiyoMode) return undefined;
    const id = setInterval(() => {
      if (chiyoBusy.current || !chiyoReady.current) return;
      setChiyoFrame((f) => CHIYO_IDLE[(CHIYO_IDLE.indexOf(f) + 1) % CHIYO_IDLE.length]);
    }, 480);
    return () => clearInterval(id);
  }, [chiyoMode]);

  const playSlapSound = useCallback(() => {
    if (!slapSound) return;
    if (!slapPool.current) {
      slapPool.current = [0, 1, 2, 3].map(() => {
        const a = new Audio('/chiyo/slap.mp3');
        a.preload = 'auto';
        return a;
      });
    }
    const t = setTimeout(() => {
      slapIdx.current = (slapIdx.current + 1) % slapPool.current.length;
      const a = slapPool.current[slapIdx.current];
      a.volume = slapVolume;
      a.currentTime = 0;
      const p = a.play();
      if (p && p.catch) p.catch(() => {});
    }, slapAudioDelayMs);
    slapTimers.current.push(t);
  }, [slapSound, slapVolume, slapAudioDelayMs]);

  // Any click anywhere lands a slap; clicks in quick succession play the
  // shorter, faster sequence instead.
  useEffect(() => {
    if (!chiyoMode) return undefined;
    const onPointerDown = () => {
      if (!chiyoReady.current) return;
      const now = Date.now();
      const fast = now - lastChiyoClick.current < fastClickWindowMs;
      lastChiyoClick.current = now;
      clearTimeout(seqTimer.current);
      clearTimeout(watchdog.current);

      const seq = fast ? CHIYO_FAST : CHIYO_SLAP;
      const stepMs = fast ? 55 : 70;
      playSlapSound();
      setChiyoSlapCount((c) => {
        const next = c + 1;
        window.localStorage.setItem('chiyoSlapCount', String(next));
        return next;
      });

      chiyoBusy.current = true;
      let i = 0;
      const step = () => {
        setChiyoFrame(seq[i]);
        i += 1;
        if (i < seq.length) {
          seqTimer.current = setTimeout(step, stepMs);
        } else {
          seqTimer.current = setTimeout(() => {
            chiyoBusy.current = false;
            setChiyoFrame(1);
          }, 220);
        }
      };
      step();
      watchdog.current = setTimeout(() => {
        chiyoBusy.current = false;
        setChiyoFrame(1);
      }, seq.length * stepMs + 600);
    };

    document.addEventListener('pointerdown', onPointerDown);
    return () => {
      document.removeEventListener('pointerdown', onPointerDown);
      clearTimeout(seqTimer.current);
      clearTimeout(watchdog.current);
    };
  }, [chiyoMode, fastClickWindowMs, playSlapSound]);

  useEffect(
    () => () => {
      slapTimers.current.forEach(clearTimeout);
    },
    []
  );

  const rootBg = '#fafaf5';
  const isOpen = open !== null;
  const open0Active = open === 0;
  const open1Active = open === 1;
  const open2Active = open === 2;
  const open3Active = open === 3;
  const open0 = () => setOpen(0);
  const open1 = () => setOpen(1);
  const open2 = () => setOpen(2);
  const open3 = () => setOpen(3);
  const closePanel = () => setOpen(null);

  const navIndicator = 'translateY(' + active * 44 + 'px)';
  const navClick = (e) => {
    const i = parseInt(e.currentTarget.getAttribute('data-nav'), 10);
    if (!Number.isNaN(i)) setActive(i);
  };

  const sidebarExpanded = !sidebarCollapsed;
  const sidebarIcon = sidebarCollapsed ? 'chevron_right' : 'chevron_left';
  const asideWidth = sidebarCollapsed ? '76px' : '264px';
  const mainMarginLeft = sidebarCollapsed ? '76px' : '264px';
  const toggleSidebar = () => setSidebarCollapsed((s) => !s);

  const asideBg = chiyoMode ? 'transparent' : '#fafaf5';
  const asideBgImage = chiyoMode ? 'none' : "url('/design/ink.svg')";
  const chiyoFill = chiyoMode ? 1 : 0;
  const chiyoIconColor = chiyoMode ? 'var(--accent)' : '#8a8d8d';
  const chiyoStatusLabel = chiyoMode ? 'ON' : 'OFF';
  const toggleChiyo = () => {
    chiyoBusy.current = false;
    setChiyoFrame(1);
    setChiyoMode((m) => !m);
  };

  // Raw CSS fragments in the design; spread into the inline styles here.
  const projMetaExtra = chiyoMode ? { color: '#4a4d4d' } : null;
  const chiyoTextExtra = chiyoMode
    ? { textShadow: '0 0 5px rgba(250,250,245,.72),0 0 1px rgba(250,250,245,.9)' }
    : null;

  return (
    <>
      <Head>
        <title>S. RAWAT — Applied AI Systems</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Bitter:wght@300;400;500;700&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,300,0,0&display=swap"
          rel="stylesheet"
        />
        <style dangerouslySetInnerHTML={{ __html: PORTFOLIO_CSS }} />
      </Head>
<div style={{ minHeight: '100vh', background: rootBg, color: '#1a1c19', position: 'relative', overflowX: 'hidden', '--accent': accent, transition: 'background-color .6s ease', ...(chiyoTextExtra) }}>

{chiyoMode && (<>
<div style={{ position: 'fixed', inset: '0', overflow: 'hidden', pointerEvents: 'none', zIndex: '0' }}>
<div ref={chiyoLayerRef} style={{ position: 'absolute', inset: '0', opacity: '.94', filter: 'saturate(1.05)' }}>
{CHIYO_FRAMES.map((f) => (
<img key={f} src={`/chiyo/s-${String(f).padStart(2, '0')}.jpg`} alt="" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', opacity: chiyoFrame === f ? 1 : 0, transition: 'opacity .06s linear' }} />
))}
</div>
<div style={{ position: 'absolute', inset: '0', background: '#241531', opacity: veilOpacity, mixBlendMode: 'multiply' }}></div>
<div style={{ position: 'absolute', inset: '0', background: 'radial-gradient(ellipse 70% 60% at 78% 45%, transparent 0%, rgba(26,15,38,.28) 78%)' }}></div>
</div>
<div style={{ position: 'fixed', inset: '0', pointerEvents: 'none', zIndex: '1', background: '#fafaf5', opacity: scrimOpacity }}></div>
</>)}

<div style={{ position: 'fixed', inset: '0', overflow: 'hidden', pointerEvents: 'none', zIndex: '0', animation: 'inkIn 2.6s ease-out both' }}>
<div style={{ position: 'absolute', left: '-4vw', bottom: '-16vh', height: '132vh', willChange: 'transform' }}>
<img src="/design/ink.svg" alt="" style={{ height: '100%', width: 'auto', display: 'block', opacity: '.12', mixBlendMode: 'multiply', transformOrigin: '50% 100%', animation: 'sway 26s ease-in-out infinite' }} />
</div>
<div style={{ position: 'absolute', right: '-12vw', bottom: '-28vh', height: '172vh', willChange: 'transform' }}>
<img src="/design/ink.svg" alt="" style={{ height: '100%', width: 'auto', display: 'block', opacity: '.075', mixBlendMode: 'multiply', transformOrigin: '50% 100%', animation: 'swayAlt 37s ease-in-out infinite' }} />
</div>
<div style={{ position: 'absolute', left: '36vw', bottom: '-10vh', height: '86vh', willChange: 'transform' }}>
<img src="/design/ink.svg" alt="" style={{ height: '100%', width: 'auto', display: 'block', opacity: '.05', filter: 'blur(1.4px)', mixBlendMode: 'multiply', transformOrigin: '50% 100%', animation: 'sway 46s ease-in-out infinite reverse' }} />
</div>
<div style={{ position: 'absolute', inset: '0', background: 'radial-gradient(ellipse 64% 54% at 44% 40%, rgba(250,250,245,.88) 0%, rgba(250,250,245,.52) 46%, rgba(250,250,245,0) 80%)' }}></div>
</div>
<canvas ref={fieldRef} style={{ position: 'fixed', inset: '0', width: '100%', height: '100%', pointerEvents: 'none', zIndex: '1' }}></canvas>
<div style={{ backgroundImage: 'linear-gradient(#9a9a92 1px, transparent 1px), linear-gradient(90deg, #9a9a92 1px, transparent 1px)', backgroundSize: '32px 32px', opacity: '.055', position: 'fixed', inset: '0', pointerEvents: 'none', zIndex: '1', animation: 'gridDrift 24s linear infinite' }}></div>

<div ref={ringRef} style={{ position: 'fixed', top: '0', left: '0', width: '34px', height: '34px', border: '1px solid rgba(26,28,25,.45)', borderRadius: '9999px', pointerEvents: 'none', zIndex: '9999', opacity: '0', transform: 'translate3d(-100px,-100px,0)', transition: 'width .25s ease, height .25s ease, background-color .25s ease, border-color .25s ease' }}></div>
<div ref={dotRef} style={{ position: 'fixed', top: '0', left: '0', width: '5px', height: '5px', background: '#1a1c19', borderRadius: '9999px', pointerEvents: 'none', zIndex: '9999', opacity: '0', transform: 'translate3d(-100px,-100px,0)' }}></div>

<div style={{ position: 'fixed', top: '0', left: '0', right: '0', height: '2px', background: 'transparent', zIndex: '60', pointerEvents: 'none' }}>
<div ref={progressRef} style={{ height: '100%', width: '100%', background: 'var(--accent)', transformOrigin: '0 50%', transform: 'scaleX(0)' }}></div>
</div>

<aside style={{ height: '100vh', width: asideWidth, position: 'fixed', top: '0', left: '0', borderRight: '1px solid #c4c7c7', backgroundColor: asideBg, backgroundImage: asideBgImage, backgroundSize: 'cover', backgroundPosition: 'center', backgroundRepeat: 'no-repeat', display: 'flex', flexDirection: 'column', padding: '28px 24px', zIndex: '50', boxSizing: 'border-box', transition: 'width .35s cubic-bezier(.16,1,.3,1)' }}>
<button className="dch-1" onClick={toggleSidebar} style={{ position: 'absolute', top: '24px', right: '-13px', width: '26px', height: '26px', borderRadius: '9999px', border: '1px solid #c4c7c7', background: '#fafaf5', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', zIndex: '51', padding: '0' }}>
<span style={{ fontFamily: '\'Material Symbols Outlined\'', fontVariationSettings: '\'wght\' 400,\'opsz\' 24', fontSize: '15px', lineHeight: '1', color: '#444748' }}>{sidebarIcon}</span>
</button>
<div style={{ marginBottom: '36px' }}>
<h1 style={{ fontSize: '12px', lineHeight: '16px', fontWeight: '600', letterSpacing: '.18em', color: '#000', margin: '0 0 5px 0', whiteSpace: 'nowrap' }}>S. RAWAT</h1>
{sidebarExpanded && (<>
<p style={{ fontSize: '10px', lineHeight: '14px', fontWeight: '500', letterSpacing: '.16em', color: '#444748', margin: '0', whiteSpace: 'nowrap' }}>APPLIED AI · EMBEDDED</p>
</>)}
</div>
<nav style={{ flexGrow: '1', position: 'relative' }}>
<div style={{ position: 'absolute', left: '-24px', top: '0', width: '2px', height: '36px', background: 'var(--accent)', transition: 'transform .5s cubic-bezier(.16,1,.3,1)', transform: navIndicator }}></div>
<div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
<a className="dch-2" href="#home" onClick={navClick} data-nav="0" style={{ display: 'flex', alignItems: 'center', gap: '12px', height: '36px', color: '#444748', transition: 'color .3s ease, padding-left .35s cubic-bezier(.16,1,.3,1)' }}>
<span style={{ fontFamily: '\'Material Symbols Outlined\'', fontVariationSettings: '\'FILL\' 0,\'wght\' 300,\'GRAD\' 0,\'opsz\' 24', fontSize: '19px', lineHeight: '1' }}>home</span>
{sidebarExpanded && (<><span style={{ fontSize: '11px', fontWeight: '600', letterSpacing: '.14em', textTransform: 'uppercase', whiteSpace: 'nowrap' }}>Home</span></>)}
</a>
<a className="dch-2" href="#projects" onClick={navClick} data-nav="1" style={{ display: 'flex', alignItems: 'center', gap: '12px', height: '36px', color: '#444748', transition: 'color .3s ease, padding-left .35s cubic-bezier(.16,1,.3,1)' }}>
<span style={{ fontFamily: '\'Material Symbols Outlined\'', fontVariationSettings: '\'FILL\' 0,\'wght\' 300,\'GRAD\' 0,\'opsz\' 24', fontSize: '19px', lineHeight: '1' }}>biotech</span>
{sidebarExpanded && (<><span style={{ fontSize: '11px', fontWeight: '600', letterSpacing: '.14em', textTransform: 'uppercase', whiteSpace: 'nowrap' }}>Work</span></>)}
</a>
<a className="dch-2" href="#about" onClick={navClick} data-nav="2" style={{ display: 'flex', alignItems: 'center', gap: '12px', height: '36px', color: '#444748', transition: 'color .3s ease, padding-left .35s cubic-bezier(.16,1,.3,1)' }}>
<span style={{ fontFamily: '\'Material Symbols Outlined\'', fontVariationSettings: '\'FILL\' 0,\'wght\' 300,\'GRAD\' 0,\'opsz\' 24', fontSize: '19px', lineHeight: '1' }}>person</span>
{sidebarExpanded && (<><span style={{ fontSize: '11px', fontWeight: '600', letterSpacing: '.14em', textTransform: 'uppercase', whiteSpace: 'nowrap' }}>About</span></>)}
</a>
<a className="dch-2" href="#skills" onClick={navClick} data-nav="3" style={{ display: 'flex', alignItems: 'center', gap: '12px', height: '36px', color: '#444748', transition: 'color .3s ease, padding-left .35s cubic-bezier(.16,1,.3,1)' }}>
<span style={{ fontFamily: '\'Material Symbols Outlined\'', fontVariationSettings: '\'FILL\' 0,\'wght\' 300,\'GRAD\' 0,\'opsz\' 24', fontSize: '19px', lineHeight: '1' }}>psychology</span>
{sidebarExpanded && (<><span style={{ fontSize: '11px', fontWeight: '600', letterSpacing: '.14em', textTransform: 'uppercase', whiteSpace: 'nowrap' }}>Stack</span></>)}
</a>
<a className="dch-2" href="#education" onClick={navClick} data-nav="4" style={{ display: 'flex', alignItems: 'center', gap: '12px', height: '36px', color: '#444748', transition: 'color .3s ease, padding-left .35s cubic-bezier(.16,1,.3,1)' }}>
<span style={{ fontFamily: '\'Material Symbols Outlined\'', fontVariationSettings: '\'FILL\' 0,\'wght\' 300,\'GRAD\' 0,\'opsz\' 24', fontSize: '19px', lineHeight: '1' }}>school</span>
{sidebarExpanded && (<><span style={{ fontSize: '11px', fontWeight: '600', letterSpacing: '.14em', textTransform: 'uppercase', whiteSpace: 'nowrap' }}>Education</span></>)}
</a>
<a className="dch-2" href="#interests" onClick={navClick} data-nav="5" style={{ display: 'flex', alignItems: 'center', gap: '12px', height: '36px', color: '#444748', transition: 'color .3s ease, padding-left .35s cubic-bezier(.16,1,.3,1)' }}>
<span style={{ fontFamily: '\'Material Symbols Outlined\'', fontVariationSettings: '\'FILL\' 0,\'wght\' 300,\'GRAD\' 0,\'opsz\' 24', fontSize: '19px', lineHeight: '1' }}>interests</span>
{sidebarExpanded && (<><span style={{ fontSize: '11px', fontWeight: '600', letterSpacing: '.14em', textTransform: 'uppercase', whiteSpace: 'nowrap' }}>Interests</span></>)}
</a>
<a className="dch-2" href="#contact" onClick={navClick} data-nav="6" style={{ display: 'flex', alignItems: 'center', gap: '12px', height: '36px', color: '#444748', transition: 'color .3s ease, padding-left .35s cubic-bezier(.16,1,.3,1)' }}>
<span style={{ fontFamily: '\'Material Symbols Outlined\'', fontVariationSettings: '\'FILL\' 0,\'wght\' 300,\'GRAD\' 0,\'opsz\' 24', fontSize: '19px', lineHeight: '1' }}>alternate_email</span>
{sidebarExpanded && (<><span style={{ fontSize: '11px', fontWeight: '600', letterSpacing: '.14em', textTransform: 'uppercase', whiteSpace: 'nowrap' }}>Contact</span></>)}
</a>
</div>
</nav>
<div style={{ display: 'flex', flexDirection: 'column', gap: '8px', paddingTop: '20px', borderTop: '1px solid rgba(196,199,199,.6)' }}>
<div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
<span style={{ width: '7px', height: '7px', borderRadius: '9999px', background: 'var(--accent)', animation: 'soft-pulse 2.4s cubic-bezier(.4,0,.6,1) infinite' }}></span>
{sidebarExpanded && (<><span style={{ fontSize: '9px', fontWeight: '600', letterSpacing: '.14em', textTransform: 'uppercase', color: '#1a1c19', whiteSpace: 'nowrap' }}>Open for freelance</span></>)}
</div>
{sidebarExpanded && (<><span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#747878', letterSpacing: '.04em', whiteSpace: 'nowrap' }}>IST {clock}</span></>)}
</div>
</aside>

<main style={{ marginLeft: mainMarginLeft, minHeight: '100vh', position: 'relative', zIndex: '2', transition: 'margin-left .35s cubic-bezier(.16,1,.3,1)' }}>
<div style={{ maxWidth: '1240px', margin: '0 auto', width: '100%', padding: '0 48px', boxSizing: 'border-box' }}>

<section id="home" style={{ padding: '104px 0 72px 0' }}>
<div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '26px', overflow: 'hidden' }}>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', letterSpacing: '.22em', textTransform: 'uppercase', color: '#747878', animation: 'fadeUp .7s ease-out both', animationDelay: '.05s', ...(projMetaExtra) }}>Applied AI Systems Engineer</span>
<span style={{ flex: '1', height: '1px', background: '#c4c7c7', transformOrigin: '0 50%', animation: 'ruleGrow 1.1s cubic-bezier(.16,1,.3,1) both', animationDelay: '.15s' }}></span>
{chiyoMode && (<>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', letterSpacing: '.14em', textTransform: 'uppercase', color: '#8a8d8d', whiteSpace: 'nowrap', ...(projMetaExtra) }}>Slaps landed {chiyoSlapCount}</span>
</>)}
<button className="dch-3" onClick={toggleChiyo} style={{ display: 'inline-flex', alignItems: 'center', gap: '7px', border: '1px solid #c4c7c7', backgroundColor: 'rgba(250,250,245,.55)', backgroundImage: 'linear-gradient(100deg,rgba(255,255,255,0) 18%,color-mix(in oklch, var(--accent) 34%, transparent) 44%,rgba(255,255,255,0) 70%)', backgroundSize: '220% 100%', backgroundRepeat: 'no-repeat', animation: 'chiyoSheen 4.2s linear infinite', padding: '7px 13px', cursor: 'pointer', fontFamily: 'inherit', whiteSpace: 'nowrap', transition: 'border-color .3s ease' }}>
<span style={{ fontFamily: '\'Material Symbols Outlined\'', fontVariationSettings: `'FILL' ${chiyoFill},'wght' 400,'GRAD' 0,'opsz' 24`, fontSize: '15px', lineHeight: '1', color: chiyoIconColor }}>bolt</span>
<span style={{ fontSize: '9px', fontWeight: '600', letterSpacing: '.14em', textTransform: 'uppercase', color: '#1a1c19' }}>Chiyo mode</span>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '9px', letterSpacing: '.1em', color: chiyoIconColor }}>{chiyoStatusLabel}</span>
</button>
</div>
<h2 style={{ fontFamily: 'Bitter,serif', fontWeight: '300', fontSize: 'clamp(56px,9.4vw,132px)', lineHeight: '.88', letterSpacing: '-.025em', textTransform: 'uppercase', margin: '0', color: '#111' }}>
<span style={{ display: 'block', overflow: 'hidden', paddingBottom: '.04em' }}><span style={{ display: 'block', animation: 'maskUp .95s cubic-bezier(.16,1,.3,1) both', animationDelay: '.1s' }}>Samarth</span></span>
<span style={{ display: 'block', overflow: 'hidden', paddingBottom: '.04em' }}><span style={{ display: 'block', animation: 'maskUp .95s cubic-bezier(.16,1,.3,1) both', animationDelay: '.22s' }}>Singh Rawat</span></span>
</h2>
<div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1.15fr) minmax(0,1fr)', gap: '56px', marginTop: '44px', alignItems: 'end' }}>
<div style={{ animation: 'fadeUp .8s ease-out both', animationDelay: '.5s' }}>
<p style={{ fontFamily: 'Bitter,serif', fontSize: '21px', lineHeight: '1.5', color: '#1a1c19', margin: '0 0 26px 0', maxWidth: '44ch', textWrap: 'pretty' }}>I build AI-driven applications and embedded systems — from real-time LLM products to firmware running on 400KB of RAM. Available for freelance work.</p>
<div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
<a className="dch-4" href="mailto:samarthrawat18@email.com" style={{ display: 'inline-flex', alignItems: 'center', gap: '10px', background: '#111', color: '#fafaf5', padding: '14px 24px', fontSize: '10px', fontWeight: '600', letterSpacing: '.16em', textTransform: 'uppercase', transition: 'transform .35s cubic-bezier(.16,1,.3,1), background-color .3s ease' }}>Start a project <span style={{ fontFamily: '\'Material Symbols Outlined\'', fontVariationSettings: '\'FILL\' 0,\'wght\' 300,\'GRAD\' 0,\'opsz\' 24', fontSize: '16px', lineHeight: '1' }}>arrow_outward</span></a>
<a className="dch-5" href="/Samarth_Updated_resume26.pdf" download="download" style={{ display: 'inline-flex', alignItems: 'center', gap: '10px', border: '1px solid #747878', padding: '14px 24px', fontSize: '10px', fontWeight: '600', letterSpacing: '.16em', textTransform: 'uppercase', color: '#111', transition: 'transform .35s cubic-bezier(.16,1,.3,1), background-color .3s ease' }}>Download resume <span style={{ fontFamily: '\'Material Symbols Outlined\'', fontVariationSettings: '\'FILL\' 0,\'wght\' 300,\'GRAD\' 0,\'opsz\' 24', fontSize: '16px', lineHeight: '1' }}>download</span></a>
</div>
</div>
<div style={{ border: '1px solid #c4c7c7', background: 'rgba(244,244,239,.72)', backdropFilter: 'blur(2px)', padding: '18px 20px', animation: 'fadeUp .8s ease-out both', animationDelay: '.62s' }}>
<div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '12px', marginBottom: '14px', borderBottom: '1px solid #c4c7c7' }}>
<h3 style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', fontWeight: '500', letterSpacing: '.16em', textTransform: 'uppercase', margin: '0', color: '#444748' }}>System dashboard</h3>
<span style={{ width: '7px', height: '7px', borderRadius: '9999px', background: 'var(--accent)', animation: 'soft-pulse 2.4s cubic-bezier(.4,0,.6,1) infinite' }}></span>
</div>
<div style={{ display: 'flex', flexDirection: 'column', gap: '13px' }}>
<div style={{ display: 'grid', gridTemplateColumns: '78px 1fr', gap: '12px', alignItems: 'baseline' }}>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '9px', letterSpacing: '.14em', textTransform: 'uppercase', color: '#8a8d8d' }}>Now</span>
<span style={{ fontSize: '13px', lineHeight: '1.45', color: '#1a1c19', minHeight: '19px' }}>{ticker}<span style={{ animation: 'blink 1s step-end infinite', color: 'var(--accent)' }}>▌</span></span>
</div>
<div style={{ display: 'grid', gridTemplateColumns: '78px 1fr', gap: '12px', alignItems: 'baseline' }}>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '9px', letterSpacing: '.14em', textTransform: 'uppercase', color: '#8a8d8d' }}>Based</span>
<span style={{ fontSize: '13px', lineHeight: '1.45', color: '#1a1c19' }}>Bhubaneswar, Odisha, India</span>
</div>
<div style={{ display: 'grid', gridTemplateColumns: '78px 1fr', gap: '12px', alignItems: 'baseline' }}>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '9px', letterSpacing: '.14em', textTransform: 'uppercase', color: '#8a8d8d' }}>Focus</span>
<span style={{ fontSize: '13px', lineHeight: '1.45', color: '#1a1c19' }}>Agentic AI · Embedded Systems</span>
</div>
<div style={{ display: 'grid', gridTemplateColumns: '78px 1fr', gap: '12px', alignItems: 'baseline' }}>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '9px', letterSpacing: '.14em', textTransform: 'uppercase', color: '#8a8d8d' }}>Local</span>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '13px', lineHeight: '1.45', color: '#1a1c19' }}>{clockFull}</span>
</div>
</div>
</div>
</div>
</section>

<section id="projects" data-reveal="1" style={{ paddingBottom: '8px' }}>
<div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '22px' }}>
<div>
<p style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', letterSpacing: '.2em', textTransform: 'uppercase', color: '#8a8d8d', margin: '0 0 6px 0' }}>01 — Selected work</p>
<h2 style={{ fontFamily: 'Bitter,serif', fontWeight: '400', fontSize: '34px', lineHeight: '1.1', textTransform: 'uppercase', letterSpacing: '-.01em', margin: '0' }}>Projects / Open-Source</h2>
</div>
<a className="dch-6" href="https://drive.google.com/drive/folders/1vqfYWG1C3KA-rb_5DO1uI2awG5tGS_9O?usp=sharing" target="_blank" rel="noopener noreferrer" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '10px', fontWeight: '600', letterSpacing: '.14em', textTransform: 'uppercase', color: '#444748', borderBottom: '1px solid #c4c7c7', paddingBottom: '3px', transition: 'color .3s ease, border-color .3s ease' }}>View all <span style={{ fontFamily: '\'Material Symbols Outlined\'', fontVariationSettings: '\'FILL\' 0,\'wght\' 300,\'GRAD\' 0,\'opsz\' 24', fontSize: '15px', lineHeight: '1' }}>arrow_outward</span></a>
</div>
<div style={{ borderTop: '1px solid #c4c7c7' }}>
<div className="dch-7" onClick={open0} data-reveal="1" style={{ display: 'grid', gridTemplateColumns: '40px minmax(0,1.25fr) minmax(0,1fr) 138px', gap: '22px', alignItems: 'start', padding: '26px 8px', borderBottom: '1px solid #c4c7c7', cursor: 'pointer', transition: 'background-color .4s ease, padding-left .4s cubic-bezier(.16,1,.3,1)' }}>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '11px', color: '#8a8d8d', paddingTop: '5px' }}>/01</span>
<div>
<h3 style={{ fontFamily: 'Bitter,serif', fontWeight: '400', fontSize: 'clamp(20px,1.75vw,27px)', lineHeight: '1.15', margin: '0 0 6px 0', letterSpacing: '-.01em', overflowWrap: 'break-word', hyphens: 'auto' }}>Critic-OS</h3>
<p style={{ fontSize: '11px', letterSpacing: '.12em', textTransform: 'uppercase', color: '#747878', margin: '0', ...(projMetaExtra) }}>AI-driven web application</p>
</div>
<div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
<p style={{ fontSize: '13px', lineHeight: '1.62', color: '#444748', margin: '0', textWrap: 'pretty' }}>Real-time satirical music critiques from 6 distinct AI personas, with a parallel enrichment engine that analyses a playlist in under 6 seconds.</p>
<div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
<span className="dch-8" style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '3px 8px', transition: 'background-color .25s ease,border-color .25s ease,color .25s ease' }}>Flask</span>
<span className="dch-8" style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '3px 8px', transition: 'background-color .25s ease,border-color .25s ease,color .25s ease' }}>Groq · Llama-3.3</span>
<span className="dch-8" style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '3px 8px', transition: 'background-color .25s ease,border-color .25s ease,color .25s ease' }}>HuggingFace</span>
<span className="dch-8" style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '3px 8px', transition: 'background-color .25s ease,border-color .25s ease,color .25s ease' }}>Redis</span>
<span className="dch-8" style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '3px 8px', transition: 'background-color .25s ease,border-color .25s ease,color .25s ease' }}>Spotify API</span>
</div>
</div>
<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '12px', paddingTop: '4px' }}>
<span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', letterSpacing: '.1em', textTransform: 'uppercase', color: '#747878' }}><span style={{ width: '6px', height: '6px', borderRadius: '9999px', background: 'var(--accent)' }}></span>Completed</span>
<span style={{ display: 'inline-flex', alignItems: 'center', gap: '7px', fontSize: '10px', fontWeight: '600', letterSpacing: '.14em', textTransform: 'uppercase', color: '#111' }}>Case study <span style={{ fontFamily: '\'Material Symbols Outlined\'', fontVariationSettings: '\'FILL\' 0,\'wght\' 300,\'GRAD\' 0,\'opsz\' 24', fontSize: '17px', lineHeight: '1' }}>arrow_forward</span></span>
</div>
</div>
<div className="dch-7" onClick={open1} data-reveal="1" style={{ display: 'grid', gridTemplateColumns: '40px minmax(0,1.25fr) minmax(0,1fr) 138px', gap: '22px', alignItems: 'start', padding: '26px 8px', borderBottom: '1px solid #c4c7c7', cursor: 'pointer', transition: 'background-color .4s ease, padding-left .4s cubic-bezier(.16,1,.3,1)' }}>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '11px', color: '#8a8d8d', paddingTop: '5px' }}>/02</span>
<div>
<h3 style={{ fontFamily: 'Bitter,serif', fontWeight: '400', fontSize: 'clamp(20px,1.75vw,27px)', lineHeight: '1.15', margin: '0 0 6px 0', letterSpacing: '-.01em', overflowWrap: 'break-word', hyphens: 'auto' }}>IoT Smart Alarm Clock</h3>
<p style={{ fontSize: '11px', letterSpacing: '.12em', textTransform: 'uppercase', color: '#747878', margin: '0', ...(projMetaExtra) }}>ESP32-C3 embedded system</p>
</div>
<div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
<p style={{ fontSize: '13px', lineHeight: '1.62', color: '#444748', margin: '0', textWrap: 'pretty' }}>A memory-constrained firmware architecture: custom .bin frame-streaming animation engine, 40% lower CPU overhead, 65% less BSS allocation.</p>
<div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
<span className="dch-8" style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '3px 8px', transition: 'background-color .25s ease,border-color .25s ease,color .25s ease' }}>ESP32-C3</span>
<span className="dch-8" style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '3px 8px', transition: 'background-color .25s ease,border-color .25s ease,color .25s ease' }}>C++</span>
<span className="dch-8" style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '3px 8px', transition: 'background-color .25s ease,border-color .25s ease,color .25s ease' }}>LittleFS</span>
<span className="dch-8" style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '3px 8px', transition: 'background-color .25s ease,border-color .25s ease,color .25s ease' }}>I2C/SPI</span>
<span className="dch-8" style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '3px 8px', transition: 'background-color .25s ease,border-color .25s ease,color .25s ease' }}>FreeRTOS</span>
</div>
</div>
<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '12px', paddingTop: '4px' }}>
<span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', letterSpacing: '.1em', textTransform: 'uppercase', color: '#747878' }}><span style={{ width: '6px', height: '6px', borderRadius: '9999px', background: 'var(--accent)' }}></span>Completed</span>
<span style={{ display: 'inline-flex', alignItems: 'center', gap: '7px', fontSize: '10px', fontWeight: '600', letterSpacing: '.14em', textTransform: 'uppercase', color: '#111' }}>Case study <span style={{ fontFamily: '\'Material Symbols Outlined\'', fontVariationSettings: '\'FILL\' 0,\'wght\' 300,\'GRAD\' 0,\'opsz\' 24', fontSize: '17px', lineHeight: '1' }}>arrow_forward</span></span>
</div>
</div>
<div className="dch-7" onClick={open2} data-reveal="1" style={{ display: 'grid', gridTemplateColumns: '40px minmax(0,1.25fr) minmax(0,1fr) 138px', gap: '22px', alignItems: 'start', padding: '26px 8px', borderBottom: '1px solid #c4c7c7', cursor: 'pointer', transition: 'background-color .4s ease, padding-left .4s cubic-bezier(.16,1,.3,1)' }}>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '11px', color: '#8a8d8d', paddingTop: '5px' }}>/03</span>
<div>
<h3 style={{ fontFamily: 'Bitter,serif', fontWeight: '400', fontSize: 'clamp(20px,1.75vw,27px)', lineHeight: '1.15', margin: '0 0 6px 0', letterSpacing: '-.01em', overflowWrap: 'break-word', hyphens: 'auto' }}>ISL Gesture Recognition</h3>
<p style={{ fontSize: '11px', letterSpacing: '.12em', textTransform: 'uppercase', color: '#747878', margin: '0', ...(projMetaExtra) }}>Random Forest classifier</p>
</div>
<div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
<p style={{ fontSize: '13px', lineHeight: '1.62', color: '#444748', margin: '0', textWrap: 'pretty' }}>Landmark and movement data from Indian Sign Language datasets, processed and classified with a trained Random Forest model.</p>
<div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
<span className="dch-8" style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '3px 8px', transition: 'background-color .25s ease,border-color .25s ease,color .25s ease' }}>Python</span>
<span className="dch-8" style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '3px 8px', transition: 'background-color .25s ease,border-color .25s ease,color .25s ease' }}>Scikit-learn</span>
<span className="dch-8" style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '3px 8px', transition: 'background-color .25s ease,border-color .25s ease,color .25s ease' }}>NumPy</span>
<span className="dch-8" style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '3px 8px', transition: 'background-color .25s ease,border-color .25s ease,color .25s ease' }}>Pandas</span>
</div>
</div>
<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '12px', paddingTop: '4px' }}>
<span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', letterSpacing: '.1em', textTransform: 'uppercase', color: '#747878' }}><span style={{ width: '6px', height: '6px', borderRadius: '9999px', background: 'var(--accent)' }}></span>Completed</span>
<span style={{ display: 'inline-flex', alignItems: 'center', gap: '7px', fontSize: '10px', fontWeight: '600', letterSpacing: '.14em', textTransform: 'uppercase', color: '#111' }}>Case study <span style={{ fontFamily: '\'Material Symbols Outlined\'', fontVariationSettings: '\'FILL\' 0,\'wght\' 300,\'GRAD\' 0,\'opsz\' 24', fontSize: '17px', lineHeight: '1' }}>arrow_forward</span></span>
</div>
</div>
<div className="dch-7" onClick={open3} data-reveal="1" style={{ display: 'grid', gridTemplateColumns: '40px minmax(0,1.25fr) minmax(0,1fr) 138px', gap: '22px', alignItems: 'start', padding: '26px 8px', borderBottom: '1px solid #c4c7c7', cursor: 'pointer', transition: 'background-color .4s ease, padding-left .4s cubic-bezier(.16,1,.3,1)' }}>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '11px', color: '#8a8d8d', paddingTop: '5px' }}>/04</span>
<div>
<h3 style={{ fontFamily: 'Bitter,serif', fontWeight: '400', fontSize: 'clamp(20px,1.75vw,27px)', lineHeight: '1.15', margin: '0 0 6px 0', letterSpacing: '-.01em', overflowWrap: 'break-word', hyphens: 'auto' }}>Movie Recommender</h3>
<p style={{ fontSize: '11px', letterSpacing: '.12em', textTransform: 'uppercase', color: '#747878', margin: '0', ...(projMetaExtra) }}>Collaborative filtering engine</p>
</div>
<div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
<p style={{ fontSize: '13px', lineHeight: '1.62', color: '#444748', margin: '0', textWrap: 'pretty' }}>Personalised movie suggestions from a collaborative filtering engine, with a lightweight web UI for input and results.</p>
<div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
<span className="dch-8" style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '3px 8px', transition: 'background-color .25s ease,border-color .25s ease,color .25s ease' }}>Python</span>
<span className="dch-8" style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '3px 8px', transition: 'background-color .25s ease,border-color .25s ease,color .25s ease' }}>Scikit-learn</span>
<span className="dch-8" style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '3px 8px', transition: 'background-color .25s ease,border-color .25s ease,color .25s ease' }}>NumPy</span>
<span className="dch-8" style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '3px 8px', transition: 'background-color .25s ease,border-color .25s ease,color .25s ease' }}>HTML</span>
</div>
</div>
<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '12px', paddingTop: '4px' }}>
<span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', letterSpacing: '.1em', textTransform: 'uppercase', color: '#747878' }}><span style={{ width: '6px', height: '6px', borderRadius: '9999px', background: 'var(--accent)' }}></span>Completed</span>
<span style={{ display: 'inline-flex', alignItems: 'center', gap: '7px', fontSize: '10px', fontWeight: '600', letterSpacing: '.14em', textTransform: 'uppercase', color: '#111' }}>Case study <span style={{ fontFamily: '\'Material Symbols Outlined\'', fontVariationSettings: '\'FILL\' 0,\'wght\' 300,\'GRAD\' 0,\'opsz\' 24', fontSize: '17px', lineHeight: '1' }}>arrow_forward</span></span>
</div>
</div>
</div>
</section>

<section id="about" data-reveal="1" style={{ padding: '72px 0 0 0' }}>
<p style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', letterSpacing: '.2em', textTransform: 'uppercase', color: '#8a8d8d', margin: '0 0 26px 0' }}>02 — Profile</p>
<div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr) minmax(0,1fr)', gap: '64px', alignItems: 'start' }}>
<div>
<p style={{ fontFamily: 'Bitter,serif', fontSize: '19px', lineHeight: '1.6', color: '#1a1c19', margin: '0 0 22px 0', textWrap: 'pretty' }}>Applied AI developer and B.Tech IT student at KIIT Bhubaneswar, specialising in interactive systems, behavioural architectures, and AI-enhanced user experiences.</p>
<p style={{ fontSize: '14px', lineHeight: '1.7', color: '#444748', margin: '0 0 28px 0', textWrap: 'pretty' }}>Experienced in integrating embedded systems, real-time interfaces, and intelligent workflow automation into cohesive, product-oriented applications that merge machine learning, IoT, and scalable web solutions.</p>
<div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,minmax(0,1fr))', gap: '20px', paddingTop: '22px', borderTop: '1px solid #c4c7c7' }}>
<div>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '9px', letterSpacing: '.16em', textTransform: 'uppercase', color: '#8a8d8d', display: 'block', marginBottom: '6px' }}>CGPA</span>
<span style={{ fontFamily: 'Bitter,serif', fontSize: '30px', fontWeight: '400', lineHeight: '1' }}>8.24</span>
</div>
<div>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '9px', letterSpacing: '.16em', textTransform: 'uppercase', color: '#8a8d8d', display: 'block', marginBottom: '6px' }}>Projects</span>
<span style={{ fontFamily: 'Bitter,serif', fontSize: '30px', fontWeight: '400', lineHeight: '1' }}>04</span>
</div>
<div>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '9px', letterSpacing: '.16em', textTransform: 'uppercase', color: '#8a8d8d', display: 'block', marginBottom: '6px' }}>Grad year</span>
<span style={{ fontFamily: 'Bitter,serif', fontSize: '30px', fontWeight: '400', lineHeight: '1' }}>2026</span>
</div>
</div>
</div>
<div id="skills">
<h3 style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', fontWeight: '500', letterSpacing: '.18em', textTransform: 'uppercase', color: '#444748', margin: '0 0 18px 0' }}>Technical stack</h3>
<div style={{ display: 'flex', flexDirection: 'column' }}>
<div className="dch-9" style={{ display: 'grid', gridTemplateColumns: '150px 1fr', gap: '20px', padding: '14px 0', borderTop: '1px solid #c4c7c7', transition: 'padding-left .35s cubic-bezier(.16,1,.3,1)' }}>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', letterSpacing: '.12em', textTransform: 'uppercase', color: '#8a8d8d' }}>Languages</span>
<span style={{ fontSize: '14px', lineHeight: '1.5', color: '#1a1c19' }}>Python, Java, C, HTML/CSS</span>
</div>
<div className="dch-9" style={{ display: 'grid', gridTemplateColumns: '150px 1fr', gap: '20px', padding: '14px 0', borderTop: '1px solid #c4c7c7', transition: 'padding-left .35s cubic-bezier(.16,1,.3,1)' }}>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', letterSpacing: '.12em', textTransform: 'uppercase', color: '#8a8d8d' }}>Frameworks</span>
<span style={{ fontSize: '14px', lineHeight: '1.5', color: '#1a1c19' }}>TensorFlow, Scikit-learn, NumPy, Pandas, Matplotlib</span>
</div>
<div className="dch-9" style={{ display: 'grid', gridTemplateColumns: '150px 1fr', gap: '20px', padding: '14px 0', borderTop: '1px solid #c4c7c7', transition: 'padding-left .35s cubic-bezier(.16,1,.3,1)' }}>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', letterSpacing: '.12em', textTransform: 'uppercase', color: '#8a8d8d' }}>Tools</span>
<span style={{ fontSize: '14px', lineHeight: '1.5', color: '#1a1c19' }}>Git, Power BI, Arduino, LaTeX, VS Code, Microsoft Office</span>
</div>
<div className="dch-9" style={{ display: 'grid', gridTemplateColumns: '150px 1fr', gap: '20px', padding: '14px 0', borderTop: '1px solid #c4c7c7', transition: 'padding-left .35s cubic-bezier(.16,1,.3,1)' }}>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', letterSpacing: '.12em', textTransform: 'uppercase', color: '#8a8d8d' }}>Data</span>
<span style={{ fontSize: '14px', lineHeight: '1.5', color: '#1a1c19' }}>MySQL</span>
</div>
<div className="dch-9" style={{ display: 'grid', gridTemplateColumns: '150px 1fr', gap: '20px', padding: '14px 0', borderTop: '1px solid #c4c7c7', borderBottom: '1px solid #c4c7c7', transition: 'padding-left .35s cubic-bezier(.16,1,.3,1)' }}>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', letterSpacing: '.12em', textTransform: 'uppercase', color: '#8a8d8d' }}>Platforms</span>
<span style={{ fontSize: '14px', lineHeight: '1.5', color: '#1a1c19' }}>ESP32, Spotify API</span>
</div>
</div>
</div>
</div>
</section>

<section data-reveal="1" style={{ padding: '72px 0 0 0', display: 'grid', gridTemplateColumns: 'minmax(0,1fr) minmax(0,1fr)', gap: '64px', alignItems: 'start' }}>
<div id="education">
<p style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', letterSpacing: '.2em', textTransform: 'uppercase', color: '#8a8d8d', margin: '0 0 26px 0' }}>03 — Education</p>
<div style={{ position: 'relative', paddingLeft: '26px' }}>
<div style={{ position: 'absolute', left: '3px', top: '6px', bottom: '6px', width: '1px', background: '#c4c7c7' }}></div>
<div style={{ position: 'relative', paddingBottom: '26px' }}>
<div style={{ position: 'absolute', left: '-26px', top: '5px', width: '7px', height: '7px', borderRadius: '9999px', background: 'var(--accent)' }}></div>
<p style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', letterSpacing: '.14em', color: '#8a8d8d', margin: '0 0 5px 0' }}>2026</p>
<h4 style={{ fontFamily: 'Bitter,serif', fontSize: '17px', fontWeight: '500', lineHeight: '1.3', margin: '0 0 3px 0' }}>Kalinga Institute of Industrial Technology</h4>
<p style={{ fontSize: '13px', color: '#444748', margin: '0' }}>B.Tech, Information Technology · Bhubaneswar · CGPA 8.24</p>
</div>
<div style={{ position: 'relative', paddingBottom: '26px' }}>
<div style={{ position: 'absolute', left: '-26px', top: '5px', width: '7px', height: '7px', borderRadius: '9999px', background: '#c4c7c7' }}></div>
<p style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', letterSpacing: '.14em', color: '#8a8d8d', margin: '0 0 5px 0' }}>2022</p>
<h4 style={{ fontFamily: 'Bitter,serif', fontSize: '17px', fontWeight: '500', lineHeight: '1.3', margin: '0 0 3px 0' }}>Lal Bahadur Shastri Public School</h4>
<p style={{ fontSize: '13px', color: '#444748', margin: '0' }}>12th Grade, CBSE · Kota · 79.4%</p>
</div>
<div style={{ position: 'relative' }}>
<div style={{ position: 'absolute', left: '-26px', top: '5px', width: '7px', height: '7px', borderRadius: '9999px', background: '#c4c7c7' }}></div>
<p style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', letterSpacing: '.14em', color: '#8a8d8d', margin: '0 0 5px 0' }}>2020</p>
<h4 style={{ fontFamily: 'Bitter,serif', fontSize: '17px', fontWeight: '500', lineHeight: '1.3', margin: '0 0 3px 0' }}>GMR DAV Varalakshmi Public School</h4>
<p style={{ fontSize: '13px', color: '#444748', margin: '0' }}>10th Grade, CBSE · Dhenkanal · 90%</p>
</div>
</div>
</div>
<div id="interests">
<p style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', letterSpacing: '.2em', textTransform: 'uppercase', color: '#8a8d8d', margin: '0 0 26px 0' }}>04 — Interests &amp; strengths</p>
<div style={{ display: 'flex', flexWrap: 'wrap', gap: '7px', marginBottom: '26px' }}>
<span className="dch-8" style={{ fontSize: '12px', letterSpacing: '.02em', border: '1px solid #c4c7c7', padding: '6px 12px', transition: 'background-color .3s ease, border-color .3s ease' }}>LLMs</span>
<span className="dch-8" style={{ fontSize: '12px', letterSpacing: '.02em', border: '1px solid #c4c7c7', padding: '6px 12px', transition: 'background-color .3s ease, border-color .3s ease' }}>Agentic AI</span>
<span className="dch-8" style={{ fontSize: '12px', letterSpacing: '.02em', border: '1px solid #c4c7c7', padding: '6px 12px', transition: 'background-color .3s ease, border-color .3s ease' }}>Fine tuning</span>
<span className="dch-8" style={{ fontSize: '12px', letterSpacing: '.02em', border: '1px solid #c4c7c7', padding: '6px 12px', transition: 'background-color .3s ease, border-color .3s ease' }}>Deep Learning</span>
<span className="dch-8" style={{ fontSize: '12px', letterSpacing: '.02em', border: '1px solid #c4c7c7', padding: '6px 12px', transition: 'background-color .3s ease, border-color .3s ease' }}>IoT Systems</span>
<span className="dch-8" style={{ fontSize: '12px', letterSpacing: '.02em', border: '1px solid #c4c7c7', padding: '6px 12px', transition: 'background-color .3s ease, border-color .3s ease' }}>Embedded Systems</span>
<span className="dch-8" style={{ fontSize: '12px', letterSpacing: '.02em', border: '1px solid #c4c7c7', padding: '6px 12px', transition: 'background-color .3s ease, border-color .3s ease' }}>Human-Computer Interaction</span>
<span className="dch-8" style={{ fontSize: '12px', letterSpacing: '.02em', border: '1px solid #c4c7c7', padding: '6px 12px', transition: 'background-color .3s ease, border-color .3s ease' }}>Data Visualization</span>
</div>
<div style={{ display: 'flex', flexDirection: 'column', gap: '14px', paddingTop: '22px', borderTop: '1px solid #c4c7c7' }}>
<p style={{ fontSize: '13px', lineHeight: '1.65', color: '#444748', margin: '0', textWrap: 'pretty' }}>Systems-oriented embedded developer experienced in modular ESP32 architecture, real-time interaction systems, and hardware-software integration.</p>
<p style={{ fontSize: '13px', lineHeight: '1.65', color: '#444748', margin: '0', textWrap: 'pretty' }}>Strong problem-solving and systems-thinking skills with focus on scalable, maintainable, and extensible design patterns.</p>
<p style={{ fontSize: '13px', lineHeight: '1.65', color: '#444748', margin: '0', textWrap: 'pretty' }}>Rapid prototyping and iterative development capability, with cross-domain exposure spanning embedded systems, UI/UX interaction design, and AI-assisted development tools.</p>
</div>
<div style={{ display: 'flex', flexWrap: 'wrap', gap: '18px', marginTop: '26px', paddingTop: '20px', borderTop: '1px solid #c4c7c7' }}>
<span style={{ display: 'inline-flex', alignItems: 'center', gap: '7px', fontSize: '11px', letterSpacing: '.1em', textTransform: 'uppercase', color: '#747878' }}><span style={{ fontFamily: '\'Material Symbols Outlined\'', fontVariationSettings: '\'wght\' 300,\'opsz\' 24', fontSize: '18px', lineHeight: '1' }}>menu_book</span>Reading</span>
<span style={{ display: 'inline-flex', alignItems: 'center', gap: '7px', fontSize: '11px', letterSpacing: '.1em', textTransform: 'uppercase', color: '#747878' }}><span style={{ fontFamily: '\'Material Symbols Outlined\'', fontVariationSettings: '\'wght\' 300,\'opsz\' 24', fontSize: '18px', lineHeight: '1' }}>movie_filter</span>Movies</span>
<span style={{ display: 'inline-flex', alignItems: 'center', gap: '7px', fontSize: '11px', letterSpacing: '.1em', textTransform: 'uppercase', color: '#747878' }}><span style={{ fontFamily: '\'Material Symbols Outlined\'', fontVariationSettings: '\'wght\' 300,\'opsz\' 24', fontSize: '18px', lineHeight: '1' }}>podcasts</span>Podcasts</span>
<span style={{ display: 'inline-flex', alignItems: 'center', gap: '7px', fontSize: '11px', letterSpacing: '.1em', textTransform: 'uppercase', color: '#747878' }}><span style={{ fontFamily: '\'Material Symbols Outlined\'', fontVariationSettings: '\'wght\' 300,\'opsz\' 24', fontSize: '18px', lineHeight: '1' }}>build</span>Building</span>
<span style={{ display: 'inline-flex', alignItems: 'center', gap: '7px', fontSize: '11px', letterSpacing: '.1em', textTransform: 'uppercase', color: '#747878' }}><span style={{ fontFamily: '\'Material Symbols Outlined\'', fontVariationSettings: '\'wght\' 300,\'opsz\' 24', fontSize: '18px', lineHeight: '1' }}>explore</span>Learning</span>
</div>
</div>
</section>

<section id="contact" data-reveal="1" style={{ padding: '96px 0 72px 0', marginTop: '72px', borderTop: '1px solid #c4c7c7' }}>
<div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1.3fr) minmax(0,1fr)', gap: '64px', alignItems: 'start' }}>
<div>
<h2 style={{ fontFamily: 'Bitter,serif', fontWeight: '300', fontSize: 'clamp(38px,5vw,64px)', lineHeight: '1.02', letterSpacing: '-.02em', margin: '0 0 24px 0', textTransform: 'uppercase' }}>Let's build<br />something</h2>
<a className="dch-10" href="mailto:samarthrawat18@email.com" style={{ display: 'inline-flex', alignItems: 'center', gap: '12px', fontFamily: 'Bitter,serif', fontSize: '22px', color: '#111', borderBottom: '1px solid #c4c7c7', paddingBottom: '6px', transition: 'border-color .35s ease, gap .35s cubic-bezier(.16,1,.3,1)' }}>samarthrawat18@email.com <span style={{ fontFamily: '\'Material Symbols Outlined\'', fontVariationSettings: '\'FILL\' 0,\'wght\' 300,\'GRAD\' 0,\'opsz\' 24', fontSize: '22px', lineHeight: '1' }}>arrow_outward</span></a>
</div>
<div style={{ display: 'flex', flexDirection: 'column', gap: '26px' }}>
<div style={{ display: 'grid', gridTemplateColumns: '80px 1fr', gap: '14px', alignItems: 'baseline' }}>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '9px', letterSpacing: '.16em', textTransform: 'uppercase', color: '#8a8d8d' }}>Phone</span>
<span style={{ fontSize: '13px', color: '#1a1c19' }}>+91 8984100922</span>
</div>
<div style={{ display: 'grid', gridTemplateColumns: '80px 1fr', gap: '14px', alignItems: 'baseline' }}>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '9px', letterSpacing: '.16em', textTransform: 'uppercase', color: '#8a8d8d' }}>Located</span>
<span style={{ fontSize: '13px', lineHeight: '1.55', color: '#1a1c19' }}>DGM-2 201, TATA Steel Meramandali Colony, Meramandali, Narendrapur, Odisha — 759121, India</span>
</div>
<div style={{ display: 'grid', gridTemplateColumns: '80px 1fr', gap: '14px', alignItems: 'baseline' }}>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '9px', letterSpacing: '.16em', textTransform: 'uppercase', color: '#8a8d8d' }}>Online</span>
<span style={{ display: 'flex', gap: '18px' }}>
<a className="dch-1" href="https://github.com/gentlewind-alt" target="_blank" rel="noopener noreferrer" style={{ fontSize: '13px', color: '#1a1c19', borderBottom: '1px solid #c4c7c7', paddingBottom: '2px', transition: 'border-color .3s ease' }}>GitHub</a>
<a className="dch-1" href="https://www.linkedin.com/in/samarth-rawat" target="_blank" rel="noopener noreferrer" style={{ fontSize: '13px', color: '#1a1c19', borderBottom: '1px solid #c4c7c7', paddingBottom: '2px', transition: 'border-color .3s ease' }}>LinkedIn</a>
</span>
</div>
</div>
</div>
<div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginTop: '80px', paddingTop: '22px', borderTop: '1px solid #c4c7c7' }}>
<p style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', letterSpacing: '.1em', color: '#8a8d8d', margin: '0' }}>© 2026 Samarth Singh Rawat</p>
<p style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', letterSpacing: '.1em', color: '#8a8d8d', margin: '0' }}>&gt; designed &amp; built with purpose</p>
</div>
</section>

</div>
</main>

{isOpen && (<>
<div onClick={closePanel} style={{ position: 'fixed', inset: '0', background: 'rgba(17,17,17,.32)', zIndex: '80', animation: 'backdropIn .35s ease-out both', backdropFilter: 'blur(2px)' }}></div>
<aside style={{ position: 'fixed', top: '0', right: '0', height: '100vh', width: 'min(660px,92vw)', background: '#fafaf5', borderLeft: '1px solid #c4c7c7', zIndex: '90', overflowY: 'auto', boxShadow: '-24px 0 60px rgba(17,17,17,.1)', animation: 'panelIn .5s cubic-bezier(.16,1,.3,1) both' }}>
<div style={{ position: 'sticky', top: '0', background: 'rgba(250,250,245,.94)', backdropFilter: 'blur(6px)', borderBottom: '1px solid #c4c7c7', display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '20px 40px', zIndex: '2' }}>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', letterSpacing: '.2em', textTransform: 'uppercase', color: '#8a8d8d' }}>Case study</span>
<button className="dch-11" onClick={closePanel} style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', background: 'none', border: '1px solid #c4c7c7', padding: '8px 14px', fontFamily: '\'IBM Plex Sans\',sans-serif', fontSize: '10px', fontWeight: '600', letterSpacing: '.14em', textTransform: 'uppercase', color: '#111', cursor: 'pointer', transition: 'background-color .3s ease, border-color .3s ease' }}>Close <span style={{ fontFamily: '\'Material Symbols Outlined\'', fontVariationSettings: '\'FILL\' 0,\'wght\' 300,\'GRAD\' 0,\'opsz\' 24', fontSize: '16px', lineHeight: '1' }}>close</span></button>
</div>
<div style={{ padding: '44px 40px 80px 40px' }}>

{open0Active && (<>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '11px', color: '#8a8d8d' }}>/01</span>
<h2 style={{ fontFamily: 'Bitter,serif', fontWeight: '300', fontSize: '48px', lineHeight: '1.05', letterSpacing: '-.02em', margin: '10px 0 8px 0' }}>Critic-OS</h2>
<p style={{ fontSize: '12px', letterSpacing: '.14em', textTransform: 'uppercase', color: '#747878', margin: '0 0 30px 0' }}>AI-driven web application · Completed</p>
<div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '34px' }}>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '4px 9px' }}>Python · Flask</span>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '4px 9px' }}>Groq · Llama-3.3</span>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '4px 9px' }}>HuggingFace</span>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '4px 9px' }}>Redis</span>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '4px 9px' }}>Spotify API</span>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '4px 9px' }}>Last.fm API</span>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '4px 9px' }}>Vercel</span>
</div>
<div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,minmax(0,1fr))', gap: '20px', padding: '22px 0', borderTop: '1px solid #c4c7c7', borderBottom: '1px solid #c4c7c7', marginBottom: '34px' }}>
<div><span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '9px', letterSpacing: '.16em', textTransform: 'uppercase', color: '#8a8d8d', display: 'block', marginBottom: '6px' }}>Personas</span><span style={{ fontFamily: 'Bitter,serif', fontSize: '28px' }}>6</span></div>
<div><span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '9px', letterSpacing: '.16em', textTransform: 'uppercase', color: '#8a8d8d', display: 'block', marginBottom: '6px' }}>Analysis</span><span style={{ fontFamily: 'Bitter,serif', fontSize: '28px' }}>&lt;6s</span></div>
<div><span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '9px', letterSpacing: '.16em', textTransform: 'uppercase', color: '#8a8d8d', display: 'block', marginBottom: '6px' }}>Runtime</span><span style={{ fontFamily: 'Bitter,serif', fontSize: '28px' }}>Serverless</span></div>
</div>
<div style={{ display: 'flex', flexDirection: 'column', gap: '26px' }}>
<div>
<h4 style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', fontWeight: '500', letterSpacing: '.18em', textTransform: 'uppercase', color: '#444748', margin: '0 0 10px 0' }}>The product</h4>
<p style={{ fontSize: '15px', lineHeight: '1.7', color: '#1a1c19', margin: '0', textWrap: 'pretty' }}>An AI-driven web application that generates real-time, satirical music critiques using Groq (Llama-3.3) and 6 distinct AI personas — from Gordon Ramsay to a cyberpunk hacker.</p>
</div>
<div>
<h4 style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', fontWeight: '500', letterSpacing: '.18em', textTransform: 'uppercase', color: '#444748', margin: '0 0 10px 0' }}>Enrichment engine</h4>
<p style={{ fontSize: '15px', lineHeight: '1.7', color: '#1a1c19', margin: '0', textWrap: 'pretty' }}>A parallel enrichment engine integrates Spotify, Last.fm, and LRC_LIB APIs with HuggingFace emotion classification, analysing a full user playlist in under 6 seconds.</p>
</div>
<div>
<h4 style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', fontWeight: '500', letterSpacing: '.18em', textTransform: 'uppercase', color: '#444748', margin: '0 0 10px 0' }}>Production</h4>
<p style={{ fontSize: '15px', lineHeight: '1.7', color: '#1a1c19', margin: '0', textWrap: 'pretty' }}>Optimised for Vercel Serverless with Redis-backed session management, keeping response times high and memory usage efficient under concurrent load.</p>
</div>
</div>
</>)}

{open1Active && (<>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '11px', color: '#8a8d8d' }}>/02</span>
<h2 style={{ fontFamily: 'Bitter,serif', fontWeight: '300', fontSize: '48px', lineHeight: '1.05', letterSpacing: '-.02em', margin: '10px 0 8px 0' }}>IoT Smart Alarm Clock</h2>
<p style={{ fontSize: '12px', letterSpacing: '.14em', textTransform: 'uppercase', color: '#747878', margin: '0 0 30px 0' }}>ESP32-C3 embedded system · Completed</p>
<div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '34px' }}>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '4px 9px' }}>ESP32-C3</span>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '4px 9px' }}>C++</span>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '4px 9px' }}>LittleFS</span>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '4px 9px' }}>I2C/SPI</span>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '4px 9px' }}>FreeRTOS</span>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '4px 9px' }}>Python · Asset packing</span>
</div>
<div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,minmax(0,1fr))', gap: '20px', padding: '22px 0', borderTop: '1px solid #c4c7c7', borderBottom: '1px solid #c4c7c7', marginBottom: '34px' }}>
<div><span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '9px', letterSpacing: '.16em', textTransform: 'uppercase', color: '#8a8d8d', display: 'block', marginBottom: '6px' }}>CPU overhead</span><span style={{ fontFamily: 'Bitter,serif', fontSize: '28px' }}>−40%</span></div>
<div><span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '9px', letterSpacing: '.16em', textTransform: 'uppercase', color: '#8a8d8d', display: 'block', marginBottom: '6px' }}>BSS memory</span><span style={{ fontFamily: 'Bitter,serif', fontSize: '28px' }}>−65%</span></div>
<div><span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '9px', letterSpacing: '.16em', textTransform: 'uppercase', color: '#8a8d8d', display: 'block', marginBottom: '6px' }}>Header check</span><span style={{ fontFamily: 'Bitter,serif', fontSize: '28px' }}>16-byte</span></div>
</div>
<div style={{ display: 'flex', flexDirection: 'column', gap: '26px' }}>
<div>
<h4 style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', fontWeight: '500', letterSpacing: '.18em', textTransform: 'uppercase', color: '#444748', margin: '0 0 10px 0' }}>Memory-constrained architecture</h4>
<p style={{ fontSize: '15px', lineHeight: '1.7', color: '#1a1c19', margin: '0', textWrap: 'pretty' }}>Engineered a custom .bin streaming animation engine to bypass ESP32-C3 RAM limitations, enabling high-quality animations via LittleFS frame-streaming with 16-byte header verification.</p>
</div>
<div>
<h4 style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', fontWeight: '500', letterSpacing: '.18em', textTransform: 'uppercase', color: '#444748', margin: '0 0 10px 0' }}>Resource optimisation</h4>
<p style={{ fontSize: '15px', lineHeight: '1.7', color: '#1a1c19', margin: '0', textWrap: 'pretty' }}>A multi-tier throttling strategy — I2C capping, sensor polling reduction with median filtering, and UI string caching — reduced CPU overhead by 40% and enhanced system stability.</p>
</div>
<div>
<h4 style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', fontWeight: '500', letterSpacing: '.18em', textTransform: 'uppercase', color: '#444748', margin: '0 0 10px 0' }}>Modular firmware design</h4>
<p style={{ fontSize: '15px', lineHeight: '1.7', color: '#1a1c19', margin: '0', textWrap: 'pretty' }}>A feature-toggle architecture cut BSS memory allocation by 65%, keeping compatibility with WiFi/BT stacks while maintaining a responsive, interrupt-driven multi-page menu system.</p>
</div>
<div>
<h4 style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', fontWeight: '500', letterSpacing: '.18em', textTransform: 'uppercase', color: '#444748', margin: '0 0 10px 0' }}>System reliability</h4>
<p style={{ fontSize: '15px', lineHeight: '1.7', color: '#1a1c19', margin: '0', textWrap: 'pretty' }}>A heterogeneous sensor suite (PIR, ultrasonic, IMU) drives gesture control and motion wake, synchronised with dual-source timekeeping (NTP + hardware RTC) for offline resilience.</p>
</div>
</div>
</>)}

{open2Active && (<>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '11px', color: '#8a8d8d' }}>/03</span>
<h2 style={{ fontFamily: 'Bitter,serif', fontWeight: '300', fontSize: '48px', lineHeight: '1.05', letterSpacing: '-.02em', margin: '10px 0 8px 0' }}>ISL Gesture Recognition</h2>
<p style={{ fontSize: '12px', letterSpacing: '.14em', textTransform: 'uppercase', color: '#747878', margin: '0 0 30px 0' }}>Random Forest classifier · Completed</p>
<div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '34px' }}>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '4px 9px' }}>Python</span>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '4px 9px' }}>Scikit-learn</span>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '4px 9px' }}>NumPy</span>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '4px 9px' }}>Pandas</span>
</div>
<div style={{ display: 'flex', flexDirection: 'column', gap: '26px' }}>
<div>
<h4 style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', fontWeight: '500', letterSpacing: '.18em', textTransform: 'uppercase', color: '#444748', margin: '0 0 10px 0' }}>Data pipeline</h4>
<p style={{ fontSize: '15px', lineHeight: '1.7', color: '#1a1c19', margin: '0', textWrap: 'pretty' }}>Processed Indian Sign Language hand gesture datasets in CSV format, carrying landmark and movement data per sample.</p>
</div>
<div>
<h4 style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', fontWeight: '500', letterSpacing: '.18em', textTransform: 'uppercase', color: '#444748', margin: '0 0 10px 0' }}>Model</h4>
<p style={{ fontSize: '15px', lineHeight: '1.7', color: '#1a1c19', margin: '0', textWrap: 'pretty' }}>Trained a Random Forest model to classify ISL gestures accurately, chosen for its robustness on tabular landmark features and its interpretability.</p>
</div>
</div>
</>)}

{open3Active && (<>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '11px', color: '#8a8d8d' }}>/04</span>
<h2 style={{ fontFamily: 'Bitter,serif', fontWeight: '300', fontSize: '48px', lineHeight: '1.05', letterSpacing: '-.02em', margin: '10px 0 8px 0' }}>Movie Recommender</h2>
<p style={{ fontSize: '12px', letterSpacing: '.14em', textTransform: 'uppercase', color: '#747878', margin: '0 0 30px 0' }}>Collaborative filtering engine · Completed</p>
<div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '34px' }}>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '4px 9px' }}>Python</span>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '4px 9px' }}>Scikit-learn</span>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '4px 9px' }}>NumPy</span>
<span style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', color: '#5e5e5e', border: '1px solid #d6d6d0', padding: '4px 9px' }}>HTML</span>
</div>
<div style={{ display: 'flex', flexDirection: 'column', gap: '26px' }}>
<div>
<h4 style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', fontWeight: '500', letterSpacing: '.18em', textTransform: 'uppercase', color: '#444748', margin: '0 0 10px 0' }}>Engine</h4>
<p style={{ fontSize: '15px', lineHeight: '1.7', color: '#1a1c19', margin: '0', textWrap: 'pretty' }}>Built a collaborative filtering engine to generate personalised movie suggestions from user rating patterns.</p>
</div>
<div>
<h4 style={{ fontFamily: '\'IBM Plex Mono\',monospace', fontSize: '10px', fontWeight: '500', letterSpacing: '.18em', textTransform: 'uppercase', color: '#444748', margin: '0 0 10px 0' }}>Interface</h4>
<p style={{ fontSize: '15px', lineHeight: '1.7', color: '#1a1c19', margin: '0', textWrap: 'pretty' }}>Processed large datasets and designed a simple web UI for user input and returned recommendations.</p>
</div>
</div>
</>)}

<div style={{ marginTop: '44px', paddingTop: '26px', borderTop: '1px solid #c4c7c7', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
<span style={{ fontSize: '13px', color: '#747878' }}>Want something like this built?</span>
<a className="dch-12" href="mailto:samarthrawat18@email.com" style={{ display: 'inline-flex', alignItems: 'center', gap: '10px', background: '#111', color: '#fafaf5', padding: '12px 22px', fontSize: '10px', fontWeight: '600', letterSpacing: '.16em', textTransform: 'uppercase', transition: 'transform .3s ease' }}>Get in touch <span style={{ fontFamily: '\'Material Symbols Outlined\'', fontVariationSettings: '\'FILL\' 0,\'wght\' 300,\'GRAD\' 0,\'opsz\' 24', fontSize: '16px', lineHeight: '1' }}>arrow_outward</span></a>
</div>
</div>
</aside>
</>)}

</div>

    </>
  );
}

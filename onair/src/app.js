/* 이채원 ON AIR — motion layer. The page reads complete without it; this file only adds motion. */
(() => {
  "use strict";
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const root = document.documentElement;
  const RM = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const FINE = matchMedia("(hover: hover) and (pointer: fine)").matches;
  const G = window.gsap, ST = window.ScrollTrigger;
  const HAS = !!(G && ST);
  const MOTION = HAS && !RM;
  const SCRAMBLE = HAS && !!window.ScrambleTextPlugin;
  const FLIP = HAS && !!window.Flip;
  root.classList.add("js");
  if (HAS) {
    G.registerPlugin(ST);
    if (SCRAMBLE) G.registerPlugin(window.ScrambleTextPlugin);
    if (FLIP) G.registerPlugin(window.Flip);
  }
  if (MOTION) root.classList.add("motion");
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, t) => a + (b - a) * t;
  const pad = (n) => String(n).padStart(2, "0");
  const KO = "가나다라마바사아자차카타파하채원온에어방송";

  /* ── film grain ── */
  (() => {
    const g = $(".grain"); if (!g) return;
    const c = document.createElement("canvas"); c.width = c.height = 160;
    const x = c.getContext("2d"); const d = x.createImageData(160, 160);
    for (let i = 0; i < d.data.length; i += 4) { const v = (Math.random() * 255) | 0; d.data[i] = d.data[i + 1] = d.data[i + 2] = v; d.data[i + 3] = 255; }
    x.putImageData(d, 0, 0);
    g.style.setProperty("--noise", `url(${c.toDataURL("image/png")})`);
  })();

  /* ── running timecode (30fps) ── */
  (() => {
    const els = $$(".js-tc"); if (!els.length) return;
    const t0 = performance.now(); let last = -1;
    const fmt = (f) => [Math.floor(f / 108000), Math.floor(f / 1800) % 60, Math.floor(f / 30) % 60, f % 30].map(pad).join(":");
    const tick = () => {
      let f = Math.floor((performance.now() - t0) / (1000 / 30));
      if (RM) f -= f % 30;
      if (f !== last) { last = f; const t = fmt(f); for (const e of els) e.textContent = t; }
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  })();

  /* ── date-aware labels: [data-when] shows data-future up to and including that day, data-past afterwards ── */
  (() => {
    const today = new Date(); today.setHours(0, 0, 0, 0);
    for (const el of $$("[data-when]")) {
      const past = new Date(el.dataset.when + "T00:00:00") < today;
      el.textContent = past ? el.dataset.past : el.dataset.future;
    }
  })();

  /* ── next race countdown (from the published schedule) ── */
  (() => {
    const items = $$(".upnext li"); if (!items.length) return;
    const today = new Date(); today.setHours(0, 0, 0, 0);
    let next = null;
    for (const li of items) {
      const d = new Date(li.dataset.date + "T00:00:00");
      const diff = Math.round((d - today) / 864e5);
      const st = $(".up-state", li);
      if (diff < 0) { li.classList.add("done"); st.textContent = "ON AIR ✓"; }
      else {
        st.textContent = diff === 0 ? "D-DAY" : `D-${diff}`;
        if (!next) { next = { li, diff, name: $("b", li).textContent, date: li.dataset.date }; li.classList.add("next"); }
      }
    }
    const el = $(".js-next");
    if (next && el) {
      el.innerHTML = `<i></i>NEXT ON AIR <b>${next.diff === 0 ? "D-DAY" : "D-" + next.diff}</b><span>${next.date.slice(5).replace("-", ".")} ${next.name}</span>`;
      el.hidden = false;
    }
  })();

  /* ── copy buttons + toast ── */
  const toastEl = $(".toast"); let toastT;
  const toast = (msg) => { if (!toastEl) return; toastEl.textContent = msg; toastEl.classList.add("show"); clearTimeout(toastT); toastT = setTimeout(() => toastEl.classList.remove("show"), 2200); };
  document.addEventListener("click", (e) => {
    const b = e.target.closest("[data-copy]"); if (!b) return;
    const v = b.dataset.copy;
    const fallback = () => {
      const t = b.closest(".c-row")?.querySelector("b");
      if (t) { const r = document.createRange(); r.selectNodeContents(t); const s = getSelection(); s.removeAllRanges(); s.addRange(r); }
      toast("선택했어요 · ⌘C 또는 Ctrl+C로 복사하세요");
    };
    try { navigator.clipboard.writeText(v).then(() => toast(`복사했어요 · ${v}`), fallback); } catch (_) { fallback(); }
  });

  /* ── mobile rundown menu ── */
  const menu = $("#menu"), menuBtn = $(".menu-btn");
  const closeMenu = () => { if (!menu || menu.hidden) return; menu.hidden = true; menuBtn?.setAttribute("aria-expanded", "false"); };
  menuBtn?.addEventListener("click", () => {
    menu.hidden = !menu.hidden; menuBtn.setAttribute("aria-expanded", String(!menu.hidden));
    if (!menu.hidden && MOTION) G.from($$("a", menu), { yPercent: 60, autoAlpha: 0, stagger: .05, duration: .6, ease: "expo.out" });
  });
  $(".menu-close")?.addEventListener("click", closeMenu);

  if (!HAS) return; // everything below is motion

  /* ── smooth scroll ── */
  let lenis = null;
  if (MOTION && FINE && window.Lenis) {
    lenis = new window.Lenis({ lerp: 0.1, wheelMultiplier: 0.95 });
    lenis.on("scroll", ST.update);
    G.ticker.add((t) => lenis.raf(t * 1000));
    G.ticker.lagSmoothing(0);
  }
  if (location.protocol === "file:") window.__onair = { lenis, ST, G }; // local QA hook only
  const scrollToEl = (el) => {
    if (!el) return;
    if (lenis) lenis.scrollTo(el, { duration: 1.5 });
    else el.scrollIntoView({ behavior: RM ? "auto" : "smooth" });
  };
  document.addEventListener("click", (e) => {
    const a = e.target.closest('a[href^="#"]'); if (!a) return;
    const id = a.getAttribute("href").slice(1); const el = id ? document.getElementById(id) : document.body;
    if (!el) return;
    e.preventDefault(); closeMenu(); scrollToEl(el);
  });

  /* ── split text into masked characters, words kept whole ── */
  function split(el) {
    if (!el) return [];
    if (el.dataset.splitDone) return $$(".ci", el);
    const text = el.textContent.trim();
    el.setAttribute("aria-label", text);
    el.textContent = "";
    text.split(/(\s+)/).forEach((word) => {
      if (/^\s+$/.test(word)) { el.append(document.createTextNode(" ")); return; }
      const w = document.createElement("span"); w.className = "w"; w.setAttribute("aria-hidden", "true");
      for (const ch of Array.from(word)) {
        const o = document.createElement("span"); o.className = "ch";
        const i = document.createElement("span"); i.className = "ci"; i.textContent = ch;
        o.append(i); w.append(o);
      }
      el.append(w);
    });
    el.dataset.splitDone = "1";
    return $$(".ci", el);
  }

  function segHead(sec) {
    const head = $(".seg-head", sec); if (!head) return;
    const title = $(".seg-title", head);
    if (title) {
      const chars = split(title);
      G.set(chars, { "--w": 900 });
      G.from(chars, { yPercent: 112, "--w": 100, duration: 1.15, ease: "expo.out", stagger: 0.032, scrollTrigger: { trigger: title, start: "top 88%", once: true } });
    }
    const meta = $(".seg-meta", head);
    if (meta) G.from(meta.children, { autoAlpha: 0, x: -12, duration: .6, stagger: .08, scrollTrigger: { trigger: meta, start: "top 90%", once: true } });
    const sub = $(".seg-sub", head);
    if (sub) G.from(sub, { autoAlpha: 0, y: 22, duration: 1, ease: "power3.out", scrollTrigger: { trigger: sub, start: "top 92%", once: true } });
  }

  /* ── hero ── */
  const heroSec = $(".hero");
  let glMouse = null;
  function heroGL() {
    const cvs = $(".hero-gl"); if (!cvs) return null;
    const gl = cvs.getContext("webgl", { antialias: false, alpha: false, powerPreference: "low-power" });
    if (!gl) return null;
    const vs = "attribute vec2 p;void main(){gl_Position=vec4(p,0.,1.);}";
    const fs = `precision mediump float;uniform vec2 r;uniform float t;uniform vec2 m;
      float h(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
      float n(vec2 p){vec2 i=floor(p),f=fract(p);vec2 u=f*f*(3.-2.*f);return mix(mix(h(i),h(i+vec2(1,0)),u.x),mix(h(i+vec2(0,1)),h(i+vec2(1,1)),u.x),u.y);}
      void main(){vec2 uv=gl_FragCoord.xy/r;float a=r.x/r.y;vec2 q=vec2(uv.x*a,uv.y);
        vec3 base=vec3(.996,.541,.678),deep=vec3(.86,.33,.52),hi=vec3(1.,.87,.92);
        float fl=n(q*1.4+vec2(t*.05,-t*.035))*.6+n(q*3.1-t*.06)*.4;
        vec3 col=mix(deep,base,smoothstep(-.15,.85,uv.y*.75+fl*.45));
        vec2 kl=vec2((.8+.07*sin(t*.21))*a,.84+.05*cos(t*.29));
        col=mix(col,hi,smoothstep(.8,0.,distance(q,kl))*.5);
        vec2 mm=vec2(m.x*a,m.y);col=mix(col,hi,smoothstep(.42,0.,distance(q,mm))*.24);
        float beam=smoothstep(.06,0.,abs(uv.x-.5-.35*sin(t*.12)+(1.-uv.y)*.25))*.07;col+=beam;
        col*=.84+.16*smoothstep(0.,.3,uv.y);col*=1.-.26*pow(length(uv-.5)*1.25,2.2);
        col+=(h(gl_FragCoord.xy+fract(t)*91.)-.5)*.03;gl_FragColor=vec4(col,1.);}`;
    const sh = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); return gl.getShaderParameter(s, gl.COMPILE_STATUS) ? s : null; };
    const v = sh(gl.VERTEX_SHADER, vs), f = sh(gl.FRAGMENT_SHADER, fs); if (!v || !f) return null;
    const pr = gl.createProgram(); gl.attachShader(pr, v); gl.attachShader(pr, f); gl.linkProgram(pr);
    if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) return null;
    gl.useProgram(pr);
    const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1]), gl.STATIC_DRAW);
    const loc = gl.getAttribLocation(pr, "p"); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    const uR = gl.getUniformLocation(pr, "r"), uT = gl.getUniformLocation(pr, "t"), uM = gl.getUniformLocation(pr, "m");
    let mouse = [0.72, 0.7], target = [0.72, 0.7], visible = true, raf = 0;
    const t0 = performance.now();
    const resize = () => {
      const dpr = Math.min(1.5, window.devicePixelRatio || 1);
      const w = (cvs.clientWidth * dpr) | 0, h = (cvs.clientHeight * dpr) | 0;
      if (cvs.width !== w || cvs.height !== h) { cvs.width = w; cvs.height = h; gl.viewport(0, 0, w, h); }
    };
    const loop = () => {
      if (!visible) { raf = 0; return; }
      resize();
      mouse[0] += (target[0] - mouse[0]) * 0.05; mouse[1] += (target[1] - mouse[1]) * 0.05;
      gl.uniform2f(uR, cvs.width, cvs.height); gl.uniform1f(uT, (performance.now() - t0) / 1000); gl.uniform2f(uM, mouse[0], mouse[1]);
      gl.drawArrays(gl.TRIANGLES, 0, 6);
      raf = requestAnimationFrame(loop);
    };
    new IntersectionObserver(([en]) => { visible = en.isIntersecting; if (visible && !raf) loop(); }).observe(cvs);
    cvs.classList.add("on"); loop();
    return (x, y) => { target = [x, y]; };
  }

  let heroIntro = null;
  if (heroSec && MOTION) {
    glMouse = heroGL();
    const word = split($(".hero-word"));
    const ko = split($(".hero-title .ko"));
    G.set(word, { "--w": 900 });
    const kick = $(".js-kicker"); const kickText = kick?.textContent || "";
    heroIntro = G.timeline({ paused: true, defaults: { ease: "expo.out" } });
    heroIntro
      .from(word, { yPercent: 118, "--w": 100, duration: 1.35, stagger: 0.06 }, 0)
      .from(".hero-cut", { yPercent: 9, autoAlpha: 0, scale: 1.05, filter: "blur(16px)", duration: 1.5 }, 0.12)
      .from(".vf-c", { scale: 1.9, autoAlpha: 0, duration: 0.7, stagger: 0.06, ease: "back.out(2)" }, 0.3)
      .from([".vf-rec", ".vf-spec", ".vf-meter", ".vf-cross", ".vf-focus"], { autoAlpha: 0, duration: 0.5, stagger: 0.07 }, 0.5)
      .from(ko, { yPercent: 108, duration: 1.05, stagger: 0.09 }, 0.32)
      .from(".hero-title .en", { autoAlpha: 0, letterSpacing: "0.7em", duration: 1.2 }, 0.5)
      .from(".hero-copy", { autoAlpha: 0, y: 18, duration: 0.9 }, 0.62)
      .from(".lt-tag", { xPercent: -100, autoAlpha: 0, duration: 0.6 }, 0.72)
      .from(".lt-main", { clipPath: "inset(0% 100% 0% 0%)", duration: 0.85, ease: "expo.inOut" }, 0.8)
      .from(".js-next", { autoAlpha: 0, y: 10, duration: 0.6 }, 1.1)
      .from(".crawl", { yPercent: 100, duration: 0.8 }, 0.55);
    if (SCRAMBLE && kick) heroIntro.set(kick, { textContent: "" }, 0).to(kick, { duration: 1.3, scrambleText: { text: kickText, chars: "ONAIR·0123456789", speed: 0.5 } }, 0.4);

    // autofocus: follows the face detected in the cutout (YuNet bbox, as fractions of the image box) every frame,
    // unless the pointer is steering it; turns green only once it has settled on the face
    const focus = $(".vf-focus"), vf = $(".vf"), cut = $(".hero-cut");
    const FACE = { cx: 0.4341, cy: 0.1597, w: 0.3871, h: 0.1649 };
    const faceBox = () => {
      const r = cut.getBoundingClientRect(), v = vf.getBoundingClientRect();
      const w = Math.max(64, r.width * FACE.w * 1.22), h = Math.max(64, r.height * FACE.h * 1.1);
      return { x: r.left - v.left + r.width * FACE.cx - w / 2, y: r.top - v.top + r.height * FACE.cy - h / 2, w, h };
    };
    let mode = "face", pointer = { x: 0, y: 0 }, heroOn = true;
    const t0 = faceBox();
    const af = { x: t0.x - t0.w * 0.3, y: t0.y - t0.h * 0.3, w: t0.w * 1.6, h: t0.h * 1.6 };
    new IntersectionObserver(([en]) => { heroOn = en.isIntersecting; }).observe(heroSec);
    G.ticker.add(() => {
      if (!heroOn) return;
      const t = mode === "face" ? faceBox() : { x: pointer.x - 59, y: pointer.y - 59, w: 118, h: 118 };
      const k = mode === "face" ? 0.14 : 0.24;
      af.x += (t.x - af.x) * k; af.y += (t.y - af.y) * k; af.w += (t.w - af.w) * k; af.h += (t.h - af.h) * k;
      G.set(focus, { x: af.x, y: af.y, width: af.w, height: af.h });
      focus.classList.toggle("lock", mode === "face" && Math.abs(t.x - af.x) < 2.5 && Math.abs(t.y - af.y) < 2.5 && Math.abs(t.w - af.w) < 2.5);
    });

    // pointer: depth parallax + studio key light + manual focus
    if (FINE) {
      const q = (t, p) => G.quickTo(t, p, { duration: 0.9, ease: "power3" });
      const wx = q(".hero-word", "x"), wy = q(".hero-word", "y"), fx = q(".hero-fig", "x"), fy = q(".hero-fig", "y"), vx = q(".vf", "x"), vy = q(".vf", "y");
      let idle;
      heroSec.addEventListener("pointermove", (e) => {
        const r = heroSec.getBoundingClientRect();
        const nx = (e.clientX - r.left) / r.width - 0.5, ny = (e.clientY - r.top) / r.height - 0.5;
        wx(nx * -34); wy(ny * -18); fx(nx * 20); fy(ny * 8); vx(nx * -6); vy(ny * -4);
        glMouse && glMouse(nx + 0.5, 0.5 - ny);
        const v = vf.getBoundingClientRect();
        pointer = { x: e.clientX - v.left, y: e.clientY - v.top }; mode = "pointer";
        clearTimeout(idle); idle = setTimeout(() => { mode = "face"; }, 1400);
      });
      heroSec.addEventListener("pointerleave", () => { clearTimeout(idle); mode = "face"; });
    }

    // audio meters dance while the hero is on screen
    const meters = $$(".vf-meter span i"); let mOn = true, lv = [0.3, 0.3];
    new IntersectionObserver(([en]) => { mOn = en.isIntersecting; }).observe(heroSec);
    G.ticker.add(() => {
      if (!mOn) return;
      const tt = performance.now() / 1000;
      lv = lv.map((l, k) => lerp(l, clamp(0.35 + 0.35 * Math.sin(tt * (3.1 + k)) * Math.sin(tt * 7.3 + k) + Math.random() * 0.3, 0.08, 0.98), 0.25));
      meters.forEach((m, k) => m.style.setProperty("--lv", (lv[k] * 100).toFixed(1) + "%"));
    });

    // the lower third cycles through her roles
    const role = $(".js-role");
    if (role && SCRAMBLE) {
      const roles = role.dataset.roles.split("|"); let ri = 0;
      setInterval(() => { if (document.hidden) return; ri = (ri + 1) % roles.length; G.to(role, { duration: 1, scrambleText: { text: roles[ri], chars: KO, speed: 0.6 } }); }, 3000);
    }
  }

  /* ── marquees: hero crawl + brand wall, steered by scroll velocity ── */
  const marquees = [];
  function marquee(track, dirSign, pxPerSec) {
    track.innerHTML += track.innerHTML;
    $$(":scope > *", track).slice(track.children.length / 2).forEach((n) => n.setAttribute("aria-hidden", "true"));
    if (!MOTION) return;
    const from = dirSign < 0 ? 0 : -50, to = dirSign < 0 ? -50 : 0;
    const tw = G.fromTo(track, { xPercent: from }, { xPercent: to, duration: Math.max(8, track.scrollWidth / 2 / pxPerSec), ease: "none", repeat: -1 });
    const m = { tw, boost: 1, dir: 1 };
    marquees.push(m);
    track.addEventListener("pointerenter", () => { m.hover = true; });
    track.addEventListener("pointerleave", () => { m.hover = false; });
  }
  const crawl = $(".crawl-track"); if (crawl) marquee(crawl, -1, 70);
  $$(".js-mq").forEach((mq) => marquee(mq, +mq.dataset.dir || -1, 60));
  if (MOTION && marquees.length) {
    let vel = 0;
    ST.create({ start: 0, end: "max", onUpdate: (s) => { vel = s.getVelocity(); } });
    G.ticker.add(() => {
      vel *= 0.92;
      const dir = vel < -5 ? -1 : 1;
      for (const m of marquees) {
        if (Math.abs(vel) > 5) m.dir = dir;
        const target = m.hover ? 0.15 : m.dir * (1 + Math.min(Math.abs(vel) / 260, 5));
        m.boost = lerp(m.boost, target, 0.08);
        m.tw.timeScale(m.boost);
      }
    });
  }

  /* ── odometer digits (scoreboard) ── */
  const odos = $$(".odo").map((o) => {
    const str = Number(o.dataset.to).toLocaleString("en-US");
    o.setAttribute("aria-label", str); o.textContent = "";
    const cols = [];
    for (const ch of str) {
      if (/\d/.test(ch)) {
        const c = document.createElement("span"); c.className = "odo-col"; c.setAttribute("aria-hidden", "true");
        const s = document.createElement("span"); s.className = "odo-strip";
        s.innerHTML = Array.from({ length: 20 }, (_, k) => `<span>${k % 10}</span>`).join("");
        c.append(s); o.append(c); cols.push({ s, d: +ch });
      } else { const sp = document.createElement("span"); sp.textContent = ch; sp.setAttribute("aria-hidden", "true"); o.append(sp); }
    }
    cols.forEach(({ s, d }) => G.set(s, { yPercent: -(10 + d) * 5 }));
    return { o, cols };
  });

  /* ── pass badge spring (profile) ── */
  function passSwing(sec) {
    const pass = $(".pass", sec); if (!pass) return () => {};
    let rot = 0, vel = 0, target = 0, lastX = null, on = false;
    const move = (e) => { if (lastX !== null) target = clamp(target + (e.clientX - lastX) * 0.35, -16, 16); lastX = e.clientX; };
    const tick = () => { if (!on) return; vel += (target - rot) * 0.07; vel *= 0.86; rot += vel; target *= 0.9; G.set(pass, { rotation: rot }); };
    sec.addEventListener("pointermove", move);
    const st = ST.create({ trigger: sec, start: "top bottom", end: "bottom top", onToggle: (s) => { on = s.isActive; }, onUpdate: (s) => { target = clamp(target + s.getVelocity() / 900, -16, 16); } });
    G.ticker.add(tick);
    return () => { sec.removeEventListener("pointermove", move); G.ticker.remove(tick); st.kill(); G.set(pass, { clearProps: "transform" }); };
  }

  /* ── tachometer (pit lane) ── */
  function buildGauge() {
    const svg = $(".js-gauge"); if (!svg) return null;
    const cx = 200, cy = 200, R = 172, MAX = 8, A0 = -120, A1 = 120;
    const ang = (v) => A0 + ((A1 - A0) * v) / MAX;
    const pt = (a, rr) => { const t = ((a - 90) * Math.PI) / 180; return [cx + rr * Math.cos(t), cy + rr * Math.sin(t)]; };
    const arc = (v0, v1, rr) => { const [x0, y0] = pt(ang(v0), rr), [x1, y1] = pt(ang(v1), rr); return `M${x0.toFixed(1)},${y0.toFixed(1)} A${rr},${rr} 0 0 1 ${x1.toFixed(1)},${y1.toFixed(1)}`; };
    let s = `<circle class="g-face" cx="200" cy="200" r="192"/><path class="g-red" d="${arc(6.5, 8, R - 9)}"/>`;
    for (let v = 0; v <= MAX + 1e-6; v += 0.25) {
      const major = Math.abs(v - Math.round(v)) < 1e-6, a = ang(v);
      const [x0, y0] = pt(a, R - (major ? 28 : 15)), [x1, y1] = pt(a, R - 2);
      s += `<line class="g-tick${v >= 6.5 ? " red" : ""}" x1="${x0.toFixed(1)}" y1="${y0.toFixed(1)}" x2="${x1.toFixed(1)}" y2="${y1.toFixed(1)}" stroke-width="${major ? 4 : 2}"/>`;
      if (major) { const [tx, ty] = pt(a, R - 50); s += `<text class="g-num" x="${tx.toFixed(1)}" y="${ty.toFixed(1)}" text-anchor="middle" dominant-baseline="central">${Math.round(v)}</text>`; }
    }
    s += `<text class="g-unit" x="200" y="132" text-anchor="middle">×1000 RPM</text><g class="g-needle"><path d="M195,206 L200,44 L205,206 Z"/><circle class="g-hub" cx="200" cy="200" r="13"/></g>`;
    svg.innerHTML = s;
    const needle = $(".g-needle", svg);
    G.set(needle, { rotation: ang(7.1), svgOrigin: "200 200" });
    return { needle, ang };
  }
  const gauge = buildGauge();

  /* ── channel static (idents + CRT) ── */
  function staticNoise(cvs, w, h) {
    const ctx = cvs.getContext("2d"); cvs.width = w; cvs.height = h;
    const img = ctx.createImageData(w, h);
    return () => { const d = img.data; for (let i = 0; i < d.length; i += 4) { const v = (Math.random() * 255) | 0; d[i] = d[i + 1] = d[i + 2] = v; d[i + 3] = 255; } ctx.putImageData(img, 0, 0); };
  }

  /* ── CRT + EPG (on TV) ── */
  (() => {
    const sec = $(".tv"); if (!sec) return;
    const slides = $$(".tv-slide", sec), btns = $$(".epg button", sec), osd = $(".js-osd", sec), cvs = $(".tv-static", sec);
    const noise = staticNoise(cvs, 120, 90);
    let cur = 0, hover = false, visible = false, timer = null;
    const show = (i) => {
      cur = i;
      btns.forEach((b, k) => { b.classList.toggle("on", k === i); b.setAttribute("aria-pressed", k === i ? "true" : "false"); });
      if (osd) osd.textContent = `CH ${i + 1} · ${slides[i].dataset.ch}`;
      slides.forEach((s, k) => s.classList.toggle("on", k === i));
      if (MOTION) {
        let n = 0; G.set(cvs, { opacity: 1 });
        const flick = () => { noise(); if (++n < 8) requestAnimationFrame(flick); }; flick();
        G.to(cvs, { opacity: 0, duration: 0.32, delay: 0.1, ease: "steps(4)" });
        const s = slides[i]; s.classList.remove("glitch"); void s.offsetWidth; s.classList.add("glitch");
      }
    };
    btns.forEach((b, i) => b.addEventListener("click", () => { show(i); restart(); }));
    const restart = () => { clearInterval(timer); if (MOTION && visible) timer = setInterval(() => { if (!hover && !document.hidden) show((cur + 1) % slides.length); }, 3600); };
    const grid = $(".tv-grid", sec);
    grid.addEventListener("pointerenter", () => { hover = true; }); grid.addEventListener("pointerleave", () => { hover = false; });
    grid.addEventListener("focusin", () => { hover = true; }); grid.addEventListener("focusout", () => { hover = false; });
    new IntersectionObserver(([en]) => { visible = en.isIntersecting; restart(); }, { threshold: 0.25 }).observe(grid);
  })();

  /* ── stage spotlight ── */
  (() => {
    const sec = $(".stage"); if (!sec || !MOTION) return;
    const spot = $(".spot", sec);
    let tx = 50, ty = 40, x = 50, y = 40, auto = !FINE, t = 0, raf = 0, vis = false;
    sec.addEventListener("pointermove", (e) => { const r = sec.getBoundingClientRect(); tx = ((e.clientX - r.left) / r.width) * 100; ty = ((e.clientY - r.top) / r.height) * 100; auto = false; });
    sec.addEventListener("pointerleave", () => { auto = true; });
    const loop = () => {
      if (!vis) { raf = 0; return; }
      t += 0.006;
      if (auto) { tx = 50 + Math.sin(t * 1.3) * 34; ty = 40 + Math.cos(t * 0.9) * 24; }
      x = lerp(x, tx, 0.08); y = lerp(y, ty, 0.08);
      spot.style.setProperty("--sx", x.toFixed(2) + "%"); spot.style.setProperty("--sy", y.toFixed(2) + "%");
      raf = requestAnimationFrame(loop);
    };
    new IntersectionObserver(([en]) => { vis = en.isIntersecting; if (vis && !raf) loop(); }).observe(sec);
  })();

  /* ── multiview: category filter (Flip) + tally director + hearts ── */
  (() => {
    const sec = $(".mv"); if (!sec) return;
    const wall = $(".mv-wall", sec), mons = $$(".mon", wall), chips = $$(".chip", sec);
    chips.forEach((c) => c.addEventListener("click", () => {
      const f = c.dataset.f;
      chips.forEach((x) => x.setAttribute("aria-pressed", x === c ? "true" : "false"));
      const state = FLIP && MOTION ? window.Flip.getState(mons) : null;
      mons.forEach((m) => m.classList.toggle("is-out", !(f === "all" || m.dataset.cat === f)));
      if (state) {
        window.Flip.from(state, {
          duration: 0.75, ease: "power3.inOut", scale: true, absolute: true, stagger: 0.015,
          onEnter: (els) => G.fromTo(els, { autoAlpha: 0, scale: 0.6 }, { autoAlpha: 1, scale: 1, duration: 0.6, ease: "back.out(1.6)" }),
          onLeave: (els) => G.to(els, { autoAlpha: 0, scale: 0.6, duration: 0.4 }),
          onComplete: () => ST.refresh(),
        });
      } else ST.refresh();
      step(true);
    }));
    const vis = () => mons.filter((m) => !m.classList.contains("is-out"));
    function step(reset) {
      const v = vis(); if (!v.length) return;
      const cur = reset ? -1 : v.findIndex((m) => m.classList.contains("pgm"));
      mons.forEach((m) => m.classList.remove("pgm", "pvw"));
      const ni = (cur + 1 + (reset ? 0 : Math.floor(Math.random() * 3))) % v.length;
      v[ni].classList.add("pgm"); if (v.length > 1) v[(ni + 1) % v.length].classList.add("pvw");
    }
    step(true);
    if (!MOTION) return;
    let timer = null;
    new IntersectionObserver(([en]) => { clearInterval(timer); if (en.isIntersecting) timer = setInterval(() => !document.hidden && step(false), 1700); }, { threshold: 0.15 }).observe(wall);
    const heart = (m) => {
      const h = document.createElement("span"); h.className = "heart"; h.setAttribute("aria-hidden", "true");
      h.textContent = ["♥", "♥", "♥", "✦"][(Math.random() * 4) | 0];
      $(".mon-screen", m).append(h);
      G.fromTo(h, { y: 0, x: 0, scale: 0.5, autoAlpha: 1 }, { y: -G.utils.random(110, 230), x: G.utils.random(-40, 16), scale: G.utils.random(0.9, 1.5), rotation: G.utils.random(-30, 30), autoAlpha: 0, duration: G.utils.random(1.2, 2), ease: "power1.out", onComplete: () => h.remove() });
    };
    mons.forEach((m) => {
      const scr = $(".mon-screen", m); let iv = null;
      m.addEventListener("pointerenter", () => { heart(m); iv = setInterval(() => heart(m), 240); });
      m.addEventListener("pointerleave", () => { clearInterval(iv); G.to(scr, { rotationX: 0, rotationY: 0, duration: 0.9, ease: "elastic.out(1,.5)" }); });
      if (FINE) m.addEventListener("pointermove", (e) => {
        const r = m.getBoundingClientRect(); const nx = (e.clientX - r.left) / r.width - 0.5, ny = (e.clientY - r.top) / r.height - 0.5;
        G.to(scr, { rotationY: nx * 16, rotationX: -ny * 12, transformPerspective: 700, duration: 0.45, ease: "power2.out" });
      });
    });
  })();

  /* ── VOD hover preview that trails the cursor ── */
  (() => {
    if (!MOTION || !FINE) return;
    const prev = $(".vod-preview"), img = prev && $("img", prev); if (!prev) return;
    G.set(prev, { xPercent: 0, yPercent: -50, autoAlpha: 0, scale: 0.85 });
    const qx = G.quickTo(prev, "x", { duration: 0.55, ease: "power3" }), qy = G.quickTo(prev, "y", { duration: 0.55, ease: "power3" }), qr = G.quickTo(prev, "rotation", { duration: 0.7, ease: "power3" });
    let lastX = 0, on = false;
    $$(".vod-row[data-thumb]").forEach((row) => {
      row.addEventListener("pointerenter", () => { on = true; img.src = row.dataset.thumb; prev.classList.toggle("land", !!row.dataset.land); G.to(prev, { autoAlpha: 1, scale: 1, duration: 0.35, ease: "power3.out" }); });
      row.addEventListener("pointerleave", () => { on = false; G.to(prev, { autoAlpha: 0, scale: 0.85, duration: 0.3 }); });
    });
    addEventListener("pointermove", (e) => { qx(e.clientX + 28); qy(e.clientY); if (on) qr(clamp((e.clientX - lastX) * 0.5, -14, 14)); lastX = e.clientX; }, { passive: true });
  })();

  /* ── tally lamp ON AIR / OFF AIR ── */
  const setTally = (onAir) => {
    $$(".js-tally, .js-offsign").forEach((t) => { t.classList.toggle("off", !onAir); const s = $("span", t); if (s) s.textContent = onAir ? "ON AIR" : "OFF AIR"; });
  };

  /* ── custom cursor ── */
  (() => {
    if (!FINE || !MOTION) return;
    const c = $(".cursor"); if (!c) return;
    root.classList.add("has-cursor");
    const ring = $(".cursor-ring", c), dot = $(".cursor-dot", c), label = $(".cursor-label", c);
    G.set([ring, dot], { xPercent: -50, yPercent: -50 });
    G.set(c, { autoAlpha: 0 });
    addEventListener("pointermove", () => G.to(c, { autoAlpha: 1, duration: 0.3 }), { once: true });
    const rx = G.quickTo(ring, "x", { duration: 0.42, ease: "power3" }), ry = G.quickTo(ring, "y", { duration: 0.42, ease: "power3" });
    const dx = G.quickTo(dot, "x", { duration: 0.08, ease: "power3" }), dy = G.quickTo(dot, "y", { duration: 0.08, ease: "power3" });
    addEventListener("pointermove", (e) => { rx(e.clientX); ry(e.clientY); dx(e.clientX); dy(e.clientY); }, { passive: true });
    const sel = "[data-cursor], a, button";
    document.addEventListener("pointerover", (e) => {
      const t = e.target.closest(sel); if (!t) return;
      if (t.dataset.cursor) { label.textContent = t.dataset.cursor; c.classList.add("is-label"); } else c.classList.add("is-hover");
    });
    document.addEventListener("pointerout", (e) => {
      const t = e.target.closest(sel); if (!t || t.contains(e.relatedTarget)) return;
      c.classList.remove("is-label", "is-hover");
    });
    addEventListener("pointerdown", () => G.to(ring, { scale: 0.75, duration: 0.15 }));
    addEventListener("pointerup", () => G.to(ring, { scale: 1, duration: 0.35, ease: "back.out(3)" }));
    document.documentElement.addEventListener("pointerleave", () => G.to(c, { autoAlpha: 0, duration: 0.2 }));
    document.documentElement.addEventListener("pointerenter", () => G.to(c, { autoAlpha: 1, duration: 0.2 }));
  })();

  /* ── scrubber + nav state ── */
  const chapters = $$("[data-chapter]");
  const scrub = $(".scrub");
  const navIds = $$(".bar-nav a").map((a) => a.dataset.nav);
  function chapterMarks() {
    const track = $(".scrub-track", scrub); if (!track) return;
    $$(".scrub-mark", track).forEach((m) => m.remove());
    const max = ST.maxScroll(window) || 1;
    chapters.forEach((s) => {
      const top = s.getBoundingClientRect().top + window.scrollY;
      const b = document.createElement("button"); b.type = "button"; b.className = "scrub-mark"; b.tabIndex = -1;
      b.style.left = (clamp(top / max, 0, 1) * 100).toFixed(2) + "%"; b.dataset.cursor = s.dataset.chapter;
      b.addEventListener("click", (ev) => { ev.stopPropagation(); scrollToEl(s); });
      track.append(b);
    });
  }
  function onScroll() {
    if (!scrub) return;
    const max = ST.maxScroll(window) || 1, p = clamp(window.scrollY / max, 0, 1);
    scrub.classList.toggle("is-away", window.scrollY < window.innerHeight * 0.55);
    $(".scrub-track", scrub).style.setProperty("--p", (p * 100).toFixed(2) + "%");
    let idx = 0; const line = window.innerHeight * 0.45;
    chapters.forEach((s, i) => { if (s.getBoundingClientRect().top <= line) idx = i; });
    $(".js-segno").textContent = pad(idx + 1); $(".js-segname").textContent = chapters[idx].dataset.chapter; $(".js-segcount").textContent = `${pad(idx + 1)} / ${pad(chapters.length)}`;
    let navOn = null;
    navIds.forEach((id) => { const el = document.getElementById(id); if (el && el.getBoundingClientRect().top <= line) navOn = id; });
    $$("[data-nav]").forEach((a) => a.classList.toggle("is-on", a.dataset.nav === navOn));
  }
  if (scrub) {
    $(".scrub-track", scrub).addEventListener("click", (e) => {
      const r = e.currentTarget.getBoundingClientRect(); const y = clamp((e.clientX - r.left) / r.width, 0, 1) * ST.maxScroll(window);
      if (lenis) lenis.scrollTo(y, { duration: 1.4 }); else window.scrollTo({ top: y, behavior: RM ? "auto" : "smooth" });
    });
    ST.addEventListener("refresh", () => { chapterMarks(); onScroll(); });
    if (lenis) lenis.on("scroll", onScroll); else addEventListener("scroll", onScroll, { passive: true });
  }

  if (!MOTION) {
    // static but correct: final states only
    ST.addEventListener("refresh", onScroll); onScroll();
    $$(".prompter .pd-line").forEach((l) => l.classList.add("on"));
    return;
  }

  /* ── scroll choreography, built in page order per breakpoint ── */
  const mm = G.matchMedia();
  mm.add({ desktop: "(min-width: 901px)", mobile: "(max-width: 900px)" }, (ctx) => {
    const { desktop } = ctx.conditions;
    const cleanups = [];

    // HERO — scroll-out parallax
    if (heroSec) {
      G.timeline({ scrollTrigger: { trigger: heroSec, start: "top top", end: "bottom top", scrub: true } })
        .to(".hero-back", { yPercent: -30, scale: 1.14, ease: "none" }, 0)
        .to(".hero-fig", { yPercent: -9, ease: "none" }, 0)
        .to(".hero-front", { yPercent: -36, autoAlpha: 0, ease: "none" }, 0)
        .to(".vf", { autoAlpha: 0, ease: "none" }, 0);
    }

    // PROMPTER
    (() => {
      const sec = $(".prompter"); if (!sec) return;
      segHead(sec);
      const pd = $(".pd", sec), box = $(".pd-lines", sec), win = $(".pd-win", sec), lines = $$(".pd-line", sec);
      const count = $(".js-pd-count", sec), bar = $(".pd-bar i", sec), n = lines.length;
      let cur = -1;
      const setActive = (i) => { if (i === cur) return; cur = i; lines.forEach((l, k) => l.classList.toggle("on", k === i)); count.textContent = `${pad(i + 1)} / ${pad(n)}`; };
      if (desktop) {
        sec.classList.add("live");
        let offs = [];
        const measure = () => { offs = lines.map((l) => l.offsetTop + l.offsetHeight / 2); };
        const render = (p) => {
          if (!offs.length) measure();
          const f = p * (n - 1), i = Math.floor(f), t = f - i;
          const c = lerp(offs[i], offs[Math.min(i + 1, n - 1)], t);
          G.set(box, { y: win.clientHeight / 2 - c });
          setActive(Math.round(f)); bar.style.width = (p * 100).toFixed(1) + "%";
        };
        const proxy = { p: 0 };
        G.to(proxy, { p: 1, ease: "none", onUpdate: () => render(proxy.p),
          scrollTrigger: { trigger: pd, start: "center center", end: () => "+=" + Math.round(n * window.innerHeight * 0.42), pin: true, scrub: 0.6, invalidateOnRefresh: true, onRefresh: () => { measure(); render(proxy.p); } } });
        measure(); render(0);
        cleanups.push(() => { sec.classList.remove("live"); G.set(box, { clearProps: "transform" }); lines.forEach((l) => l.classList.remove("on")); });
      } else {
        sec.classList.add("stack");
        lines.forEach((l, i) => ST.create({ trigger: l, start: "top 62%", end: "bottom 38%", onToggle: (s) => s.isActive && setActive(i) }));
        cleanups.push(() => { sec.classList.remove("stack"); lines.forEach((l) => l.classList.remove("on")); });
      }
    })();

    // PROFILE
    (() => {
      const sec = $(".profile"); if (!sec) return;
      segHead(sec);
      G.fromTo($(".frame-img", sec), { clipPath: "inset(14% 14% 14% 14%)" }, { clipPath: "inset(0% 0% 0% 0%)", ease: "power2.out", scrollTrigger: { trigger: $(".frame", sec), start: "top 88%", end: "top 35%", scrub: 0.8 } });
      G.fromTo($(".frame-img img", sec), { yPercent: -14 }, { yPercent: 0, ease: "none", scrollTrigger: { trigger: $(".frame", sec), start: "top bottom", end: "bottom top", scrub: true } });
      G.from($$(".crop", sec), { scale: 1.8, autoAlpha: 0, duration: 0.7, stagger: 0.07, ease: "back.out(2)", scrollTrigger: { trigger: $(".frame", sec), start: "top 70%", once: true } });
      G.from($(".pass-wrap", sec), { y: -280, duration: 1.6, ease: "elastic.out(1,.42)", scrollTrigger: { trigger: $(".pass-wrap", sec), start: "top 85%", once: true } });
      G.from($$(".spec dt, .spec dd", sec), { autoAlpha: 0, x: 14, duration: 0.5, stagger: 0.04, scrollTrigger: { trigger: $(".spec", sec), start: "top 88%", once: true } });
      cleanups.push(passSwing(sec));
    })();

    // RECORD — odometers roll
    odos.forEach(({ o, cols }, k) => {
      cols.forEach(({ s, d }, i) => G.fromTo(s, { yPercent: 0 }, { yPercent: -(10 + d) * 5, duration: 1.8 + i * 0.18, ease: "power4.out", delay: k * 0.08, scrollTrigger: { trigger: o, start: "top 88%", once: true } }));
    });
    G.from(".board", { y: 60, autoAlpha: 0, rotationX: 12, transformPerspective: 900, duration: 1.1, ease: "expo.out", scrollTrigger: { trigger: ".board", start: "top 85%", once: true } });

    // IDENTS (static → channel card)
    const ident = (sec) => {
      const cvs = $(".ident-static", sec), noise = staticNoise(cvs, 160, 90);
      const chars = $$(".ident-title [data-split]", sec).flatMap(split);
      G.set(chars, { "--w": 900 });
      let run = false, raf = 0;
      const loop = () => { if (!run) { raf = 0; return; } noise(); raf = requestAnimationFrame(loop); };
      const setRun = (v) => { run = v; if (v && !raf) loop(); };
      const tl = G.timeline({ defaults: { ease: "expo.out" } });
      tl.set(cvs, { opacity: 1 }, 0)
        .to(cvs, { opacity: 0, duration: 0.5, ease: "steps(5)" }, 0.35)
        .from($(".ident-osd", sec), { autoAlpha: 0, duration: 0.01 }, 0.3)
        .from($(".ident-ch", sec), { autoAlpha: 0, y: 14, duration: 0.6 }, 0.55)
        .from(chars, { yPercent: 115, "--w": 100, duration: 1.1, stagger: 0.04 }, 0.6)
        .from($(".ident-sub", sec), { autoAlpha: 0, y: 24, duration: 0.9 }, 1.0);
      if (desktop) {
        ST.create({ animation: tl, trigger: sec, start: "top top", end: "+=110%", pin: true, scrub: 0.6,
          onUpdate: () => setRun(G.getProperty(cvs, "opacity") > 0.02), onToggle: (s) => setRun(s.isActive && G.getProperty(cvs, "opacity") > 0.02) });
      } else {
        tl.pause(0);
        ST.create({ trigger: sec, start: "top 70%", once: true, onEnter: () => { setRun(true); tl.play(0).then(() => setRun(false)); } });
      }
      cleanups.push(() => setRun(false));
    };
    $$(".ident--sports").forEach(ident);

    // RACE DAY — course
    (() => {
      const sec = $(".course"); if (!sec) return;
      segHead(sec);
      G.from($(".press-q", sec), { autoAlpha: 0, y: 30, duration: 1, ease: "power3.out", scrollTrigger: { trigger: $(".press-q", sec), start: "top 88%", once: true } });
      G.from($$(".upnext li", sec), { autoAlpha: 0, x: 24, duration: 0.6, stagger: 0.07, ease: "power3.out", scrollTrigger: { trigger: $(".upnext", sec), start: "top 88%", once: true } });
      G.from($$(".press-list li", sec), { autoAlpha: 0, y: 20, duration: 0.6, stagger: 0.07, scrollTrigger: { trigger: $(".press-list", sec), start: "top 92%", once: true } });
      const pin = $(".course-pin", sec), track = $(".course-track", sec), svg = $(".course-svg", sec);
      const path = $(".route", sec), pathBg = $(".route-bg", sec), runner = $(".runner", sec);
      const kmEl = $(".js-km", sec), nowEl = $(".js-cpnow", sec), cps = $$(".cp", sec);
      if (desktop) {
        sec.classList.add("h");
        let len = 1, lut = [], centers = [];
        const build = () => {
          G.set(track, { x: 0 });
          const H = track.clientHeight, W = track.scrollWidth, mid = H * 0.5;
          svg.setAttribute("width", W); svg.setAttribute("height", H); svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
          const pts = [{ x: 0, y: mid }]; centers = [];
          cps.forEach((cp, i) => {
            const x = cp.offsetParent === track ? cp.offsetLeft + cp.offsetWidth / 2 : cp.offsetParent.offsetLeft + cp.offsetLeft + cp.offsetWidth / 2, y = mid + Math.sin(i * 1.2) * H * 0.075;
            cp.style.setProperty("--y", y.toFixed(1) + "px"); pts.push({ x, y }); centers.push({ x, cp });
          });
          // the route ends on the FINISH checkpoint (no tail past it)
          let d = `M${pts[0].x},${pts[0].y}`;
          for (let i = 0; i < pts.length - 1; i++) {
            const p0 = pts[i - 1] || pts[i], p1 = pts[i], p2 = pts[i + 1], p3 = pts[i + 2] || p2;
            d += ` C${(p1.x + (p2.x - p0.x) / 6).toFixed(1)},${(p1.y + (p2.y - p0.y) / 6).toFixed(1)} ${(p2.x - (p3.x - p1.x) / 6).toFixed(1)},${(p2.y - (p3.y - p1.y) / 6).toFixed(1)} ${p2.x.toFixed(1)},${p2.y.toFixed(1)}`;
          }
          path.setAttribute("d", d); pathBg.setAttribute("d", d);
          len = path.getTotalLength(); path.style.strokeDasharray = len; path.style.strokeDashoffset = len;
          lut = []; const N = 700; for (let k = 0; k <= N; k++) lut.push(path.getPointAtLength((len * k) / N).x);
        };
        const lenAtX = (x) => { let lo = 0, hi = lut.length - 1; while (lo < hi) { const m = (lo + hi) >> 1; if (lut[m] < x) lo = m + 1; else hi = m; } return (len * lo) / (lut.length - 1); };
        const dist = () => Math.max(0, track.scrollWidth - window.innerWidth);
        const render = () => {
          // the "you are here" point travels from screen-centre at the start to the FINISH dot at the end of the pin,
          // so the last checkpoint is always reached and the counter lands on exactly 42.195
          const d = dist(), tr = d ? Math.min(1, Math.max(0, -G.getProperty(track, "x") / d)) : 1, t = tr > 0.995 ? 1 : tr;
          const c0 = window.innerWidth * 0.5, c1 = centers.length ? centers[centers.length - 1].x : c0;
          const cx = c0 + (c1 - c0) * t;
          const l = t >= 1 ? len : lenAtX(cx); path.style.strokeDashoffset = len - l;
          const p = path.getPointAtLength(l); G.set(runner, { x: p.x, y: p.y });
          const km = (l / len) * 42.195; kmEl.textContent = km.toFixed(3); runner.dataset.km = km.toFixed(1) + " KM";
          let name = "START LINE";
          for (const c of centers) { const hit = c.x <= cx + 2 || t >= 1; c.cp.classList.toggle("hit", hit); if (hit && c.cp.dataset.name) name = c.cp.dataset.name; }
          nowEl.textContent = name;
        };
        build();
        G.to(track, { x: () => -dist(), ease: "none", onUpdate: render,
          scrollTrigger: { trigger: pin, start: "top top", end: () => "+=" + dist(), pin: true, scrub: 0.8, invalidateOnRefresh: true, onRefreshInit: build, onRefresh: render } });
        G.from($$(".cp-card", sec), { autoAlpha: 0, y: (i) => (i % 2 ? 40 : -40), duration: 0.8, stagger: 0.03, ease: "power3.out", scrollTrigger: { trigger: pin, start: "top 70%", once: true } });
        render();
        cleanups.push(() => { sec.classList.remove("h"); cps.forEach((c) => c.classList.remove("hit")); G.set(track, { clearProps: "transform" }); });
      } else {
        const list = $(".cps", sec);
        ST.create({ trigger: list, start: "top 65%", end: "bottom 65%", scrub: true, onUpdate: (s) => {
          list.style.setProperty("--vp", s.progress.toFixed(4)); kmEl.textContent = (s.progress * 42.195).toFixed(3);
          let name = "START LINE"; const line = window.innerHeight * 0.65;
          for (const cp of cps) { if (cp.getBoundingClientRect().top < line && cp.dataset.name) name = cp.dataset.name; }
          nowEl.textContent = name;
        } });
        cps.forEach((cp) => G.from($(".cp-card", cp), { x: 28, autoAlpha: 0, duration: 0.7, ease: "power3.out", scrollTrigger: { trigger: cp, start: "top 90%", once: true } }));
        cleanups.push(() => list.style.removeProperty("--vp"));
      }
    })();

    // PIT LANE — tachometer
    (() => {
      const sec = $(".pit"); if (!sec) return;
      segHead(sec);
      if (gauge) {
        const st = { v: 0.8, kmh: 0 }; const speed = $(".js-speed"), gear = $(".js-gear");
        G.fromTo(st, { v: 0.8, kmh: 0 }, { v: 7.15, kmh: 120, ease: "power2.in",
          onUpdate: () => {
            const shake = st.v > 6.7 ? Math.sin(performance.now() / 38) * 1.4 : 0;
            G.set(gauge.needle, { rotation: gauge.ang(st.v) + shake, svgOrigin: "200 200" });
            speed.textContent = Math.round(st.kmh); gear.textContent = st.kmh < 4 ? "N" : String(Math.min(6, 1 + Math.floor(st.kmh / 21)));
          },
          scrollTrigger: { trigger: $(".gauge", sec), start: "top 80%", end: "bottom 35%", scrub: 0.6 } });
      }
      G.from($(".quote-cap", sec), { autoAlpha: 0, y: 30, duration: 0.9, ease: "power3.out", scrollTrigger: { trigger: $(".quote-cap", sec), start: "top 90%", once: true } });
      G.from($$(".pit-list li", sec), { autoAlpha: 0, x: 30, duration: 0.6, stagger: 0.08, ease: "power3.out", scrollTrigger: { trigger: $(".pit-list", sec), start: "top 88%", once: true } });
      G.fromTo($(".pit-photo img", sec), { scale: 1.16 }, { scale: 1.02, ease: "none", scrollTrigger: { trigger: $(".pit-photo", sec), start: "top bottom", end: "bottom top", scrub: true } });
      G.from($(".pit-photo", sec), { clipPath: "inset(0% 0% 100% 0%)", duration: 1.3, ease: "expo.inOut", scrollTrigger: { trigger: $(".pit-photo", sec), start: "top 85%", once: true } });
    })();

    // ON TV
    (() => {
      const sec = $(".tv"); if (!sec) return;
      segHead(sec);
      G.from($(".tvset", sec), { autoAlpha: 0, y: 50, rotationX: 10, transformPerspective: 900, duration: 1.1, ease: "expo.out", scrollTrigger: { trigger: $(".tvset", sec), start: "top 85%", once: true } });
      G.from($$(".epg li", sec), { autoAlpha: 0, x: 26, duration: 0.6, stagger: 0.07, ease: "power3.out", scrollTrigger: { trigger: $(".epg", sec), start: "top 88%", once: true } });
    })();

    // ON STAGE
    (() => {
      const sec = $(".stage"); if (!sec) return;
      segHead(sec);
      G.from($$(".shot", sec), { clipPath: "inset(0% 0% 100% 0%)", duration: 1.25, ease: "expo.inOut", stagger: 0.18, scrollTrigger: { trigger: $(".stage-photos", sec), start: "top 82%", once: true } });
      $$(".deck", sec).forEach((d) => G.from($$(".cue-card", d), {
        y: 90, rotation: () => G.utils.random(-16, 16), autoAlpha: 0, duration: 0.95, ease: "back.out(1.5)", stagger: 0.06, clearProps: "transform,opacity,visibility",
        scrollTrigger: { trigger: d, start: "top 86%", once: true } }));
    })();

    $$(".ident--live").forEach(ident);

    // MULTIVIEW
    (() => {
      const sec = $(".mv"); if (!sec) return;
      segHead(sec);
      G.from($$(".chip", sec), { autoAlpha: 0, y: 12, duration: 0.5, stagger: 0.05, scrollTrigger: { trigger: $(".chips", sec), start: "top 90%", once: true } });
      G.from($$(".mon-screen", sec), { scaleY: 0.015, filter: "brightness(4)", duration: 0.55, ease: "power3.out", stagger: { each: 0.04, from: "random" }, clearProps: "filter",
        scrollTrigger: { trigger: $(".mv-wall", sec), start: "top 80%", once: true } });
      G.from($$(".more-air li", sec), { autoAlpha: 0, y: 12, duration: 0.45, stagger: 0.03, scrollTrigger: { trigger: $(".more-air", sec), start: "top 92%", once: true } });
    })();

    // VOD
    (() => {
      const sec = $(".vod"); if (!sec) return;
      segHead(sec);
      $$(".vod-list", sec).forEach((l) => G.from($$(".vod-row", l), { autoAlpha: 0, y: 26, duration: 0.6, stagger: 0.04, ease: "power3.out", scrollTrigger: { trigger: l, start: "top 90%", once: true } }));
    })();

    // CUE SHEET — director's NOW bar
    (() => {
      const sec = $(".cue"); if (!sec) return;
      segHead(sec);
      const list = $(".sheet-list", sec), rows = $$(".sheet-row", sec), now = $(".sheet-now", sec);
      G.from(rows, { autoAlpha: 0, x: -24, duration: 0.6, stagger: 0.06, ease: "power3.out", scrollTrigger: { trigger: list, start: "top 85%", once: true } });
      let idx = -1;
      ST.create({ trigger: list, start: "top 62%", end: "bottom 62%", onUpdate: (s) => {
        G.set(now, { y: list.offsetTop + s.progress * list.offsetHeight });
        const i = Math.min(rows.length - 1, Math.floor(s.progress * rows.length));
        if (i === idx) return; idx = i;
        rows.forEach((r, k) => r.classList.toggle("on", k === i));
        const it = $(".r-item", rows[i]);
        if (SCRAMBLE && it) G.to(it, { duration: 0.8, scrambleText: { text: it.dataset.text, chars: KO, speed: 0.9 } });
      } });
    })();

    // OFF AIR
    (() => {
      const sec = $(".offair"); if (!sec) return;
      const grid = $(".off-grid", sec);
      G.from($(".off-visual", sec), { clipPath: "inset(100% 0% 0% 0%)", duration: 1.4, ease: "expo.inOut", scrollTrigger: { trigger: grid, start: "top 75%", once: true } });
      G.from($(".off-visual img", sec), { yPercent: 16, duration: 1.7, ease: "expo.out", scrollTrigger: { trigger: grid, start: "top 75%", once: true } });
      const marks = $$(".off-h mark", sec); G.set(marks, { "--hl": "0%" });
      G.to(marks, { "--hl": "100%", duration: 0.9, ease: "power2.inOut", stagger: 0.5, scrollTrigger: { trigger: $(".off-h", sec), start: "top 78%", once: true } });
      G.from($$(".off-copy > *:not(.off-h)", sec), { autoAlpha: 0, y: 20, duration: 0.7, stagger: 0.08, scrollTrigger: { trigger: $(".off-copy", sec), start: "top 80%", once: true } });
      G.from($$(".c-row", sec), { autoAlpha: 0, y: 16, duration: 0.6, stagger: 0.1, scrollTrigger: { trigger: $(".contact", sec), start: "top 90%", once: true } });
      ST.create({ trigger: $(".signoff", sec), start: "top 75%", onEnter: () => setTally(false), onLeaveBack: () => setTally(true) });
      G.timeline({ scrollTrigger: { trigger: $(".signoff", sec), start: "top 70%", once: true } })
        .set(".signoff-tv i", { opacity: 1, scaleX: 1, scaleY: 1 })
        .to(".signoff-tv i", { scaleY: 0.012, duration: 0.28, ease: "power4.in" })
        .to(".signoff-tv i", { scaleX: 0.004, duration: 0.22, ease: "power4.in" })
        .to(".signoff-tv i", { opacity: 0, duration: 0.25 })
        .fromTo(".signoff-tv b", { autoAlpha: 0, scale: 0.9 }, { autoAlpha: 1, scale: 1, duration: 0.6, ease: "expo.out" }, "-=.1");
    })();

    ST.sort();
    return () => cleanups.forEach((f) => f && f());
  });

  /* ── start: cold open → hero intro ── */
  function coldOpen(done) {
    const top = ["#C0C0C0", "#C0C000", "#00C0C0", "#00C000", "#C000C0", "#C00000", "#0000C0"];
    const mid = ["#0000C0", "#131313", "#C000C0", "#131313", "#00C0C0", "#131313", "#C0C0C0"];
    const bot = ["#00214C", "#FFFFFF", "#32006A", "#131313", "#090909", "#131313", "#1D1D1D", "#131313"];
    const row = (cls, arr) => `<div class="co-row ${cls}">${arr.map((c) => `<i style="background:${c}"></i>`).join("")}</div>`;
    const el = document.createElement("div"); el.className = "coldopen"; el.setAttribute("aria-hidden", "true");
    el.innerHTML = `<div class="co-bars">${row("", top)}${row("", mid)}${row("b", bot)}</div>
      <div class="co-slate"><div><span>PROGRAM</span><b>이채원 ON AIR</b></div><div><span>HOST</span><b>LEE CHAEWON</b></div><div><span>TC</span><b class="co-tc">00:59:57:00</b></div></div>
      <div class="co-leader"><div class="co-ring"><i></i><span class="co-num">3</span></div></div>
      <div class="co-onair"><b>ON AIR</b></div><button class="co-skip" type="button">SKIP ▶▶</button>`;
    document.body.append(el);
    root.style.overflow = "hidden"; lenis && lenis.stop();
    const num = $(".co-num", el), ring = $(".co-ring", el), tc = $(".co-tc", el);
    const finish = () => { el.remove(); root.style.overflow = ""; lenis && lenis.start(); removeEventListener("keydown", skip); done(); };
    const tl = G.timeline({ onComplete: finish });
    tl.from($(".co-slate", el), { autoAlpha: 0, y: 14, duration: 0.3 }, 0.05)
      .to($(".co-bars", el), { x: 7, duration: 0.05, repeat: 5, yoyo: true, ease: "none" }, 0.5)
      .to($(".co-leader", el), { autoAlpha: 1, duration: 0.1 }, 0.72)
      .to($(".co-slate", el), { autoAlpha: 0, duration: 0.1 }, 0.72);
    [3, 2, 1].forEach((n, i) => {
      const t = 0.74 + i * 0.42;
      tl.call(() => { num.textContent = n; tc.textContent = `00:59:5${7 + i}:00`; }, null, t)
        .fromTo(ring, { "--a": "0deg" }, { "--a": "360deg", duration: 0.42, ease: "none" }, t)
        .fromTo(num, { scale: 1.3, autoAlpha: 0 }, { scale: 1, autoAlpha: 1, duration: 0.16, ease: "power2.out" }, t);
    });
    tl.call(() => { tc.textContent = "01:00:00:00"; }, null, 2.0)
      .to($(".co-onair", el), { autoAlpha: 1, duration: 0.06 }, 2.0)
      .fromTo($(".co-onair b", el), { scale: 1.5, letterSpacing: "0.25em" }, { scale: 1, letterSpacing: "-0.02em", duration: 0.4, ease: "expo.out" }, 2.0)
      .to(el, { clipPath: "inset(50% 0% 50% 0%)", duration: 0.5, ease: "expo.inOut" }, 2.5);
    function skip() { tl.progress(1); }
    el.addEventListener("click", skip); addEventListener("keydown", skip);
  }

  const start = () => { heroIntro && heroIntro.play(0); };
  if (MOTION) coldOpen(start); else start();
  document.fonts?.ready?.then(() => ST.refresh());
  addEventListener("load", () => ST.refresh());
})();

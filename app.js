(function () {
  const data = window.siteContent;
  const root = document.documentElement;
  const shell = document.querySelector("[data-scroll-shell]");
  const loader = document.querySelector("[data-loader]");
  const loaderBar = document.querySelector("[data-loader-bar]");
  const helloStage = document.querySelector("[data-hello-stage]");
  const helloWord = document.querySelector("[data-hello-word]");
  const helloSub = document.querySelector("[data-hello-sub]");
  const impactOverlay = document.querySelector("[data-impact-overlay]");
  const impactWord = document.querySelector("[data-impact-word]");
  const ambientCanvas = document.querySelector("#ambient-canvas");
  const signalCanvas = document.querySelector("#signal-canvas");
  const ambient = ambientCanvas.getContext("2d");
  const signal = signalCanvas.getContext("2d");

  const state = {
    pointer: { x: window.innerWidth / 2, y: window.innerHeight / 2 },
    target: { x: window.innerWidth / 2, y: window.innerHeight / 2 },
    sound: false,
    audio: null,
    tick: 0,
    impactLocked: false,
  };

  document.title = data.meta.title;
  document.querySelector('meta[name="description"]').setAttribute("content", data.meta.description);

  const el = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  };

  const setText = (selector, text) => {
    const node = document.querySelector(selector);
    if (node) node.textContent = text;
  };

  function lineSpans(lines) {
    return lines.map((line, index) => {
      const span = el("span", "line-reveal", line);
      span.style.transitionDelay = `${index * 110 + 220}ms`;
      return span;
    });
  }

  function randomBetween(min, max) {
    return min + Math.random() * (max - min);
  }

  function renderHello() {
    const text = data.intro.hello || "HELLO";
    helloWord.innerHTML = "";
    [...text].forEach((char, index) => {
      const span = el("span", "hello-char", char);
      span.dataset.final = char;
      span.style.setProperty("--burst-x", `${randomBetween(-46, 46)}vw`);
      span.style.setProperty("--burst-y", `${randomBetween(-34, 34)}vh`);
      span.style.setProperty("--burst-r", `${randomBetween(-38, 38)}deg`);
      span.style.setProperty("--burst-s", `${randomBetween(0.32, 0.74)}`);
      span.style.transitionDelay = `${index * 34}ms`;
      helloWord.append(span);
    });
    helloSub.textContent = data.intro.helloSub || "";
  }

  function scrambleHello(duration = 1180) {
    const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*+-=?/<>[]{}";
    const chars = [...helloWord.querySelectorAll(".hello-char")];
    const started = performance.now();
    const timer = window.setInterval(() => {
      const elapsed = performance.now() - started;
      const progress = Math.min(1, elapsed / duration);
      chars.forEach((span, index) => {
        const charProgress = Math.min(1, Math.max(0, progress * 1.28 - index * 0.06));
        const settled = charProgress > 0.78;
        span.textContent = settled ? span.dataset.final : alphabet[Math.floor(Math.random() * alphabet.length)];
        span.style.color = !settled && Math.random() > 0.58 ? "var(--selection)" : "var(--l1)";
        span.style.setProperty("--jitter-x", `${randomBetween(-10, 10) * (1 - charProgress)}px`);
        span.style.setProperty("--jitter-y", `${randomBetween(-8, 8) * (1 - charProgress)}px`);
        span.style.setProperty("--skew", `${randomBetween(-10, 10) * (1 - charProgress)}deg`);
      });
      root.style.setProperty("--hello-x", `${42 + Math.sin(elapsed / 160) * 14}%`);
      root.style.setProperty("--hello-y", `${50 + Math.cos(elapsed / 130) * 10}%`);
      if (progress >= 1) {
        window.clearInterval(timer);
        chars.forEach((span) => {
          span.textContent = span.dataset.final;
          span.style.color = "var(--l1)";
          span.style.setProperty("--jitter-x", "0px");
          span.style.setProperty("--jitter-y", "0px");
          span.style.setProperty("--skew", "0deg");
        });
      }
    }, 38);
  }

  function renderContent() {
    setText("[data-brand]", data.nav.brand);
    document.querySelector('[data-jump="work"]').textContent = data.nav.workLabel;
    document.querySelector('[data-jump="contact"]').textContent = data.nav.contactLabel;
    document.querySelector("[data-kicker]").innerHTML = data.intro.kicker.join("<br>");
    setText("[data-system-line]", data.intro.systemLine);

    const bio = document.querySelector("[data-bio]");
    bio.append(document.createTextNode(data.intro.bioBefore));
    const protectedText = el("span", "protected");
    protectedText.setAttribute("aria-label", "Protected text");
    [...data.intro.protectedText].forEach((char) => protectedText.append(el("span", "", char)));
    bio.append(protectedText, document.createTextNode(data.intro.bioAfter));

    const hero = document.querySelector("[data-hero-title]");
    lineSpans(data.intro.heroLines).forEach((span) => hero.append(span));

    const manifesto = document.querySelector("[data-manifesto]");
    data.manifesto.forEach((item) => {
      const p = el("p", "line-reveal");
      p.dataset.tone = item.tone;
      p.innerHTML = item.html;
      manifesto.append(p);
    });

    const work = document.querySelector("[data-work-grid]");
    data.work.forEach((project) => {
      const link = el("a", "work-card");
      link.href = project.href;
      link.dataset.size = project.size;
      link.setAttribute("aria-label", `${project.title} - ${project.years}`);
      if (project.external) {
        link.target = "_blank";
        link.rel = "noopener noreferrer";
      }

      const visual = el("div", `work-card__visual visual-${project.visual}`);
      if (project.type) visual.append(el("span", "work-card__label", project.type));

      const meta = el("div", "work-card__meta");
      meta.append(el("span", "work-card__title", project.title));
      const years = el("span", "work-card__year");
      years.append(el("span", "", project.years));
      if (project.tag) years.append(el("span", "", project.tag));
      meta.append(years);
      link.append(visual, meta);
      work.append(link);
    });

    const purpose = document.querySelector("[data-purpose]");
    lineSpans(data.purpose).forEach((span) => purpose.append(span));
    impactWord.textContent = data.purpose.join("\n");

    const headline = document.querySelector("[data-contact-headline]");
    lineSpans(data.contact.headline).forEach((span) => headline.append(span));

    const email = document.querySelector("[data-email]");
    email.href = "#contact";
    email.textContent = data.contact.email;

    const socials = document.querySelector("[data-socials]");
    data.contact.socials.forEach((social) => {
      const link = el("a", "hover-frame", social.label);
      link.href = social.href;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      socials.append(link);
    });
  }

  function pad(value) {
    return String(value).padStart(2, "0");
  }

  function updateClock() {
    const clock = document.querySelector("[data-clock]");
    const now = new Date();
    const cn = new Date(now.toLocaleString("en-US", { timeZone: "Asia/Shanghai" }));
    const text = `${pad(cn.getHours())}:${pad(cn.getMinutes())}`;
    clock.textContent = window.innerWidth < 900 ? text : `GMT+8 CN ${text}`;
  }

  function updateCoords() {
    const coords = document.querySelector("[data-coords]");
    coords.textContent = `${String(Math.round(state.pointer.x)).padStart(4, "0")} X ${String(Math.round(state.pointer.y)).padStart(4, "0")} Y`;
  }

  function resizeCanvas() {
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    for (const canvas of [ambientCanvas, signalCanvas]) {
      canvas.width = Math.floor(window.innerWidth * ratio);
      canvas.height = Math.floor(window.innerHeight * ratio);
      canvas.style.width = `${window.innerWidth}px`;
      canvas.style.height = `${window.innerHeight}px`;
      canvas.getContext("2d").setTransform(ratio, 0, 0, ratio, 0, 0);
    }
  }

  function color(name) {
    return getComputedStyle(root).getPropertyValue(name).trim();
  }

  function drawAmbient() {
    const w = window.innerWidth;
    const h = window.innerHeight;
    const bg = color("--bg");
    ambient.clearRect(0, 0, w, h);
    ambient.fillStyle = bg;
    ambient.fillRect(0, 0, w, h);

    const l = color("--l4");
    ambient.strokeStyle = l;
    ambient.lineWidth = 1;
    const grid = Math.max(42, Math.floor(w / 22));
    const drift = (state.tick * 0.18) % grid;
    for (let x = -grid + drift; x < w + grid; x += grid) {
      ambient.beginPath();
      ambient.moveTo(x, 0);
      ambient.lineTo(x + Math.sin(state.tick / 80 + x) * 10, h);
      ambient.stroke();
    }
    for (let y = -grid; y < h + grid; y += grid) {
      ambient.beginPath();
      ambient.moveTo(0, y + drift * 0.5);
      ambient.lineTo(w, y + Math.sin(state.tick / 70 + y) * 8);
      ambient.stroke();
    }

    const grad = ambient.createRadialGradient(state.pointer.x, state.pointer.y, 0, state.pointer.x, state.pointer.y, Math.max(w, h) * 0.58);
    grad.addColorStop(0, "rgba(192,254,4,0.12)");
    grad.addColorStop(0.32, "rgba(192,254,4,0.025)");
    grad.addColorStop(1, "rgba(192,254,4,0)");
    ambient.fillStyle = grad;
    ambient.fillRect(0, 0, w, h);
  }

  function drawSignal() {
    const w = window.innerWidth;
    const h = window.innerHeight;
    signal.clearRect(0, 0, w, h);
    state.pointer.x += (state.target.x - state.pointer.x) * 0.08;
    state.pointer.y += (state.target.y - state.pointer.y) * 0.08;

    signal.strokeStyle = root.classList.contains("dark") ? "rgba(255,255,255,0.18)" : "rgba(0,0,0,0.15)";
    signal.lineWidth = 1;
    signal.beginPath();
    signal.moveTo(state.pointer.x, 0);
    signal.lineTo(state.pointer.x, h);
    signal.moveTo(0, state.pointer.y);
    signal.lineTo(w, state.pointer.y);
    signal.stroke();

    signal.fillStyle = "rgba(192,254,4,0.92)";
    signal.fillRect(state.pointer.x - 3, state.pointer.y - 3, 6, 6);
    updateCoords();
  }

  function animate() {
    state.tick += 1;
    drawAmbient();
    drawSignal();
    requestAnimationFrame(animate);
  }

  function revealOnScroll() {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
          }
        });
      },
      { root: shell, threshold: 0.2 }
    );
    document.querySelectorAll(".line-reveal").forEach((node, index) => {
      node.style.transitionDelay ||= `${Math.min(index * 60, 420)}ms`;
      observer.observe(node);
    });
  }

  function setReady() {
    let progress = 0;
    const timer = window.setInterval(() => {
      progress += Math.random() * 22 + 12;
      loaderBar.style.width = `${Math.min(progress, 100)}%`;
      if (progress >= 100) {
        window.clearInterval(timer);
        loader.classList.add("is-hidden");
        startIntroSequence();
      }
    }, 120);
  }

  function startIntroSequence() {
    document.body.classList.add("is-hello-active", "is-iris-active");
    scrambleHello();
    window.setTimeout(() => {
      document.body.classList.add("is-ready");
      document.querySelectorAll(".hero-title .line-reveal").forEach((node) => node.classList.add("is-visible"));
    }, 180);
    window.setTimeout(() => {
      document.body.classList.add("is-hello-blast");
    }, 1160);
    window.setTimeout(() => {
      document.body.classList.add("is-iris-open");
    }, 1270);
    window.setTimeout(() => {
      document.body.classList.remove("is-hello-active", "is-hello-blast");
      helloStage.setAttribute("hidden", "");
    }, 2050);
    window.setTimeout(() => {
      document.body.classList.remove("is-iris-active", "is-iris-open");
      document.body.classList.add("is-settled");
    }, 2450);
  }

  function triggerImpact() {
    if (state.impactLocked) return;
    state.impactLocked = true;
    document.body.classList.remove("is-impacting");
    void impactOverlay.offsetWidth;
    document.body.classList.add("is-impacting");
    window.setTimeout(() => {
      document.body.classList.remove("is-impacting");
      window.setTimeout(() => {
        state.impactLocked = false;
      }, 900);
    }, 980);
  }

  function bindImpactTrigger() {
    const purpose = document.querySelector(".purpose");
    if (!purpose) return;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && entry.intersectionRatio > 0.34) {
            triggerImpact();
          }
        });
      },
      { root: shell, threshold: [0.34, 0.62] }
    );
    observer.observe(purpose);
  }

  function initSound() {
    if (!state.audio) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (!AudioContext) return;
      const context = new AudioContext();
      const osc = context.createOscillator();
      const gain = context.createGain();
      osc.type = "sine";
      osc.frequency.value = 96;
      gain.gain.value = 0.00001;
      osc.connect(gain).connect(context.destination);
      osc.start();
      state.audio = { context, gain };
    }
  }

  function bindEvents() {
    window.addEventListener("resize", () => {
      resizeCanvas();
      updateClock();
    });
    window.addEventListener("pointermove", (event) => {
      state.target.x = event.clientX;
      state.target.y = event.clientY;
    });

    document.querySelector('[data-jump="work"]').addEventListener("click", () => {
      document.querySelector("#selected-work").scrollIntoView({ behavior: "smooth", block: "start" });
    });
    document.querySelector('[data-jump="contact"]').addEventListener("click", () => {
      document.querySelector("#contact").scrollIntoView({ behavior: "smooth", block: "start" });
    });
    document.querySelector("[data-theme-toggle]").addEventListener("click", (event) => {
      root.classList.toggle("dark");
      event.currentTarget.textContent = root.classList.contains("dark") ? "Theme[D]" : "Theme[A]";
    });
    document.querySelector("[data-sound-toggle]").addEventListener("click", async (event) => {
      initSound();
      if (!state.audio) return;
      await state.audio.context.resume();
      state.sound = !state.sound;
      state.audio.gain.gain.setTargetAtTime(state.sound ? 0.018 : 0.00001, state.audio.context.currentTime, 0.04);
      event.currentTarget.textContent = state.sound ? "Sound[|]" : "Sound[ ]";
      event.currentTarget.setAttribute("aria-pressed", String(state.sound));
    });
  }

  function restoreHashScroll() {
    const id = window.location.hash.slice(1);
    if (!id) return;
    const target = document.getElementById(id);
    if (!target) return;
    window.setTimeout(() => {
      target.scrollIntoView({ block: "start" });
      if (id === "purpose") window.setTimeout(triggerImpact, 120);
    }, 2850);
  }

  renderContent();
  renderHello();
  resizeCanvas();
  updateClock();
  window.setInterval(updateClock, 1000);
  bindEvents();
  bindImpactTrigger();
  restoreHashScroll();
  revealOnScroll();
  animate();
  setReady();
})();

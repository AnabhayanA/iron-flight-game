
"use strict";

const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");
const W = canvas.width;
const H = canvas.height;
const keys = new Set();

const ui = {
  timer: document.getElementById("armor-value"),
  timerBar: document.getElementById("armor-fill"),
  progress: document.getElementById("kills-value"),
  boost: document.getElementById("dash-value")
};

const TOTAL = 8;
const LIMIT = 60;
const clamp = (v, min, max) => Math.max(min, Math.min(max, v));

let hero;
let checkpoints;
let completed;
let remaining;
let boostCooldown;
let boostTime;
let state;
let lastTime = null;
let particles = [];

function reset() {
  hero = {
    x: 150,
    y: 270,
    vx: 0,
    vy: 0,
    face: 1
  };

  checkpoints = [
    { x: 330, y: 210 },
    { x: 590, y: 340 },
    { x: 800, y: 175 },
    { x: 660, y: 425 },
    { x: 380, y: 380 },
    { x: 190, y: 155 },
    { x: 515, y: 130 },
    { x: 825, y: 295 }
  ];

  completed = 0;
  remaining = LIMIT;
  boostCooldown = 0;
  boostTime = 0;
  state = "playing";
  particles = [];
  keys.clear();
  updateHUD();
}

function updateHUD() {
  ui.timer.textContent = `${remaining.toFixed(1)}s`;
  ui.timerBar.style.width = `${remaining / LIMIT * 100}%`;
  ui.timerBar.style.background =
    remaining > 15 ? "#39d58a" : "#f04d4c";

  ui.progress.textContent = `${completed}/${TOTAL}`;
  ui.boost.textContent =
    boostCooldown <= 0
      ? "READY"
      : `${boostCooldown.toFixed(1)}s`;
}

function boost() {
  if (state !== "playing" || boostCooldown > 0) return;

  boostCooldown = 2.4;
  boostTime = 0.28;

  let dx = Number(keys.has("d") || keys.has("arrowright")) -
           Number(keys.has("a") || keys.has("arrowleft"));
  let dy = Number(keys.has("s") || keys.has("arrowdown")) -
           Number(keys.has("w") || keys.has("arrowup"));

  if (!dx && !dy) dx = hero.face;

  const length = Math.hypot(dx, dy) || 1;
  hero.vx = dx / length * 750;
  hero.vy = dy / length * 750;

  for (let i = 0; i < 18; i++) {
    particles.push({
      x: hero.x,
      y: hero.y,
      vx: (Math.random() - .5) * 230,
      vy: (Math.random() - .5) * 230,
      life: .5
    });
  }
}

function update(dt) {
  for (const p of particles) {
    p.x += p.vx * dt;
    p.y += p.vy * dt;
    p.life -= dt;
  }
  particles = particles.filter(p => p.life > 0);

  if (state !== "playing") return;

  remaining = Math.max(0, remaining - dt);
  boostCooldown = Math.max(0, boostCooldown - dt);
  boostTime = Math.max(0, boostTime - dt);

  if (remaining <= 0) {
    state = "lost";
    updateHUD();
    return;
  }

  let dx = Number(keys.has("d") || keys.has("arrowright")) -
           Number(keys.has("a") || keys.has("arrowleft"));
  let dy = Number(keys.has("s") || keys.has("arrowdown")) -
           Number(keys.has("w") || keys.has("arrowup"));

  const length = Math.hypot(dx, dy) || 1;
  dx /= length;
  dy /= length;

  if (dx) hero.face = Math.sign(dx);

  if (boostTime <= 0) {
    const speed = 330;
    hero.vx = dx * speed;
    hero.vy = dy * speed;
  }

  hero.x = clamp(hero.x + hero.vx * dt, 35, W - 35);
  hero.y = clamp(hero.y + hero.vy * dt, 125, H - 45);

  const checkpoint = checkpoints[completed];

  if (checkpoint) {
    const distance = Math.hypot(
      hero.x - checkpoint.x,
      hero.y - checkpoint.y
    );

    if (distance < 47) {
      completed++;

      for (let i = 0; i < 24; i++) {
        const angle = Math.random() * Math.PI * 2;
        particles.push({
          x: checkpoint.x,
          y: checkpoint.y,
          vx: Math.cos(angle) * 180,
          vy: Math.sin(angle) * 180,
          life: .6
        });
      }

      if (completed === TOTAL) {
        state = "won";
      }
    }
  }

  updateHUD();
}

function rectangle(x, y, w, h, color) {
  ctx.fillStyle = color;
  ctx.fillRect(x, y, w, h);
}

function circle(x, y, r, color) {
  ctx.beginPath();
  ctx.arc(x, y, r, 0, Math.PI * 2);
  ctx.fillStyle = color;
  ctx.fill();
}

function text(message, x, y, size, color = "#fff") {
  ctx.save();
  ctx.font = `900 ${size}px Impact, Arial Black, sans-serif`;
  ctx.textAlign = "center";
  ctx.lineWidth = 5;
  ctx.strokeStyle = "#111a32";
  ctx.strokeText(message, x, y);
  ctx.fillStyle = color;
  ctx.fillText(message, x, y);
  ctx.restore();
}

function drawBackground(time) {
  const sky = ctx.createLinearGradient(0, 0, 0, H);
  sky.addColorStop(0, "#3986c6");
  sky.addColorStop(.65, "#92d9ef");
  sky.addColorStop(1, "#ffd08a");
  rectangle(0, 0, W, H, sky);

  circle(770, 150, 60, "#ffe18b");

  for (let i = 0; i < 17; i++) {
    const x = i * 65;
    const height = 115 + Math.abs(Math.sin(i * 2.3)) * 170;
    const y = H - height;

    rectangle(
      x, y, 59, height,
      i % 2 ? "#354c73" : "#48668d"
    );

    for (let wy = y + 15; wy < H - 15; wy += 24) {
      for (let wx = x + 12; wx < x + 52; wx += 18) {
        rectangle(wx, wy, 9, 12, "#ffd994");
      }
    }
  }

  rectangle(0, H - 25, W, 25, "#152440");
}

function drawHero(time) {
  ctx.save();
  ctx.translate(hero.x, hero.y + Math.sin(time * .006) * 3);
  ctx.scale(hero.face, 1);

  const red = "#bc293e";
  const gold = "#efbc54";
  const ink = "#111a32";

  // Jet flames
  for (const x of [-13, 13]) {
    ctx.save();
    ctx.shadowColor = "#63efff";
    ctx.shadowBlur = 17;
    circle(x, 58, 11, "#60eaff");
    circle(x, 65, 6, "#fffbd6");
    ctx.restore();
  }

  // Legs
  for (const x of [-13, 13]) {
    rectangle(x - 10, 18, 20, 37, red);
    rectangle(x - 10, 42, 20, 16, gold);
  }

  // Arms
  rectangle(-36, -25, 17, 52, red);
  rectangle(19, -25, 17, 52, red);
  rectangle(-36, 6, 17, 19, gold);
  rectangle(19, 6, 17, 19, gold);

  // Torso
  rectangle(-23, -35, 46, 62, red);
  rectangle(-19, -27, 38, 17, gold);
  rectangle(-15, 10, 30, 13, "#8d263a");

  // Helmet
  circle(0, -57, 25, red);
  rectangle(-17, -65, 34, 26, gold);

  // Eyes
  ctx.save();
  ctx.shadowColor = "#7defff";
  ctx.shadowBlur = 12;
  rectangle(-13, -57, 10, 5, "#bdfaff");
  rectangle(3, -57, 10, 5, "#bdfaff");

  // Arc reactor
  circle(0, -7, 12, ink);
  circle(0, -7, 8, "#86f5ff");
  circle(0, -7, 4, "#fff");
  ctx.restore();

  ctx.restore();
}

function drawCheckpoint(checkpoint, time) {
  const pulse = Math.sin(time * .005) * 4;
  const radius = 42 + pulse;

  ctx.save();
  ctx.shadowColor = "#67f3ff";
  ctx.shadowBlur = 24;
  ctx.lineWidth = 9;
  ctx.strokeStyle = "#72f4ff";
  ctx.beginPath();
  ctx.arc(checkpoint.x, checkpoint.y, radius, 0, Math.PI * 2);
  ctx.stroke();

  ctx.lineWidth = 3;
  ctx.strokeStyle = "#ffffff";
  ctx.beginPath();
  ctx.arc(checkpoint.x, checkpoint.y, radius - 8, 0, Math.PI * 2);
  ctx.stroke();
  ctx.restore();

  text(
    `GATE ${completed + 1}`,
    checkpoint.x,
    checkpoint.y - 62,
    22,
    "#ffe05c"
  );
}

function drawParticles() {
  for (const p of particles) {
    ctx.save();
    ctx.globalAlpha = clamp(p.life / .6, 0, 1);
    circle(p.x, p.y, 4, "#8cf6ff");
    ctx.restore();
  }
}

function drawOverlay() {
  if (state === "playing") return;

  rectangle(0, 0, W, H, "rgba(11,16,37,.83)");

  if (state === "won") {
    text("FLIGHT TEST COMPLETE!", W / 2, 220, 58, "#ffe05c");
    text(
      `FINAL TIME: ${(LIMIT - remaining).toFixed(1)} SECONDS`,
      W / 2, 280, 28
    );
  } else {
    text("TIME EXPIRED!", W / 2, 220, 65, "#ff7171");
    text(
      `CHECKPOINTS: ${completed}/${TOTAL}`,
      W / 2, 280, 28
    );
  }

  rectangle(W / 2 - 180, 325, 360, 58, "#ffd44c");
  text("PRESS R TO RESTART", W / 2, 363, 29, "#111a32");
}

function render(time) {
  ctx.clearRect(0, 0, W, H);
  drawBackground(time);

  if (state === "playing") {
    const current = checkpoints[completed];
    if (current) drawCheckpoint(current, time);
  }

  drawParticles();
  drawHero(time);
  drawOverlay();
}

function frame(time) {
  const dt = lastTime === null
    ? 0
    : Math.min((time - lastTime) / 1000, .04);

  lastTime = time;
  update(dt);
  render(time);
  requestAnimationFrame(frame);
}

window.addEventListener("keydown", event => {
  const key = event.key.toLowerCase();

  if ([
    "arrowup", "arrowdown",
    "arrowleft", "arrowright", " "
  ].includes(key)) {
    event.preventDefault();
  }

  if (key === "r" && state !== "playing") {
    reset();
    return;
  }

  if (key === "shift" && !event.repeat) boost();
  keys.add(key);
});

window.addEventListener("keyup", event => {
  keys.delete(event.key.toLowerCase());
});

window.addEventListener("blur", () => keys.clear());

reset();
requestAnimationFrame(frame);


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
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
const rand = (lo, hi) => lo + Math.random() * (hi - lo);
let hero, checkpoints, completed, remaining, boostCooldown, boostTime, state;
let particles = [];
let lastTime = null;

function reset() {
  hero = { x: 150, y: 270, vx: 0, vy: 0, face: 1 };
  checkpoints = [
    { x: 330, y: 210 }, { x: 590, y: 340 },
    { x: 800, y: 175 }, { x: 660, y: 425 },
    { x: 380, y: 380 }, { x: 190, y: 155 },
    { x: 515, y: 130 }, { x: 825, y: 295 }
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
  ui.timerBar.style.background = remaining > 15 ? "#52d7e9" : "#f26b63";
  ui.progress.textContent = `${completed}/${TOTAL}`;
  ui.boost.textContent = boostCooldown <= 0 ? "READY" : `${boostCooldown.toFixed(1)}s`;
}

function burst(x, y, count, color = "#65ecff") {
  for (let i = 0; i < count; i++) {
    const a = rand(0, Math.PI * 2);
    const speed = rand(45, 230);
    particles.push({
      x, y,
      vx: Math.cos(a) * speed,
      vy: Math.sin(a) * speed,
      life: rand(.3, .8),
      maxLife: .8,
      color,
      size: rand(2, 5)
    });
  }
}

function boost() {
  if (state !== "playing" || boostCooldown > 0) return;
  boostCooldown = 2.4;
  boostTime = .28;

  let dx = Number(keys.has("d") || keys.has("arrowright")) -
    Number(keys.has("a") || keys.has("arrowleft"));
  let dy = Number(keys.has("s") || keys.has("arrowdown")) -
    Number(keys.has("w") || keys.has("arrowup"));

  if (!dx && !dy) dx = hero.face;
  const len = Math.hypot(dx, dy) || 1;
  hero.vx = dx / len * 750;
  hero.vy = dy / len * 750;
  burst(hero.x, hero.y + 30, 24, "#81f4ff");
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

  const len = Math.hypot(dx, dy) || 1;
  dx /= len;
  dy /= len;

  if (dx) hero.face = Math.sign(dx);

  if (boostTime <= 0) {
    hero.vx = dx * 330;
    hero.vy = dy * 330;
  }

  hero.x = clamp(hero.x + hero.vx * dt, 40, W - 40);
  hero.y = clamp(hero.y + hero.vy * dt, 135, H - 65);

  if ((dx || dy || boostTime > 0) && Math.random() < .7) {
    particles.push({
      x: hero.x + rand(-12, 12),
      y: hero.y + 51,
      vx: rand(-35, 35),
      vy: rand(80, 180),
      life: .25,
      maxLife: .25,
      color: boostTime > 0 ? "#fff5ad" : "#62e7ff",
      size: rand(2, 5)
    });
  }

  const gate = checkpoints[completed];

  if (gate && Math.hypot(hero.x - gate.x, hero.y - gate.y) < 48) {
    burst(gate.x, gate.y, 35, "#eec56c");
    completed++;
    if (completed === TOTAL) state = "won";
  }

  updateHUD();
}

function fillRect(x, y, w, h, color) {
  ctx.fillStyle = color;
  ctx.fillRect(x, y, w, h);
}

function disk(x, y, r, color) {
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.arc(x, y, r, 0, Math.PI * 2);
  ctx.fill();
}

function poly(points, color, stroke = "#1b1322", line = 2) {
  ctx.beginPath();
  ctx.moveTo(points[0][0], points[0][1]);

  for (let i = 1; i < points.length; i++) {
    ctx.lineTo(points[i][0], points[i][1]);
  }

  ctx.closePath();
  ctx.fillStyle = color;
  ctx.fill();

  if (stroke) {
    ctx.strokeStyle = stroke;
    ctx.lineWidth = line;
    ctx.stroke();
  }
}

function drawBackground(time) {
  const sky = ctx.createLinearGradient(0, 0, 0, H);
  sky.addColorStop(0, "#080f22");
  sky.addColorStop(.65, "#172e4a");
  sky.addColorStop(1, "#4b3851");
  fillRect(0, 0, W, H, sky);

  const glow = ctx.createRadialGradient(760, 150, 5, 760, 150, 360);
  glow.addColorStop(0, "rgba(98,221,238,.22)");
  glow.addColorStop(1, "rgba(98,221,238,0)");
  fillRect(0, 0, W, H, glow);

  disk(760, 125, 37, "#c7d6df");
  disk(748, 118, 36, "#152740");

  ctx.save();
  ctx.strokeStyle = "rgba(83,212,231,.09)";
  ctx.lineWidth = 1;

  for (let i = 0; i <= 16; i++) {
    const x = i * 64;
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, H);
    ctx.stroke();
  }

  for (let y = 0; y < H; y += 45) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(W, y);
    ctx.stroke();
  }

  ctx.restore();

  for (let i = 0; i < 24; i++) {
    const x = i * 43;
    const height = 100 + (Math.sin(i * 2.71) + 1) * 62;
    const y = H - height;

    fillRect(x, y, 39, height, i % 3 ? "#101b32" : "#14253c");

    for (let wy = y + 15; wy < H - 12; wy += 21) {
      for (let wx = x + 8; wx < x + 34; wx += 13) {
        if ((Math.floor(wx + wy + i) % 4) !== 0) {
          fillRect(wx, wy, 4, 7, "#876c70");
        }
      }
    }
  }

  fillRect(0, H - 17, W, 17, "#0a1224");
  fillRect(0, H - 18, W, 2, "#b48152");

  ctx.fillStyle = "rgba(126,234,245,.46)";
  ctx.font = "bold 13px monospace";
  ctx.textAlign = "left";
  ctx.fillText("STARK // SIMULATION ACTIVE", 23, H - 34);
  ctx.textAlign = "right";
  ctx.fillText(`ALTITUDE  ${Math.round(500 - hero.y)} M`, W - 24, H - 34);
}

function drawHero(time) {
  if (window.AurelArmor?.draw(ctx, hero, time, boostTime > 0)) return;
  ctx.save();
  ctx.translate(hero.x, hero.y + Math.sin(time * .006) * 2);
  ctx.scale(hero.face, 1);

  const red = "#a51f35";
  const redLight = "#e04b4a";
  const gold = "#e8ad50";
  const goldLight = "#ffe09b";
  const edge = "#180e22";

  for (const x of [-13, 13]) {
    ctx.save();
    ctx.shadowColor = "#4ceaff";
    ctx.shadowBlur = boostTime > 0 ? 35 : 17;

    poly([
      [x - 9, 46], [x + 9, 46],
      [x + 6, 66 + (boostTime > 0 ? 18 : 0)],
      [x, 80 + (boostTime > 0 ? 22 : 0)],
      [x - 6, 66 + (boostTime > 0 ? 18 : 0)]
    ], "#5beaff", null);

    poly([
      [x - 4, 49], [x + 4, 49],
      [x, 70 + (boostTime > 0 ? 18 : 0)]
    ], "#fff7b2", null);

    ctx.restore();
  }

  for (const x of [-14, 14]) {
    poly([
      [x - 11, 15], [x + 11, 15],
      [x + 10, 43], [x + 7, 52],
      [x - 9, 52], [x - 12, 39]
    ], red, edge, 2.5);

    poly([
      [x - 8, 28], [x + 8, 28],
      [x + 7, 40], [x - 8, 40]
    ], gold);

    poly([
      [x - 11, 44], [x + 11, 44],
      [x + 13, 55], [x - 13, 55]
    ], redLight);
  }

  for (const s of [-1, 1]) {
    ctx.save();
    ctx.scale(s, 1);

    poly([
      [21, -32], [35, -28], [43, -14],
      [37, 4], [24, 4], [20, -12]
    ], redLight);

    poly([
      [27, 3], [40, 4], [42, 28],
      [30, 31], [23, 20]
    ], red);

    poly([
      [28, 15], [40, 15],
      [39, 24], [29, 26]
    ], gold);

    ctx.save();
    ctx.shadowColor = "#65eaff";
    ctx.shadowBlur = 12;
    disk(35, 30, 5, "#c6fcff");
    ctx.restore();

    ctx.restore();
  }

  poly([
    [-26, -34], [26, -34], [29, -5],
    [22, 23], [-22, 23], [-29, -5]
  ], red, edge, 3);

  poly([
    [-23, -28], [-4, -22], [0, -10],
    [-18, -5], [-26, -12]
  ], gold);

  poly([
    [23, -28], [4, -22], [0, -10],
    [18, -5], [26, -12]
  ], gold);

  poly([
    [-20, 9], [-4, 14], [4, 14],
    [20, 9], [17, 22], [-17, 22]
  ], "#7d1b32");

  poly([
    [-12, -3], [0, -9], [12, -3],
    [9, 8], [-9, 8]
  ], "#121b2e");

  ctx.save();
  ctx.shadowColor = "#65f3ff";
  ctx.shadowBlur = 21;
  disk(0, 0, 9, "#7aefff");
  disk(0, 0, 5, "#f3ffff");
  ctx.restore();

  poly([
    [-21, -68], [-14, -80], [14, -80],
    [21, -68], [19, -46], [9, -36],
    [-9, -36], [-19, -46]
  ], red, edge, 3);

  poly([
    [-15, -67], [15, -67], [13, -48],
    [6, -41], [-6, -41], [-13, -48]
  ], gold);

  poly([
    [-14, -68], [-8, -75],
    [8, -75], [14, -68]
  ], goldLight);

  ctx.save();
  ctx.shadowColor = "#67edff";
  ctx.shadowBlur = 14;

  poly([
    [-12, -59], [-2, -57],
    [-5, -53], [-13, -55]
  ], "#d5fcff", null);

  poly([
    [12, -59], [2, -57],
    [5, -53], [13, -55]
  ], "#d5fcff", null);

  ctx.restore();

  poly([
    [-4, -46], [4, -46],
    [2, -41], [-2, -41]
  ], "#aa773e", null);

  ctx.restore();
}

function drawCheckpoint(gate, time) {
  const pulse = Math.sin(time * .005) * 3;
  const r = 43 + pulse;

  ctx.save();
  ctx.translate(gate.x, gate.y);
  ctx.rotate(time * .0003);

  ctx.shadowColor = "#55eaff";
  ctx.shadowBlur = 22;
  ctx.strokeStyle = "#64eaff";
  ctx.lineWidth = 7;

  ctx.beginPath();
  ctx.arc(0, 0, r, 0, Math.PI * 2);
  ctx.stroke();

  ctx.shadowBlur = 0;
  ctx.strokeStyle = "rgba(200,249,255,.6)";
  ctx.lineWidth = 2;

  ctx.beginPath();
  ctx.arc(0, 0, r - 10, 0, Math.PI * 2);
  ctx.stroke();

  ctx.strokeStyle = "#edbe66";
  ctx.lineWidth = 5;

  for (let a = 0; a < Math.PI * 2; a += Math.PI / 2) {
    ctx.beginPath();
    ctx.arc(0, 0, r + 6, a, a + .25);
    ctx.stroke();
  }

  ctx.restore();

  ctx.textAlign = "center";
  ctx.fillStyle = "#e7c27c";
  ctx.font = "bold 15px Arial";
  ctx.fillText(
    `FLIGHT GATE  ${String(completed + 1).padStart(2, "0")}`,
    gate.x,
    gate.y - 66
  );
}

function drawParticles() {
  for (const p of particles) {
    ctx.save();
    ctx.globalAlpha = clamp(p.life / p.maxLife, 0, 1);
    ctx.shadowColor = p.color;
    ctx.shadowBlur = 9;
    disk(p.x, p.y, p.size, p.color);
    ctx.restore();
  }
}

function drawOverlay() {
  if (state === "playing") return;

  ctx.save();
  fillRect(0, 0, W, H, "rgba(4,9,22,.85)");

  const x = W / 2 - 265;
  const y = 143;
  const width = 530;
  const height = 257;

  fillRect(x, y, width, height, "#101d32");

  ctx.strokeStyle = "#b53645";
  ctx.lineWidth = 4;
  ctx.strokeRect(x, y, width, height);

  fillRect(x, y, width, 6, "#e8b761");

  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillStyle = "#74e7f2";
  ctx.font = "bold 15px Arial";
  ctx.fillText(
    "STARK INDUSTRIES  /  FLIGHT SYSTEMS",
    W / 2,
    182
  );

  ctx.fillStyle = state === "won" ? "#f4d185" : "#ff8181";
  ctx.font = "bold 41px Arial";
  ctx.fillText(
    state === "won" ? "MISSION COMPLETE" : "MISSION FAILED",
    W / 2,
    244
  );

  ctx.fillStyle = "#f5f1e8";
  ctx.font = "bold 21px Arial";
  ctx.fillText(
    state === "won"
      ? `FLIGHT TIME: ${(LIMIT - remaining).toFixed(1)} SECONDS`
      : `CHECKPOINTS CLEARED: ${completed}/${TOTAL}`,
    W / 2,
    296
  );

  fillRect(W / 2 - 155, 329, 310, 47, "#e7b85e");

  ctx.fillStyle = "#121b2b";
  ctx.font = "bold 19px Arial";
  ctx.fillText("PRESS R TO RESTART", W / 2, 353);

  ctx.restore();
}

function render(time) {
  ctx.clearRect(0, 0, W, H);
  drawBackground(time);

  if (state === "playing") {
    const gate = checkpoints[completed];
    if (gate) drawCheckpoint(gate, time);
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

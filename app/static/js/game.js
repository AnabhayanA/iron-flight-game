
"use strict";

const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");
const W = canvas.width;
const H = canvas.height;
const TAU = Math.PI * 2;
const keys = new Set();

const ui = {
  armor: document.getElementById("armor-fill"),
  value: document.getElementById("armor-value"),
  kills: document.getElementById("kills-value"),
  dash: document.getElementById("dash-value")
};

const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const rnd = (a, b) => a + Math.random() * (b - a);
const dist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
const hash = n => {
  const x = Math.sin(n * 127.1 + 78.233) * 43758.5453;
  return x - Math.floor(x);
};

let hero, drones, shots, missiles, enemyShots, particles, texts;
let boss, kills, spawnTimer, shootTimer, missileTimer;
let shake, state, elapsed, bossWarning, cameraX;

function box(x, y, w, h, color, outline = null, sw = 2) {
  ctx.fillStyle = color;
  ctx.fillRect(x, y, w, h);
  if (outline) {
    ctx.strokeStyle = outline;
    ctx.lineWidth = sw;
    ctx.strokeRect(x, y, w, h);
  }
}

function disk(x, y, r, color, outline = null, sw = 2) {
  ctx.beginPath();
  ctx.arc(x, y, r, 0, TAU);
  ctx.fillStyle = color;
  ctx.fill();
  if (outline) {
    ctx.strokeStyle = outline;
    ctx.lineWidth = sw;
    ctx.stroke();
  }
}

function poly(points, color, outline = "#10152b", sw = 2) {
  ctx.beginPath();
  points.forEach(([x, y], i) => {
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.closePath();
  ctx.fillStyle = color;
  ctx.fill();
  if (outline) {
    ctx.strokeStyle = outline;
    ctx.lineWidth = sw;
    ctx.lineJoin = "round";
    ctx.stroke();
  }
}

function line(x, y, x2, y2, color, sw = 2) {
  ctx.beginPath();
  ctx.moveTo(x, y);
  ctx.lineTo(x2, y2);
  ctx.strokeStyle = color;
  ctx.lineWidth = sw;
  ctx.lineCap = "round";
  ctx.stroke();
}

function words(message, x, y, size, color = "#fff") {
  ctx.save();
  ctx.font = `900 ${size}px Impact, "Arial Black", sans-serif`;
  ctx.textAlign = "center";
  ctx.lineJoin = "round";
  ctx.lineWidth = Math.max(3, size * .11);
  ctx.strokeStyle = "#10152b";
  ctx.strokeText(message, x, y);
  ctx.fillStyle = color;
  ctx.fillText(message, x, y);
  ctx.restore();
}

function burst(x, y, color, count = 15, power = 190) {
  for (let i = 0; i < count; i++) {
    const angle = rnd(0, TAU);
    const speed = rnd(35, power);
    const life = rnd(.2, .65);
    particles.push({
      x, y,
      vx: Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed,
      life,
      max: life,
      size: rnd(2, 5),
      color
    });
  }
}

function popup(message, x, y, color = "#ffe05c") {
  texts.push({ message, x, y, color, life: .8 });
}

function reset() {
  hero = {
    x: 180, y: 265,
    vx: 0, vy: 0,
    hp: 100, face: 1,
    inv: 0, dash: 0, dashTime: 0,
    aim: 0, recoil: 0, flash: 0,
    arm: 0, tilt: 0
  };

  drones = [];
  shots = [];
  missiles = [];
  enemyShots = [];
  particles = [];
  texts = [];
  boss = null;
  kills = 0;
  spawnTimer = 1;
  shootTimer = 0;
  missileTimer = 0;
  shake = 0;
  elapsed = 0;
  bossWarning = 0;
  cameraX = 0;
  state = "playing";
  keys.clear();
  updateHUD();
}

function updateHUD() {
  ui.value.textContent = `${Math.ceil(hero.hp)}%`;
  ui.armor.style.width = `${hero.hp}%`;
  ui.armor.style.background =
    hero.hp > 50 ? "#39d58a" :
    hero.hp > 25 ? "#ffd347" : "#f04d4c";

  ui.kills.textContent = boss
    ? `BOSS ${Math.ceil(boss.hp)}%`
    : `${kills}/5`;

  ui.dash.textContent =
    hero.dash <= 0 ? "READY" : `${hero.dash.toFixed(1)}s`;
}

function spawnDrone() {
  if (kills >= 5 || drones.length >= 3) return;

  const fast = Math.random() < .3;
  drones.push({
    x: W + 45,
    y: rnd(145, H - 115),
    hp: fast ? 2 : 3,
    r: fast ? 21 : 26,
    speed: fast ? 140 : 95,
    fire: rnd(1.1, 2.1),
    phase: rnd(0, TAU),
    fast,
    flash: 0
  });
}

function spawnBoss() {
  if (boss || kills < 5) return;

  boss = {
    x: W + 135,
    y: 265,
    hp: 100,
    r: 75,
    phase: 0,
    fire: 1.7,
    flash: 0
  };

  drones = [];
  enemyShots = [];
  bossWarning = 3;
  shake = 12;
}

function palm() {
  const a = hero.arm;
  return {
    x: hero.x + hero.face * (44 + a * 21 - hero.recoil * 6),
    y: hero.y + 10 - a * 35
  };
}

function shoot() {
  if (state !== "playing" || shootTimer > 0) return;

  shootTimer = .18;
  hero.aim = .35;
  hero.arm = 1;
  hero.flash = .13;
  hero.recoil = 1;

  const p = palm();

  shots.push({
    x: p.x + hero.face * 13,
    y: p.y,
    vx: hero.face * 800,
    r: 9,
    life: 1.5
  });

  burst(p.x, p.y, "#86f5ff", 8, 120);
  shake = Math.max(shake, 2);
}

function missile() {
  if (state !== "playing" || missileTimer > 0) return;

  missileTimer = 3.5;

  const target = boss || drones.reduce((best, d) => {
    if (!best || dist(hero, d) < dist(hero, best)) return d;
    return best;
  }, null);

  missiles.push({
    x: hero.x + hero.face * 20,
    y: hero.y - 32,
    vx: hero.face * 330,
    vy: -100,
    angle: hero.face === 1 ? 0 : Math.PI,
    target,
    life: 4,
    trail: []
  });

  burst(hero.x, hero.y - 32, "#ffd05e", 12, 145);
  popup("MISSILE!", hero.x, hero.y - 100);
}

function dash() {
  if (state !== "playing" || hero.dash > 0) return;

  hero.dash = 2.4;
  hero.dashTime = .19;
  hero.inv = Math.max(hero.inv, .25);

  if (keys.has("a") || keys.has("arrowleft")) hero.face = -1;
  if (keys.has("d") || keys.has("arrowright")) hero.face = 1;

  hero.vx = hero.face * 870;
  burst(hero.x, hero.y, "#6eeaff", 25, 280);
  popup("BOOST!", hero.x, hero.y - 105, "#83f6ff");
}

function hurt(amount) {
  if (state !== "playing" || hero.inv > 0) return;

  hero.hp = Math.max(0, hero.hp - amount);
  hero.inv = .75;
  shake = 9;
  burst(hero.x, hero.y, "#ff6c56", 20, 230);
  popup("HIT!", hero.x, hero.y - 95, "#ff6868");

  if (hero.hp <= 0) {
    state = "lost";
    burst(hero.x, hero.y, "#ffcf50", 55, 340);
  }
}

function damageEnemy(target, amount) {
  if (!target || target.hp <= 0) return;

  target.hp = Math.max(0, target.hp - amount);
  target.flash = .12;
  burst(target.x, target.y, "#8af4ff", 9, 130);

  if (target.hp > 0) return;

  shake = 8;
  burst(target.x, target.y, "#ffd14f", 36, 300);
  burst(target.x, target.y, "#f4564d", 18, 220);
  popup("KABOOM!", target.x, target.y - 55);

  if (target === boss) {
    state = "won";
    boss = null;
    enemyShots = [];
    burst(W - 170, H / 2, "#fff0a0", 55, 400);
  } else {
    kills++;
    drones = drones.filter(d => d.hp > 0);
    if (kills >= 5) spawnBoss();
  }
}

function fireEnemy(x, y, speed, offset = 0) {
  const a = Math.atan2(hero.y - y, hero.x - x) + offset;
  enemyShots.push({
    x, y,
    vx: Math.cos(a) * speed,
    vy: Math.sin(a) * speed,
    r: 7,
    life: 4
  });
}

function updateHero(dt) {
  let dx = Number(keys.has("d") || keys.has("arrowright")) -
           Number(keys.has("a") || keys.has("arrowleft"));
  let dy = Number(keys.has("s") || keys.has("arrowdown")) -
           Number(keys.has("w") || keys.has("arrowup"));

  const length = Math.hypot(dx, dy) || 1;
  dx /= length;
  dy /= length;

  if (dx) hero.face = dx;

  hero.inv = Math.max(0, hero.inv - dt);
  hero.dash = Math.max(0, hero.dash - dt);
  hero.dashTime = Math.max(0, hero.dashTime - dt);
  hero.aim = Math.max(0, hero.aim - dt);
  hero.flash = Math.max(0, hero.flash - dt);
  hero.recoil = Math.max(0, hero.recoil - dt * 7);
  shootTimer = Math.max(0, shootTimer - dt);
  missileTimer = Math.max(0, missileTimer - dt);

  const targetArm = hero.aim > 0 || keys.has(" ") ? 1 : 0;
  hero.arm += (targetArm - hero.arm) * Math.min(1, dt * 16);

  if (hero.dashTime <= 0) {
    const friction = Math.exp(-6 * dt);
    hero.vx = (hero.vx + dx * 1400 * dt) * friction;
    hero.vy = (hero.vy + dy * 1400 * dt) * friction;
  }

  hero.x = clamp(hero.x + hero.vx * dt, 75, W - 85);
  hero.y = clamp(hero.y + hero.vy * dt, 125, H - 115);

  const desiredTilt = clamp(hero.vx / 950, -.14, .14);
  hero.tilt += (desiredTilt - hero.tilt) * Math.min(1, dt * 8);

  if (keys.has(" ")) shoot();

  if (hero.dashTime > 0) {
    burst(hero.x - hero.face * 25, hero.y + 22,
      "#70ecff", 2, 100);
  }

  cameraX += (Math.abs(hero.vx) * .18 + 16) * dt;
}

function updateDrones(dt) {
  if (!boss && kills < 5) {
    spawnTimer -= dt;
    if (spawnTimer <= 0) {
      spawnDrone();
      spawnTimer = rnd(1.4, 2.1);
    }
  }

  for (const d of drones) {
    d.phase += dt * (d.fast ? 4 : 2);
    d.flash = Math.max(0, d.flash - dt);

    if (d.x > W - 150) {
      d.x -= d.speed * dt;
    } else {
      const targetX = clamp(hero.x + 190, 245, W - 110);
      d.x += clamp(targetX - d.x, -90, 90) * dt;
    }

    const desiredY =
      hero.y + Math.sin(d.phase) * (d.fast ? 75 : 45);

    d.y += clamp(desiredY - d.y, -110, 110) * dt;
    d.y = clamp(d.y, 125, H - 95);

    d.fire -= dt;
    if (d.fire <= 0) {
      d.fire = rnd(1.2, 2.2);
      fireEnemy(d.x, d.y, d.fast ? 300 : 250);
    }

    if (dist(hero, d) < d.r + 25) hurt(14);
  }
}

function updateBoss(dt) {
  if (!boss) return;

  boss.phase += dt;
  boss.flash = Math.max(0, boss.flash - dt);

  if (boss.x > W - 165) boss.x -= 100 * dt;
  boss.y = 265 + Math.sin(boss.phase * 1.3) * 100;
  boss.fire -= dt;

  if (boss.fire <= 0) {
    boss.fire = 1.3;
    for (const offset of [-.23, 0, .23]) {
      fireEnemy(boss.x - 50, boss.y, 300, offset);
    }
    burst(boss.x - 50, boss.y, "#ff7373", 9, 120);
  }

  if (dist(hero, boss) < boss.r + 25) hurt(22);
}

function updateShots(dt) {
  for (const s of shots) {
    const oldX = s.x;
    s.x += s.vx * dt;
    s.life -= dt;

    const targets = boss ? [boss] : drones.slice();

    for (const target of targets) {
      if (s.life <= 0 || target.hp <= 0) continue;

      if (
        target.x + target.r >= Math.min(oldX, s.x) &&
        target.x - target.r <= Math.max(oldX, s.x) &&
        Math.abs(target.y - s.y) < target.r + s.r
      ) {
        s.life = 0;
        damageEnemy(target, target === boss ? 4 : 1);
        break;
      }
    }
  }

  shots = shots.filter(s =>
    s.life > 0 && s.x > -40 && s.x < W + 40);
}

function updateMissiles(dt) {
  for (const m of missiles) {
    m.life -= dt;

    if (!m.target || m.target.hp <= 0) {
      m.target = boss ||
        drones.find(d => d.hp > 0) || null;
    }

    if (m.target) {
      const a = Math.atan2(
        m.target.y - m.y, m.target.x - m.x
      );
      const blend = Math.min(1, dt * 5);
      m.vx += (Math.cos(a) * 430 - m.vx) * blend;
      m.vy += (Math.sin(a) * 430 - m.vy) * blend;
    }

    m.x += m.vx * dt;
    m.y += m.vy * dt;
    m.angle = Math.atan2(m.vy, m.vx);

    m.trail.push({ x: m.x, y: m.y });
    if (m.trail.length > 15) m.trail.shift();

    if (m.target && m.target.hp > 0 &&
        dist(m, m.target) < m.target.r + 10) {
      m.life = 0;
      damageEnemy(m.target, m.target === boss ? 22 : 3);
      burst(m.x, m.y, "#ffbb52", 27, 250);
      shake = 9;
    }
  }

  missiles = missiles.filter(m =>
    m.life > 0 &&
    m.x > -60 && m.x < W + 60 &&
    m.y > -60 && m.y < H + 60);
}

function updateEnemyShots(dt) {
  for (const s of enemyShots) {
    s.x += s.vx * dt;
    s.y += s.vy * dt;
    s.life -= dt;

    if (dist(s, hero) < s.r + 25) {
      s.life = 0;
      hurt(boss ? 12 : 10);
    }
  }

  enemyShots = enemyShots.filter(s =>
    s.life > 0 &&
    s.x > -30 && s.x < W + 30 &&
    s.y > -30 && s.y < H + 30);
}

function updateEffects(dt) {
  for (const p of particles) {
    p.x += p.vx * dt;
    p.y += p.vy * dt;
    p.vx *= Math.exp(-2 * dt);
    p.vy *= Math.exp(-2 * dt);
    p.life -= dt;
  }
  particles = particles.filter(p => p.life > 0);

  for (const t of texts) {
    t.y -= 37 * dt;
    t.life -= dt;
  }
  texts = texts.filter(t => t.life > 0);

  shake = Math.max(0, shake - 30 * dt);
}

function update(dt) {
  elapsed += dt;
  updateEffects(dt);

  if (state !== "playing") return;

  bossWarning = Math.max(0, bossWarning - dt);

  updateHero(dt);
  updateDrones(dt);
  updateBoss(dt);
  updateShots(dt);

  if (state === "playing") updateMissiles(dt);
  if (state === "playing") updateEnemyShots(dt);

  updateHUD();
}

// Premium comic environment: bright, layered, and readable.
function background(t) {
  const sky = ctx.createLinearGradient(0, 0, 0, H);
  sky.addColorStop(0, "#3986c6");
  sky.addColorStop(.62, "#91d9ee");
  sky.addColorStop(1, "#ffcc83");
  box(0, 0, W, H, sky);

  // Soft sun halo.
  const halo = ctx.createRadialGradient(
    772, 150, 25, 772, 150, 220
  );
  halo.addColorStop(0, "rgba(255,240,171,.85)");
  halo.addColorStop(1, "rgba(255,240,171,0)");
  box(0, 0, W, H, halo);

  disk(772, 150, 64, "#ffe17a", "#263452", 4);
  disk(772, 150, 49, "#ffefac");

  // Controlled halftone texture in the sky.
  for (let y = 15; y < 300; y += 19) {
    for (let x = 15; x < W; x += 19) {
      disk(x, y, 1.25, "rgba(22,40,75,.12)");
    }
  }

  // Distant skyline.
  const far = cameraX * .16;
  for (let i = -2; i < 25; i++) {
    const x = i * 48 - (far % 48);
    const h = 100 + hash(i + 60) * 135;
    box(x, H - h, 44, h, "#83a8c3");
  }

  // Midground skyline.
  const mid = cameraX * .42;
  for (let i = -2; i < 19; i++) {
    const x = i * 65 - (mid % 65);
    const h = 135 + hash(i + 80) * 185;
    const y = H - h;

    box(x, y, 61, h,
      i % 3 === 0 ? "#3c567f" : "#4b6990",
      "#253450", 2);

    for (let wy = y + 16; wy < H - 10; wy += 23) {
      for (let wx = x + 10; wx < x + 54; wx += 18) {
        if (hash(i * 700 + wy * 9 + wx) > .35) {
          box(wx, wy, 8, 11, "#ffe8a5");
        }
      }
    }
  }

  // Foreground skyline.
  const near = cameraX * .85;
  for (let i = -2; i < 11; i++) {
    const x = i * 116 - (near % 116);
    const h = 105 + hash(i + 140) * 165;
    const y = H - h;

    box(x, y, 108, h,
      i % 2 ? "#25385e" : "#30466e",
      "#101a34", 3);

    box(x + 7, y + 6, 4, h - 6, "#4c6790");

    for (let wy = y + 18; wy < H - 10; wy += 24) {
      for (let wx = x + 20; wx < x + 98; wx += 22) {
        const lit = hash(i * 1300 + wy * 7 + wx) > .42;
        box(wx, wy, 10, 12,
          lit ? "#ffd48a" : "#405b80");
      }
    }
  }

  box(0, H - 29, W, 29, "#152440");
  box(0, H - 29, W, 5, "#101a34");

  // Sparse movement streaks.
  const speed = Math.abs(hero.vx) / 870;
  if (speed > .18) {
    ctx.save();
    ctx.globalAlpha = speed * .5;
    for (let i = 0; i < 8; i++) {
      const x = (hash(i + 10) * W + elapsed * 130) % W;
      const y = 155 + hash(i + 90) * 270;
      line(x, y, x + 45 + speed * 60, y, "#fff", 2);
    }
    ctx.restore();
  }
}

// Sleek red-and-gold armor with metallic highlights.
function drawHero(t) {
  if (hero.inv > 0 && Math.floor(t / 75) % 2 === 0) return;

  ctx.save();
  ctx.translate(hero.x, hero.y + Math.sin(t * .006) * 2);
  ctx.rotate(hero.tilt);
  ctx.scale(hero.face, 1);

  const ink = "#10152b";
  const red = "#b72a3d";
  const darkRed = "#78243b";
  const bright = "#ed5051";
  const gold = "#e9b34b";
  const lightGold = "#fff0b0";
  const cyan = "#76efff";

  // Motion afterimages while boosting.
  if (hero.dashTime > 0) {
    for (let i = 1; i <= 3; i++) {
      disk(-i * 23, 0, 25 - i * 4,
        `rgba(79,229,255,${.2 / i})`);
    }
  }

  // Jetpack.
  poly([[-20,-28],[-30,-20],[-31,20],[-18,25]], darkRed);
  poly([[20,-28],[30,-20],[31,20],[18,25]], darkRed);

  // Long, athletic legs and jet boots.
  for (const x of [-11, 11]) {
    const flame = 12 + Math.sin(t * .036 + x) * 7;

    poly([[x-8,17],[x+8,17],[x+9,39],
      [x+7,54],[x-8,54],[x-9,39]], red);

    poly([[x-6,19],[x+5,19],[x+6,33],
      [x-5,34]], bright);

    disk(x, 40, 5, gold, ink);

    poly([[x-8,45],[x+8,45],[x+9,73],
      [x-9,73]], gold);

    poly([[x-5,48],[x+4,48],[x+4,65],
      [x-5,65]], lightGold, null);

    poly([[x-10,69],[x+10,69],[x+11,81],
      [x-10,81]], red);

    ctx.save();
    ctx.shadowColor = cyan;
    ctx.shadowBlur = 19;
    poly([[x-6,81],[x+6,81],[x+5,96+flame],
      [x,104+flame],[x-5,96+flame]], "#38d8ff", null);
    poly([[x-3,82],[x+3,82],[x,93+flame]],
      "#fffbd5", null);
    ctx.restore();
  }

  // Rear arm.
  poly([[-22,-31],[-32,-25],[-34,-5],
    [-27,8],[-19,4],[-18,-19]], red);
  poly([[-32,0],[-24,1],[-24,24],[-33,25]], gold);

  // Narrow torso.
  poly([[-23,-30],[23,-30],[25,-12],
    [18,11],[13,27],[-13,27],[-18,11],[-25,-12]], red);

  poly([[-21,-25],[-5,-28],[-11,-7],
    [-19,5],[-24,-10]], bright);

  poly([[21,-25],[5,-28],[11,-7],
    [19,5],[24,-10]], bright);

  // Metallic gold chest plates.
  poly([[-18,-23],[-3,-27],[-3,-8],
    [-13,5],[-21,-7]], gold);

  poly([[18,-23],[3,-27],[3,-8],
    [13,5],[21,-7]], gold);

  poly([[-16,-21],[-8,-23],[-12,-12],
    [-18,-10]], lightGold, null);

  poly([[16,-21],[8,-23],[12,-12],
    [18,-10]], lightGold, null);

  // Abdomen and waist.
  poly([[-15,9],[15,9],[11,24],[-11,24]], darkRed);
  for (let y = 13; y < 24; y += 5) {
    line(-9, y, 9, y, "#ed6b61", 2);
  }
  poly([[-13,25],[13,25],[10,34],[-10,34]], gold);

  // Chest reactor.
  ctx.save();
  ctx.shadowColor = cyan;
  ctx.shadowBlur = 22;
  disk(0, -10, 13, "#e2fcff", ink, 3);
  disk(0, -10, 8, cyan);
  disk(0, -10, 4, "#fff");
  ctx.restore();

  // Neck and helmet.
  poly([[-10,-37],[10,-37],[8,-29],[-8,-29]], darkRed);

  poly([[-20,-62],[-16,-78],[-8,-86],
    [8,-86],[16,-78],[20,-62],[18,-45],
    [11,-36],[-11,-36],[-18,-45]], red);

  poly([[-14,-76],[-8,-83],[8,-83],
    [14,-76],[10,-70],[-10,-70]], bright);

  poly([[-17,-65],[17,-65],[16,-51],
    [10,-40],[-10,-40],[-16,-51]], gold);

  poly([[-15,-63],[-7,-64],[-11,-51],
    [-16,-53]], lightGold, null);

  poly([[-10,-41],[10,-41],[6,-38],
    [-6,-38]], "#ad7c34");

  box(-22, -62, 5, 13, gold);
  box(17, -62, 5, 13, gold);

  ctx.save();
  ctx.shadowColor = cyan;
  ctx.shadowBlur = 14;
  poly([[-15,-57],[-3,-55],[-5,-50],
    [-15,-52]], "#c4faff");
  poly([[3,-55],[15,-57],[15,-52],
    [5,-50]], "#c4faff");
  ctx.restore();

  // Smooth animated repulsor arm.
  const a = hero.arm;
  const recoil = hero.recoil * 6;
  const elbowX = 30 + a * 11 - recoil * .4;
  const elbowY = -7 - a * 16;
  const handX = 44 + a * 21 - recoil;
  const handY = 10 - a * 35;

  poly([[18,-34],[30,-32],[35,-23],
    [27,-16],[18,-20]], bright);

  line(22, -26, elbowX, elbowY, ink, 17);
  line(22, -26, elbowX, elbowY, red, 12);
  disk(elbowX, elbowY, 7, gold, ink);

  line(elbowX, elbowY, handX, handY, ink, 17);
  line(elbowX, elbowY, handX, handY, gold, 12);
  line(elbowX+1, elbowY-2,
    handX+1, handY-2, lightGold, 2);

  disk(handX, handY, 9, red, ink);

  ctx.save();
  ctx.shadowColor = cyan;
  ctx.shadowBlur = 18;
  disk(handX+3, handY, 5, cyan);
  disk(handX+3, handY, 2, "#fff");
  ctx.restore();

  if (hero.flash > 0) {
    const power = hero.flash / .13;
    ctx.save();
    ctx.shadowColor = cyan;
    ctx.shadowBlur = 27;
    disk(handX+14, handY, 22*power,
      `rgba(72,235,255,${.3*power})`);
    disk(handX+14, handY, 10*power, "#b5faff");
    disk(handX+14, handY, 4*power, "#fff");
    ctx.restore();
  }

  ctx.restore();
}

function drawDrone(d, t) {
  ctx.save();
  ctx.translate(d.x, d.y + Math.sin(t*.005+d.phase)*3);

  const metal = d.fast ? "#77568b" : "#58677e";

  line(-35,-8,-12,-8,"#10152b",5);
  line(12,-8,35,-8,"#10152b",5);

  disk(-35,-8,10,"#58d9ed","#10152b",3);
  disk(35,-8,10,"#58d9ed","#10152b",3);

  poly([[-26,-15],[-14,-25],[14,-25],
    [26,-15],[26,15],[14,25],[-14,25],[-26,15]],
    d.flash>0?"#fff":metal,"#10152b",4);

  poly([[-18,-12],[18,-12],[14,14],[-14,14]],
    "#303d58");

  ctx.save();
  ctx.shadowColor = "#ff5867";
  ctx.shadowBlur = 14;
  disk(0,0,11,"#f34c57","#10152b",3);
  disk(0,0,5,"#ffb0a2");
  ctx.restore();

  for (let i=0; i<d.hp; i++) {
    box(-14+i*11,-38,8,4,"#ff6565");
  }

  ctx.restore();
}

function drawBoss() {
  if (!boss) return;

  ctx.save();
  ctx.translate(boss.x, boss.y);

  poly([[-100,-20],[-50,-48],[-25,-25],
    [-40,35],[-100,55]],"#495575","#10152b",5);

  poly([[100,-20],[50,-48],[25,-25],
    [40,35],[100,55]],"#495575","#10152b",5);

  for (const x of [-85,85]) {
    disk(x,15,21,"#233454","#10152b",4);
    ctx.save();
    ctx.shadowColor="#6deaff";
    ctx.shadowBlur=17;
    disk(x,15,12,"#62eaff");
    ctx.restore();
  }

  poly([[-55,-55],[-20,-75],[20,-75],
    [55,-55],[65,15],[40,65],
    [-40,65],[-65,15]],
    boss.flash>0?"#fff":"#a22d45","#10152b",5);

  poly([[-38,-43],[38,-43],[46,20],
    [24,48],[-24,48],[-46,20]],"#303d58");

  poly([[-33,-62],[-13,-72],[13,-72],
    [33,-62],[20,-48],[-20,-48]],"#e6b74d");

  ctx.save();
  ctx.shadowColor="#ff5366";
  ctx.shadowBlur=23;
  disk(0,0,26,"#ff5965","#10152b",5);
  disk(0,0,14,"#ffd0aa");
  disk(0,0,7,"#fff");
  ctx.restore();

  ctx.restore();

  // Boss health bar stays below the normal top HUD.
  box(W/2-190,103,380,20,"#10152b");
  box(W/2-186,107,372*(boss.hp/100),12,"#ff5366");
  words("OMEGA DRONE",W/2,97,23,"#ffe15c");
}

function drawProjectiles() {
  for (const s of shots) {
    ctx.save();
    ctx.shadowColor="#56edff";
    ctx.shadowBlur=19;
    disk(s.x,s.y,13,"rgba(66,231,255,.3)");
    disk(s.x,s.y,9,"#42e7ff","#10152b",2);
    disk(s.x,s.y,4,"#fff");
    ctx.restore();

    line(s.x-Math.sign(s.vx)*36,s.y,
      s.x-Math.sign(s.vx)*12,s.y,"#a1f9ff",5);
  }

  for (const m of missiles) {
    m.trail.forEach((p,i) => {
      ctx.save();
      ctx.globalAlpha=(i+1)/m.trail.length*.8;
      disk(p.x,p.y,2+i*.3,
        i%2?"#ff9950":"#ffe3a3");
      ctx.restore();
    });

    ctx.save();
    ctx.translate(m.x,m.y);
    ctx.rotate(m.angle);

    poly([[-13,-5],[7,-5],[15,0],
      [7,5],[-13,5]],"#d9e0e8","#10152b",2);
    poly([[-11,-5],[-17,-11],[-6,-5]],"#f04d4c");
    poly([[-11,5],[-17,11],[-6,5]],"#f04d4c");
    poly([[-14,-4],[-25,0],[-14,4]],"#ffc05e",null);

    ctx.restore();
  }

  for (const s of enemyShots) {
    ctx.save();
    ctx.shadowColor="#ff5366";
    ctx.shadowBlur=14;
    disk(s.x,s.y,8,"#ff5366","#10152b",2);
    disk(s.x,s.y,3,"#ffe5a4");
    ctx.restore();
  }
}

function drawEffects() {
  for (const p of particles) {
    ctx.save();
    ctx.globalAlpha=clamp(p.life/p.max,0,1);
    disk(p.x,p.y,p.size,p.color);
    ctx.restore();
  }

  for (const t of texts) {
    ctx.save();
    ctx.globalAlpha=clamp(t.life/.8,0,1);
    words(t.message,t.x,t.y,29,t.color);
    ctx.restore();
  }
}

function drawTarget() {
  const target = boss || drones.reduce((best,d) => {
    if (!best || dist(hero,d)<dist(hero,best)) return d;
    return best;
  },null);

  if (!target || state!=="playing") return;

  const r=target.r+12;
  ctx.save();
  ctx.strokeStyle="rgba(110,244,255,.75)";
  ctx.lineWidth=2;
  ctx.setLineDash([12,8]);
  ctx.strokeRect(target.x-r,target.y-r,r*2,r*2);
  ctx.setLineDash([]);
  ctx.restore();
}

function drawCombatHUD() {
  // Missile cooldown.
  box(16,H-72,180,47,"rgba(16,21,43,.88)","#10152b",2);
  ctx.textAlign="left";
  ctx.font="bold 13px Arial";
  ctx.fillStyle=missileTimer<=0?"#8df5ff":"#e0e7ee";
  ctx.fillText("M  MISSILE",28,H-51);

  box(28,H-42,155,7,"#46516a");
  box(28,H-42,
    155*(1-missileTimer/3.5),7,"#76eaff");

  if (bossWarning>0) {
    ctx.save();
    ctx.globalAlpha=Math.min(1,bossWarning);
    box(0,H/2-66,W,115,"rgba(24,12,35,.85)");
    words("WARNING!",W/2,H/2-14,56,"#ff626b");
    words("OMEGA DRONE INCOMING",W/2,H/2+23,28,
      "#ffe05c");
    ctx.restore();
  }
}

function overlay() {
  if (state==="playing") return;

  box(0,0,W,H,"rgba(11,16,37,.79)");

  const won=state==="won";
  words(won?"MISSION COMPLETE!":"MISSION FAILED!",
    W/2,235,72,won?"#ffe05c":"#ff7171");

  words(won?"THE CITY IS SAFE!":"ARMOR SYSTEMS OFFLINE",
    W/2,285,28,"#fff");

  box(W/2-165,321,330,57,"#ffd44c","#10152b",4);
  words("PRESS R TO RESTART",W/2,360,28,"#10152b");
}

function render(t) {
  ctx.clearRect(0,0,W,H);
  ctx.save();

  if (shake>0) {
    ctx.translate(rnd(-shake,shake),rnd(-shake,shake));
  }

  background(t);

  for (const d of drones) drawDrone(d,t);
  drawBoss();
  drawTarget();
  drawProjectiles();
  drawHero(t);
  drawEffects();

  ctx.restore();

  drawCombatHUD();
  overlay();
}

let lastTime=null;

function frame(t) {
  const dt=lastTime===null
    ? 0 : Math.min((t-lastTime)/1000,.04);

  lastTime=t;
  update(dt);
  render(t);
  requestAnimationFrame(frame);
}

window.addEventListener("keydown",event=>{
  const key=event.key.toLowerCase();

  if (["arrowup","arrowdown","arrowleft",
    "arrowright"," "].includes(key)) {
    event.preventDefault();
  }

  if (key==="r" && state!=="playing") {
    reset();
    return;
  }

  if (key==="shift" && !event.repeat) dash();
  if (key==="m" && !event.repeat) missile();

  keys.add(key);
});

window.addEventListener("keyup",event=>{
  keys.delete(event.key.toLowerCase());
});

window.addEventListener("blur",()=>keys.clear());

reset();
requestAnimationFrame(frame);

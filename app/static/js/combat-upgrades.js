
"use strict";

/*
  IRON FLIGHT — ADVANCED COMBAT SYSTEMS
  Loads AFTER game.js.
  Adds chest beam, shield, charged repulsor,
  cooldowns, and combat notifications.
*/

(() => {
  if (new URLSearchParams(location.search).get("mode") !== "combat") {
    return;
  }

  const ENERGY_MAX = 100;

  const systems = {
    energy: ENERGY_MAX,
    shield: 0,
    shieldCooldown: 0,
    beam: 0,
    beamCooldown: 0,
    beamDamageTimer: 0,
    chargeCooldown: 0,
    lastState: "playing"
  };

  const controls = new Set();
  const effects = [];
  const messages = [];

  const originalUpdate = update;
  const originalRender = render;
  const originalReset = reset;
  const originalHurt = hurt;

  const limit = (value, min, max) =>
    Math.max(min, Math.min(max, value));

  function notify(message, color = "#8beeff") {
    messages.push({
      message,
      color,
      life: 2.1
    });

    if (messages.length > 3) messages.shift();

    // JARVIS may listen for these events in a future upgrade.
    window.dispatchEvent(
      new CustomEvent("ironflight:combat", {
        detail: { message }
      })
    );
  }

  function spark(x, y, color, count = 14) {
    for (let i = 0; i < count; i++) {
      const angle = Math.random() * Math.PI * 2;
      const speed = 45 + Math.random() * 180;

      effects.push({
        x,
        y,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        color,
        life: .4,
        max: .4
      });
    }
  }

  function resetSystems() {
    systems.energy = ENERGY_MAX;
    systems.shield = 0;
    systems.shieldCooldown = 0;
    systems.beam = 0;
    systems.beamCooldown = 0;
    systems.beamDamageTimer = 0;
    systems.chargeCooldown = 0;
    systems.lastState = "playing";

    controls.clear();
    effects.length = 0;
    messages.length = 0;

    notify("Advanced combat systems online.");
  }

  // Keep the existing restart behavior.
  reset = function () {
    originalReset();
    resetSystems();
  };

  // Shield intercepts damage before the original armor system.
  hurt = function (amount) {
    if (state !== "playing") return;

    if (systems.shield > 0) {
      spark(hero.x, hero.y, "#6eeeff", 8);
      return;
    }

    originalHurt(amount);
  };

  function activateShield() {
    if (state !== "playing") return;

    if (systems.shield > 0) return;

    if (systems.shieldCooldown > 0) {
      notify("Shield generator cooling down.", "#ffcf75");
      return;
    }

    if (systems.energy < 30) {
      notify("Insufficient energy for shield.", "#ff8585");
      return;
    }

    systems.energy -= 30;
    systems.shield = 3.5;
    systems.shieldCooldown = 9;

    spark(hero.x, hero.y, "#70eaff", 28);
    notify("Energy shield activated.");
  }

  function activateBeam() {
    if (state !== "playing") return;
    if (systems.beam > 0) return;

    if (systems.beamCooldown > 0) {
      notify("Chest beam recharging.", "#ffcf75");
      return;
    }

    if (systems.energy < 40) {
      notify("Insufficient energy for chest beam.", "#ff8585");
      return;
    }

    systems.energy -= 40;
    systems.beam = 1.35;
    systems.beamCooldown = 6;
    systems.beamDamageTimer = 0;

    spark(hero.x, hero.y - 10, "#b3faff", 25);
    notify("Unibeam activated. Maximum output.");
  }

  function chargedRepulsor() {
    if (state !== "playing") return;

    if (systems.chargeCooldown > 0) {
      notify("Charged repulsor cooling down.", "#ffcf75");
      return;
    }

    if (systems.energy < 25) {
      notify("Insufficient energy for charged shot.", "#ff8585");
      return;
    }

    systems.energy -= 25;
    systems.chargeCooldown = 3.5;

    const x = hero.x + hero.face * 55;
    const y = hero.y - 12;

    // Reuse the original projectile system.
    shots.push({
      x,
      y,
      vx: hero.face * 950,
      r: 19,
      life: 1.5,
      charged: true
    });

    hero.flash = .22;
    hero.recoil = 1;

    spark(x, y, "#f5dc9b", 25);
    notify("Charged repulsor fired.");
  }

  // Charged projectiles use the original hit detection,
  // with additional damage when they hit a target.
  const originalDamageEnemy = damageEnemy;

  damageEnemy = function (target, amount) {
    originalDamageEnemy(target, amount);
  };

  function updateBeamDamage(dt) {
    if (systems.beam <= 0 || state !== "playing") return;

    systems.beamDamageTimer -= dt;
    if (systems.beamDamageTimer > 0) return;

    systems.beamDamageTimer = .12;

    const startX = hero.x + hero.face * 15;
    const beamY = hero.y - 10;
    const range = 850;

    const targets = boss ? [boss] : [...drones];

    for (const target of targets) {
      if (!target || target.hp <= 0) continue;

      const ahead =
        (target.x - startX) * hero.face;

      if (
        ahead >= 0 &&
        ahead <= range &&
        Math.abs(target.y - beamY) <= target.r + 15
      ) {
        originalDamageEnemy(
          target,
          target === boss ? 3 : 1
        );
      }
    }
  }

  function updateChargedShots() {
    for (const shot of shots) {
      if (!shot.charged || shot.bonusApplied) continue;

      // Increase projectile radius for collision detection.
      shot.r = 19;
    }
  }

  function updateSystems(dt) {
    if (state !== "playing") {
      systems.lastState = state;
      return;
    }

    systems.energy = limit(
      systems.energy + 9 * dt,
      0,
      ENERGY_MAX
    );

    systems.shield = Math.max(0, systems.shield - dt);

    systems.shieldCooldown = Math.max(
      0,
      systems.shieldCooldown - dt
    );

    systems.beam = Math.max(0, systems.beam - dt);

    systems.beamCooldown = Math.max(
      0,
      systems.beamCooldown - dt
    );

    systems.chargeCooldown = Math.max(
      0,
      systems.chargeCooldown - dt
    );

    updateBeamDamage(dt);
    updateChargedShots();
  }

  function updateVisualEffects(dt) {
    for (const effect of effects) {
      effect.x += effect.vx * dt;
      effect.y += effect.vy * dt;
      effect.life -= dt;
    }

    for (let i = effects.length - 1; i >= 0; i--) {
      if (effects[i].life <= 0) effects.splice(i, 1);
    }

    for (const message of messages) {
      message.life -= dt;
    }

    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].life <= 0) messages.splice(i, 1);
    }
  }

  // Extend the original update loop.
  update = function (dt) {
    updateSystems(dt);
    originalUpdate(dt);
    updateVisualEffects(dt);
  };

  function drawShield(t) {
    if (systems.shield <= 0) return;

    ctx.save();

    const pulse = Math.sin(t * .012) * 4;
    const radius = 103 + pulse;

    ctx.beginPath();
    ctx.arc(hero.x, hero.y, radius, 0, Math.PI * 2);

    ctx.fillStyle = "rgba(74, 219, 255, .09)";
    ctx.fill();

    ctx.strokeStyle = "#77efff";
    ctx.lineWidth = 4;
    ctx.shadowColor = "#66eaff";
    ctx.shadowBlur = 25;
    ctx.stroke();

    ctx.shadowBlur = 0;
    ctx.setLineDash([12, 12]);

    ctx.beginPath();
    ctx.arc(
      hero.x,
      hero.y,
      radius - 11,
      0,
      Math.PI * 2
    );

    ctx.strokeStyle = "rgba(190, 249, 255, .8)";
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.restore();
  }

  function drawBeam(t) {
    if (systems.beam <= 0) return;

    const x = hero.x + hero.face * 15;
    const y = hero.y - 10;
    const endX = x + hero.face * 850;

    ctx.save();

    ctx.lineCap = "round";
    ctx.shadowColor = "#54eaff";
    ctx.shadowBlur = 35;

    ctx.strokeStyle = "rgba(67, 219, 255, .3)";
    ctx.lineWidth = 45;

    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(endX, y);
    ctx.stroke();

    ctx.strokeStyle = "#5ceaff";
    ctx.lineWidth = 23;

    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(endX, y);
    ctx.stroke();

    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 9 + Math.sin(t * .05) * 2;

    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(endX, y);
    ctx.stroke();

    ctx.restore();
  }

  function drawEffects() {
    for (const effect of effects) {
      ctx.save();

      ctx.globalAlpha = limit(
        effect.life / effect.max,
        0,
        1
      );

      ctx.fillStyle = effect.color;
      ctx.shadowColor = effect.color;
      ctx.shadowBlur = 12;

      ctx.beginPath();
      ctx.arc(
        effect.x,
        effect.y,
        3,
        0,
        Math.PI * 2
      );
      ctx.fill();

      ctx.restore();
    }
  }

  function drawMeter(x, y, width, value, color) {
    ctx.fillStyle = "#243a50";
    ctx.fillRect(x, y, width, 8);

    ctx.fillStyle = color;
    ctx.fillRect(
      x,
      y,
      width * limit(value, 0, 1),
      8
    );
  }

  function drawSystemsHUD() {
    const x = W - 222;
    const y = H - 137;

    ctx.save();

    ctx.fillStyle = "rgba(7, 19, 36, .93)";
    ctx.fillRect(x, y, 205, 121);

    ctx.strokeStyle = "#4eb8d3";
    ctx.lineWidth = 1.5;
    ctx.strokeRect(x, y, 205, 121);

    ctx.textAlign = "left";
    ctx.font = "bold 13px Arial";
    ctx.fillStyle = "#92efff";
    ctx.fillText("ARC REACTOR SYSTEMS", x + 12, y + 20);

    ctx.font = "bold 11px Arial";
    ctx.fillStyle = "#eaf8ff";
    ctx.fillText(
      `ENERGY  ${Math.ceil(systems.energy)}%`,
      x + 12,
      y + 40
    );

    drawMeter(
      x + 12,
      y + 47,
      180,
      systems.energy / ENERGY_MAX,
      "#69eaff"
    );

    ctx.fillStyle = "#f4ce83";
    ctx.font = "bold 11px Arial";

    const beamText = systems.beamCooldown > 0
      ? `${systems.beamCooldown.toFixed(1)}s`
      : "READY";

    const shieldText = systems.shield > 0
      ? "ACTIVE"
      : systems.shieldCooldown > 0
        ? `${systems.shieldCooldown.toFixed(1)}s`
        : "READY";

    const chargeText = systems.chargeCooldown > 0
      ? `${systems.chargeCooldown.toFixed(1)}s`
      : "READY";

    ctx.fillText(`B  BEAM: ${beamText}`, x + 12, y + 72);
    ctx.fillText(`E  SHIELD: ${shieldText}`, x + 12, y + 90);
    ctx.fillText(`C  CHARGE: ${chargeText}`, x + 12, y + 108);

    ctx.restore();
  }

  function drawNotifications() {
    ctx.save();
    ctx.textAlign = "center";
    ctx.font = "bold 14px Arial";

    messages.forEach((entry, index) => {
      const y = 150 + index * 25;

      ctx.fillStyle = "rgba(5, 16, 30, .86)";
      ctx.fillRect(W / 2 - 260, y - 18, 520, 24);

      ctx.fillStyle = entry.color;
      ctx.fillText(entry.message, W / 2, y);
    });

    ctx.restore();
  }

  // Extend rendering without replacing existing graphics.
  render = function (t) {
    originalRender(t);

    if (state === "playing") {
      drawShield(t);
      drawBeam(t);
      drawEffects();
      drawSystemsHUD();
      drawNotifications();
    }
  };

  window.addEventListener("keydown", event => {
    const key = event.key.toLowerCase();

    if (event.repeat) return;

    if (key === "b") activateBeam();
    if (key === "e") activateShield();
    if (key === "c") chargedRepulsor();
  });

  // The original game already handles R to restart.
  // Listen for a fresh game state to reset ability systems.
  window.addEventListener("keydown", event => {
    if (
      event.key.toLowerCase() === "r" &&
      state !== "playing"
    ) {
      resetSystems();
    }
  });

  resetSystems();
})();

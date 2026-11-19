"use strict";

// Blender-rendered poses keep the 3D asset compatible with the Canvas renderer.
(() => {
  const base = new URL("../models/", document.currentScript.src);
  const runtime = new URL("wire-reference-bulk-v001/runtime/", base);
  let anchors = null;
  fetch(new URL("anchors.json", runtime))
    .then(response => response.ok ? response.json() : null)
    .then(value => { anchors = value; })
    .catch(() => {});
  const poses = {};
  for (const name of ["hover", "fire"]) {
    const image = new Image();
    image.src = new URL(`${name}.png`, runtime).href;
    poses[name] = image;
  }
  window.AurelArmor = {
    draw(ctx, hero, time, boosting = false) {
      const firing = (hero.arm || 0) > .4;
      const image = poses[firing ? "fire" : "hover"];
      if (!image.complete || !image.naturalWidth) return false;
      if (hero.inv > 0 && Math.floor(time / 75) % 2 === 0) return true;
      ctx.save();
      ctx.translate(hero.x, hero.y + Math.sin(time * .006) * 2);
      ctx.rotate(hero.tilt || 0);
      ctx.scale(hero.face, 1);
      // Sprite center matches the torso origin used by existing hitboxes.
      ctx.drawImage(image, -108, -110, 216, 216);
      ctx.shadowColor = "#6deaff";
      ctx.shadowBlur = boosting ? 24 : 12;
      const poseAnchors = anchors?.[firing ? "fire" : "hover"];
      for (const [x, y] of poseAnchors?.boots || [[-12, 87], [12, 87]]) {
        const length = (boosting ? 32 : 13) + Math.sin(time * .035 + x) * 4;
        ctx.fillStyle = "#52dfff";
        ctx.beginPath();
        ctx.moveTo(x - 4, y);
        ctx.lineTo(x + 4, y);
        ctx.lineTo(x, y + length);
        ctx.fill();
      }
      if (hero.flash > 0) {
        ctx.fillStyle = "#e9ffff";
        ctx.beginPath();
        const [palmX, palmY] = poseAnchors?.palm || [65, -25];
        ctx.arc(palmX - (hero.recoil || 0) * 6, palmY, 8, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.restore();
      return true;
    }
  };
})();

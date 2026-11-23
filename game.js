import * as THREE from 'three';
import { GLTFLoader } from '/three/GLTFLoader.js';

const status = document.querySelector('#status');
const enter = document.querySelector('#enter');
const reticle = document.querySelector('#reticle');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x829db4);
scene.fog = new THREE.FogExp2(0x829db4, 0.016);

let renderer;
try {
  renderer = new THREE.WebGLRenderer({ antialias: true });
} catch (error) {
  status.textContent = 'Could not start WebGL. Check browser hardware acceleration.';
  throw error;
}
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
document.body.append(renderer.domElement);

const camera = new THREE.PerspectiveCamera(53, 1, 0.08, 110);
function resize() {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
}
addEventListener('resize', resize);
resize();

scene.add(new THREE.HemisphereLight(0xe0f3ff, 0x666778, 2));
for (const [color, intensity, x, y, z] of [
  [0xffead2, 3.2, -8, 12, 4],
  [0xb2dfff, 1.8, 5, 6, -9],
]) {
  const light = new THREE.DirectionalLight(color, intensity);
  light.position.set(x, y, z);
  scene.add(light);
}

const ground = new THREE.Mesh(
  new THREE.PlaneGeometry(180, 180),
  new THREE.MeshStandardMaterial({ color: 0x566777, roughness: 0.95 }),
);
ground.rotation.x = -Math.PI / 2;
scene.add(ground);
const grid = new THREE.GridHelper(62, 31, 0x96aabb, 0x687e8e);
grid.position.y = 0.01;
scene.add(grid);

const obstacles = [];
const blockers = [];
const targets = [];
const targetFaces = [];
const obstacleMaterial = new THREE.MeshStandardMaterial({ color: 0x34495a });
const edgesMaterial = new THREE.LineBasicMaterial({ color: 0x849cae });
for (const [x, z, width, height, depth] of [
  [-5, 7, 3, 1.1, 2.2], [5, 10, 2.5, 1.8, 3], [-8, 17, 4, 2.8, 2],
  [8, 20, 3, 1.2, 4], [0, 23, 4.5, 1.6, 2],
]) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(width, height, depth), obstacleMaterial);
  mesh.position.set(x, height / 2, z);
  mesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(mesh.geometry), edgesMaterial));
  scene.add(mesh);
  blockers.push(mesh);
  obstacles.push(new THREE.Box3().setFromObject(mesh));
}

const standMaterial = new THREE.MeshStandardMaterial({ color: 0x283945 });
for (const [x, z, height] of [[0, 12, 1.45], [-8, 12, 1.55], [8, 15, 2], [-4, 25, 1.4], [4, 27, 2]]) {
  const stand = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.16, height, 10), standMaterial);
  stand.position.set(x, height / 2, z);
  const rim = new THREE.Mesh(new THREE.SphereGeometry(0.65, 24, 16), standMaterial);
  rim.scale.z = 0.3;
  rim.position.set(x, height, z);
  const face = new THREE.Mesh(new THREE.SphereGeometry(0.53, 24, 16),
    new THREE.MeshStandardMaterial({ color: 0xf0a548, emissive: 0xb4480b, emissiveIntensity: 0.4 }));
  face.scale.z = 0.38;
  face.position.copy(rim.position);
  face.userData.target = targets.length;
  targets.push({ face, hit: false });
  targetFaces.push(face);
  scene.add(stand, rim, face);
}

const player = new THREE.Group();
scene.add(player);
const shadow = new THREE.Mesh(new THREE.CircleGeometry(0.48, 24),
  new THREE.MeshBasicMaterial({ color: 0x13202b, transparent: true, opacity: 0.3, depthWrite: false }));
shadow.rotation.x = -Math.PI / 2;
shadow.visible = false;
scene.add(shadow);

const keys = new Set();
const movementKeys = new Set([
  'KeyW', 'KeyA', 'KeyS', 'KeyD', 'ArrowUp', 'ArrowLeft', 'ArrowDown', 'ArrowRight',
  'ShiftLeft', 'ShiftRight', 'Space', 'ControlLeft', 'ControlRight', 'KeyF',
]);
const state = { mode: 'ground', heightSpeed: 0, floor: 0, grounded: true, jump: false, flight: false };
const velocity = new THREE.Vector3();
const forward = new THREE.Vector3();
const right = new THREE.Vector3();
const move = new THREE.Vector3();
const focus = new THREE.Vector3();
const lookAt = new THREE.Vector3();
const cameraOffset = new THREE.Vector3();
const cameraGoal = new THREE.Vector3();
const shotPoint = new THREE.Vector3();
const muzzle = new THREE.Vector3();
const shotDirection = new THREE.Vector3();
const ray = new THREE.Raycaster();
const center = new THREE.Vector2();
const shotGeometry = new THREE.BufferGeometry().setAttribute('position', new THREE.BufferAttribute(new Float32Array(6), 3));
const shotMaterial = new THREE.LineBasicMaterial({ color: 0xb9f6ff, transparent: true, depthWrite: false });
const beam = new THREE.Line(shotGeometry, shotMaterial);
beam.frustumCulled = false;
beam.visible = false;
scene.add(beam);
const flash = new THREE.Mesh(new THREE.SphereGeometry(0.09, 10, 8),
  new THREE.MeshBasicMaterial({ color: 0xb9f6ff, transparent: true }));
flash.visible = false;
scene.add(flash);

const actions = new Map();
const oneShots = new Set(['Flight Takeoff', 'Landing', 'Repulsor Right']);
let mixer, palm, action, animation, shot, ready = false, locked = false;
let yaw = 0, pitch = 0.23, viewYaw = yaw, viewPitch = pitch, beamTime = 0, hits = 0;

function play(name) {
  if (animation === name) return;
  const next = actions.get(name);
  if (action) action.fadeOut(0.14);
  next.reset().setEffectiveWeight(1).fadeIn(0.14).play();
  action = next;
  animation = name;
}

function updateStatus() {
  const labels = { ground: 'Ground', takeoff: 'Taking off', flight: 'Flight', landing: 'Landing' };
  status.textContent = labels[state.mode] + '  |  Targets ' + hits + '/' + targets.length;
}

enter.addEventListener('click', async () => {
  try {
    await renderer.domElement.requestPointerLock();
  } catch {
    enter.textContent = 'Mouse capture failed. Click to retry.';
  }
});
document.addEventListener('pointerlockchange', () => {
  locked = document.pointerLockElement === renderer.domElement;
  enter.hidden = !ready || locked;
  reticle.hidden = !locked;
  keys.clear();
  state.jump = state.flight = false;
});
document.addEventListener('mousemove', (event) => {
  if (!locked) return;
  yaw -= event.movementX * 0.0025;
  pitch = THREE.MathUtils.clamp(pitch + event.movementY * 0.0025, -0.28, 0.85);
});
document.addEventListener('keydown', (event) => {
  if (!locked || !movementKeys.has(event.code)) return;
  event.preventDefault();
  keys.add(event.code);
  if (event.repeat) return;
  if (event.code === 'KeyF') state.flight = true;
  if (event.code === 'Space') state.jump = true;
});
document.addEventListener('keyup', (event) => keys.delete(event.code));
window.addEventListener('blur', () => {
  keys.clear();
  state.jump = state.flight = false;
});
document.addEventListener('mousedown', (event) => {
  if (!locked || event.button !== 0 || shot || state.mode === 'takeoff' || state.mode === 'landing') return;
  shot = { fired: false, yaw: viewYaw };
});

function setMode(mode) {
  state.mode = mode;
  updateStatus();
}

function overlaps(box, position) {
  const x = position.x - THREE.MathUtils.clamp(position.x, box.min.x, box.max.x);
  const z = position.z - THREE.MathUtils.clamp(position.z, box.min.z, box.max.z);
  return x * x + z * z < 0.36 ** 2;
}

function moveAxis(axis, dt) {
  const position = player.position;
  const previous = position[axis];
  position[axis] = THREE.MathUtils.clamp(previous + velocity[axis] * dt, -29, 29);
  if (obstacles.some(box => position.y < box.max.y - 0.015 && overlaps(box, position))) {
    position[axis] = previous;
    velocity[axis] = 0;
  }
}

function updateMovement(dt) {
  const position = player.position;
  if (state.flight) {
    if (state.mode === 'ground' || state.mode === 'landing') {
      setMode(state.grounded ? 'takeoff' : 'flight');
      state.grounded = false;
      state.heightSpeed = 0;
    } else {
      setMode('landing');
    }
  }
  state.flight = false;

  forward.set(Math.sin(viewYaw), 0, Math.cos(viewYaw));
  right.set(-forward.z, 0, forward.x);
  const along = Number(keys.has('KeyW') || keys.has('ArrowUp')) - Number(keys.has('KeyS') || keys.has('ArrowDown'));
  const across = Number(keys.has('KeyD') || keys.has('ArrowRight')) - Number(keys.has('KeyA') || keys.has('ArrowLeft'));
  const fast = keys.has('ShiftLeft') || keys.has('ShiftRight');
  const flying = state.mode === 'flight';
  const onGround = state.mode === 'ground';
  move.copy(forward).multiplyScalar(along).addScaledVector(right, across).normalize();
  const speed = flying ? (fast ? 15 : 8) : (fast ? 5.5 : 2.65);
  const response = flying ? 3.6 : 15;
  const drive = onGround || flying;
  velocity.x = THREE.MathUtils.damp(velocity.x, drive ? move.x * speed : 0, response, dt);
  velocity.z = THREE.MathUtils.damp(velocity.z, drive ? move.z * speed : 0, response, dt);
  moveAxis('x', dt);
  moveAxis('z', dt);

  if (onGround) {
    if (state.jump && state.grounded) {
      state.heightSpeed = 5.8;
      state.grounded = false;
    }
    state.heightSpeed -= 15 * dt;
  } else if (flying) {
    const vertical = Number(keys.has('Space')) - Number(keys.has('ControlLeft') || keys.has('ControlRight'));
    state.heightSpeed = THREE.MathUtils.damp(state.heightSpeed, vertical * (fast ? 7 : 4), 6, dt);
  } else if (state.mode === 'takeoff') {
    state.heightSpeed = THREE.MathUtils.damp(state.heightSpeed, 1.35, 4, dt);
  } else {
    state.heightSpeed = THREE.MathUtils.damp(state.heightSpeed, -4, 5, dt);
  }
  state.jump = false;

  const previousY = position.y;
  state.floor = 0;
  for (const box of obstacles) {
    if (previousY >= box.max.y - 0.015 && overlaps(box, position)) state.floor = Math.max(state.floor, box.max.y);
  }
  position.y = Math.min(22, previousY + state.heightSpeed * dt);
  state.grounded = position.y <= state.floor && state.heightSpeed <= 0;
  if (state.grounded) {
    position.y = state.floor;
    state.heightSpeed = 0;
    if (state.mode === 'flight') setMode('landing');
  }
  if (position.y >= 22 && state.heightSpeed > 0) state.heightSpeed = 0;

  const facing = shot ? shot.yaw : (move.lengthSq() && drive ? Math.atan2(move.x, move.z) : player.rotation.y);
  const delta = Math.atan2(Math.sin(facing - player.rotation.y), Math.cos(facing - player.rotation.y));
  player.rotation.y += delta * (1 - Math.exp(-15 * dt));

  const moving = velocity.lengthSq() > 0.12;
  if (shot) play('Repulsor Right');
  else if (state.mode === 'takeoff') play('Flight Takeoff');
  else if (state.mode === 'landing') play(state.grounded ? 'Landing' : 'Hover');
  else if (flying) play(moving ? 'Forward Flight' : 'Hover');
  else play(state.grounded && moving ? (fast ? 'Run' : 'Walk') : 'Idle');
}

function updateCamera(dt) {
  viewYaw = THREE.MathUtils.damp(viewYaw, yaw, 24, dt);
  viewPitch = THREE.MathUtils.damp(viewPitch, pitch, 24, dt);
  focus.copy(player.position).y += 1.15;
  lookAt.lerp(focus, 1 - Math.exp(-17 * dt));
  const distance = 4.7 * Math.max(1, 0.65 / camera.aspect);
  cameraOffset.set(
    -Math.sin(viewYaw) * Math.cos(viewPitch) * distance - Math.cos(viewYaw) * 0.75,
    Math.sin(viewPitch) * distance + 0.55,
    -Math.cos(viewYaw) * Math.cos(viewPitch) * distance + Math.sin(viewYaw) * 0.75,
  );
  cameraGoal.copy(lookAt).add(cameraOffset);
  cameraGoal.y = Math.max(cameraGoal.y, 0.3);
  cameraOffset.subVectors(cameraGoal, lookAt);
  ray.set(lookAt, cameraOffset.clone().normalize());
  ray.far = cameraOffset.length();
  const obstacle = ray.intersectObjects(blockers, false)[0];
  if (obstacle) cameraGoal.copy(lookAt).addScaledVector(ray.ray.direction, Math.max(0.75, obstacle.distance - 0.2));
  camera.position.copy(cameraGoal);
  focus.copy(lookAt).addScaledVector(right, 0.62);
  focus.y += THREE.MathUtils.lerp(0.85, 1.25, THREE.MathUtils.smoothstep(viewPitch, -0.28, 0.23));
  camera.lookAt(focus);
  camera.updateMatrixWorld();
}

function fire() {
  shot.fired = true;
  ray.setFromCamera(center, camera);
  ray.far = 65;
  const aim = ray.intersectObjects([ground, ...blockers, ...targetFaces], false)[0];
  if (aim) shotPoint.copy(aim.point);
  else ray.ray.at(65, shotPoint);

  palm.getWorldPosition(muzzle);
  shotDirection.subVectors(shotPoint, muzzle);
  const distance = shotDirection.length();
  ray.set(muzzle, shotDirection.normalize());
  ray.far = distance + 0.06;
  const impact = ray.intersectObjects([ground, ...blockers, ...targetFaces], false)[0];
  if (impact) {
    shotPoint.copy(impact.point);
    const target = targets[impact.object.userData.target];
    if (target && !target.hit) {
      target.hit = true;
      target.face.material.color.setHex(0x67e0be);
      target.face.material.emissive.setHex(0x149d7d);
      hits++;
      updateStatus();
    }
  }
  const positions = shotGeometry.getAttribute('position');
  positions.setXYZ(0, muzzle.x, muzzle.y, muzzle.z);
  positions.setXYZ(1, shotPoint.x, shotPoint.y, shotPoint.z);
  positions.needsUpdate = true;
  flash.position.copy(muzzle);
  beamTime = 0.14;
}

try {
  const { scene: armor, animations } = await new GLTFLoader().loadAsync('/armor.glb');
  const bounds = new THREE.Box3().setFromObject(armor, true);
  const scale = 1.84 / (bounds.max.y - bounds.min.y);
  armor.scale.setScalar(scale);
  armor.position.y = -bounds.min.y * scale;
  armor.traverse(object => {
    if (object.isSkinnedMesh) object.frustumCulled = false;
  });
  player.add(armor);
  palm = armor.getObjectByName('FX_Palm_R') ?? armor.getObjectByName('palm_flashR');
  if (!palm) throw new Error('Missing right palm attachment');
  mixer = new THREE.AnimationMixer(armor);
  for (const clip of animations) {
    const root = clip.tracks.find(track => track.name === 'root.position');
    // The controller owns altitude. Keep the baked hover bob around its baseline.
    if (root && ['Hover', 'Forward Flight', 'Flight Takeoff', 'Landing'].includes(clip.name)) {
      for (let i = 1; i < root.values.length; i += 3) {
        root.values[i] = oneShots.has(clip.name) ? 0 : root.values[i] - 0.36;
      }
    }
    const clipAction = mixer.clipAction(clip);
    if (oneShots.has(clip.name)) {
      clipAction.setLoop(THREE.LoopOnce, 1);
      clipAction.clampWhenFinished = true;
    }
    actions.set(clip.name, clipAction);
  }
  for (const name of ['Idle', 'Walk', 'Run', 'Hover', 'Forward Flight', ...oneShots]) {
    if (!actions.has(name)) throw new Error('Missing animation: ' + name);
  }
  mixer.addEventListener('finished', ({ action: ended }) => {
    if (ended !== action) return;
    if (animation === 'Flight Takeoff' && state.mode === 'takeoff') setMode('flight');
    if (animation === 'Landing' && state.mode === 'landing') setMode('ground');
    if (animation === 'Repulsor Right') shot = null;
  });
  ready = true;
  shadow.visible = true;
  enter.hidden = false;
  updateStatus();
  play('Idle');
} catch (error) {
  status.textContent = 'Could not load V004 armor: ' + error.message;
  console.error(error);
}

lookAt.set(0, 1.15, 0);
let previous = performance.now();
renderer.setAnimationLoop(now => {
  const dt = Math.min((now - previous) / 1000, 0.04);
  previous = now;
  if (ready) {
    updateMovement(dt);
    mixer.update(dt);
    player.updateMatrixWorld(true);
    shadow.position.set(player.position.x, state.floor + 0.025, player.position.z);
    shadow.material.opacity = 0.3 / (1 + player.position.y - state.floor);
  }
  updateCamera(dt);
  if (shot && !shot.fired && animation === 'Repulsor Right' && action.time >= 0.44) fire();
  beamTime = Math.max(0, beamTime - dt);
  beam.visible = flash.visible = beamTime > 0;
  shotMaterial.opacity = flash.material.opacity = beamTime / 0.14;
  renderer.render(scene, camera);
});

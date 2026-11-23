import { createServer } from 'node:http';
import { createReadStream, existsSync, statSync } from 'node:fs';

const files = {
  '/': ['index.html', 'text/html'],
  '/game.js': ['game.js', 'text/javascript'],
  '/armor.glb': ['blender/exports/iron-man-mark3-v004.glb', 'model/gltf-binary'],
  '/three/three.module.js': ['node_modules/three/build/three.module.js', 'text/javascript'],
  '/three/three.core.js': ['node_modules/three/build/three.core.js', 'text/javascript'],
  '/three/GLTFLoader.js': ['node_modules/three/examples/jsm/loaders/GLTFLoader.js', 'text/javascript'],
  '/utils/BufferGeometryUtils.js': ['node_modules/three/examples/jsm/utils/BufferGeometryUtils.js', 'text/javascript'],
  '/utils/SkeletonUtils.js': ['node_modules/three/examples/jsm/utils/SkeletonUtils.js', 'text/javascript'],
};

createServer((request, response) => {
  const route = files[request.url.split('?')[0]];
  const file = route && new URL(route[0], import.meta.url);
  if (!file || !existsSync(file)) {
    response.writeHead(404).end('File not found');
    return;
  }
  response.writeHead(200, {
    'Content-Type': route[1],
    'Content-Length': statSync(file).size,
  });
  createReadStream(file).pipe(response);
}).listen(3000, '127.0.0.1', () => console.log('Iron Flight running at http://localhost:3000'));

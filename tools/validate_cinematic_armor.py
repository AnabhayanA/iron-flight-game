"""Consolidate Blender's node clips and validate the cinematic GLB delivery."""
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'app/static/models/cinematic'

def validate():
    path = OUT / 'ironman-cinematic.glb'
    data = path.read_bytes()
    magic, version, size = struct.unpack_from('<4sII', data)
    assert magic == b'glTF' and version == 2 and size == len(data)
    length, kind = struct.unpack_from('<II', data, 12)
    gltf = json.loads(data[20:20+length])
    binary_chunks = data[20+length:]
    # Blender 5.2 emits a clip per animated node even in SCENE mode.
    # They share a timeline, so combine channels into one playable suit clip.
    clips = gltf.get('animations', [])
    assert clips
    if len(clips) > 1:
        combined = {'name': 'Hover_to_repulsor', 'samplers': [], 'channels': []}
        for clip in clips:
            offset = len(combined['samplers'])
            combined['samplers'].extend(clip['samplers'])
            for channel in clip['channels']:
                channel['sampler'] += offset
                combined['channels'].append(channel)
        gltf['animations'] = [combined]
        encoded = json.dumps(gltf, separators=(',', ':')).encode()
        encoded += b' ' * (-len(encoded) % 4)
        data = struct.pack('<4sII', b'glTF', 2, 20+len(encoded)+len(binary_chunks))
        data += struct.pack('<II', len(encoded), kind)+encoded+binary_chunks
        path.write_bytes(data)
    names = {node.get('name') for node in gltf['nodes']}
    assert {'Head', 'Shoulder_R', 'Knee_L', 'Digit_L_4_2'} <= names
    assert any(m.get('emissiveFactor') for m in gltf['materials'])
    triangles = sum(gltf['accessors'][p['indices']]['count']//3
                    for mesh in gltf['meshes'] for p in mesh['primitives'])
    report = {'bytes': len(data), 'triangles': triangles,
              'meshes': len(gltf['meshes']), 'animations': len(gltf['animations'])}
    (OUT/'glb-validation.json').write_text(json.dumps(report, indent=2))
    print(report)

if __name__ == '__main__':
    validate()

# AUREL powered armor

Original crimson ceramic and champagne alloy armor with a split brow helmet,
layered torso, cyan ion reactor, articulated rigid armor limbs, palm repulsors,
and boot thrusters. No downloaded model or texture assets are used.

- `aurel.blend`: editable Blender source, lighting, camera, and keyed poses.
- `aurel.glb`: standalone glTF 2.0 binary with metallic/roughness materials,
  emissive surfaces, named joint hierarchy, and node animation.
- `aurel-hover.png`, `aurel-fire.png`: transparent renders used by both game modes.

The game uses Canvas 2D. It displays renders of the model rather than loading
the GLB at runtime. The existing collision, movement, weapons, and mission logic
are retained. Original drawing remains the fallback while images load or fail.
The GLB is available at `/static/models/aurel.glb` for a future 3D renderer.
Emission is stored in the GLB; bloom requires renderer postprocessing.
Articulation uses rigid parented nodes, not a skinned humanoid skeleton.

Rebuild from the repository root (Blender 5.2):

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --python tools/build_armor.py
```

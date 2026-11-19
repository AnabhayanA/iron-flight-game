# Reference-informed cinematic armor

`ironman-cinematic.blend` is the editable master in meters, with an evaluated
standing height of 1.85 m. The supplied front/back image guided the gold
faceplate, triangular reactor, red torso, gold limbs, abdomen, and back panels.
This is a procedural interpretation, not an exact sculpted replica.

The suit uses separate custom lofted shells and crowned polygon panels, with
named rigid joints and individual three-segment fingers. It has coated metallic
red, champagne gold, titanium, recessed black channels, and cyan emission.
Studio area lights and procedural microfinish are included in the Blender file.

`ironman-cinematic.glb` contains evaluated geometry, PBR metallic/roughness and
emissive materials, and one scene animation transitioning from hover to an aimed
palm pose. Procedural microfinish is Blender-only; it is not baked into the GLB.
Bloom requires support in the destination renderer.

Front, back, and three-quarter PNGs are review renders. Transparent hover/fire
PNGs are supplied for later Canvas 2D integration. Existing game files and the
earlier AUREL suit have not been changed by this build.

Rebuild from the project root:

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --python tools/build_cinematic_armor.py
```

Further production work includes art refinement, baked texture maps, LODs,
collision hulls, and a skin-weighted humanoid/IK rig. The current articulation
uses parented rigid armor nodes.

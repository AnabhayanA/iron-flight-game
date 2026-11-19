"""Remove interrupted rear seam overlays from the saved helmet review."""
import bpy
from pathlib import Path
from shutil import copyfile
from mathutils import Vector

base=Path(__file__).resolve().parents[1]/'app/static/models'
source=base/'helmet-review-v004'
target=base/'helmet-review-v005'
assert not target.exists(), 'Preserve existing review revisions'
bpy.ops.wm.open_mainfile(filepath=str(source/'helmet.blend'))
target.mkdir()
for o in list(bpy.data.objects):
    if o.name.startswith('Rear crown panel line'):
        bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.context.scene.objects:
    if o.type in {'MESH','CURVE','EMPTY'}:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(target/'helmet.glb'),export_format='GLB',use_selection=True,export_apply=True,export_animations=False)
scene=bpy.context.scene
scene.camera.location=(.25,.8,.19)
scene.camera.rotation_euler=(Vector((0,0,.13))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(target/'back.png')
bpy.ops.wm.save_as_mainfile(filepath=str(target/'helmet.blend'))
bpy.ops.render.render(write_still=True)
for name in ['front.png','three-quarter.png']:
    copyfile(source/name,target/name)
print('HELMET_SEAM_REPAIR_COMPLETE',target)

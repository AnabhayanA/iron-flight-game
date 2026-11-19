"""Repair shell topology in a new body revision and verify the final geometry."""
import bpy
import math
import json
from pathlib import Path
from mathutils import Vector

P=Path(__file__).resolve().parents[1]
base=P/'app/static/models'
out=base/'mcu-body-v002'
assert not out.exists(),'Never replace a saved revision'
bpy.ops.wm.open_mainfile(filepath=str(base/'mcu-body-v001/04-complete-armor.blend'))
out.mkdir()
exec(compile((P/'tools/armor_shell_quality.py').read_text(),'armor_shell_quality','exec'))
S=bpy.context.scene
count=repair_shells(S)
root=bpy.data.objects['Armor_Root_METERS']
bpy.context.view_layer.update()
d=bpy.context.evaluated_depsgraph_get()
pts=[o.matrix_world@Vector(c) for o in S.objects if o.type=='MESH' for c in o.evaluated_get(d).bound_box]
lo=min(v.z for v in pts);hi=max(v.z for v in pts);factor=1.85/(hi-lo)
root.scale*=factor;root.location.z=(root.location.z-lo)*factor
bpy.context.view_layer.update()
d=bpy.context.evaluated_depsgraph_get()
pts=[o.matrix_world@Vector(c) for o in S.objects if o.type=='MESH' for c in o.evaluated_get(d).bound_box]
height=max(p.z for p in pts)-min(p.z for p in pts)
assert abs(height-1.85)<.0001
assert all(math.isfinite(c) for o in S.objects if o.type=='MESH' for v in o.data.vertices for c in v.co)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'mcu-armor.blend'))
bpy.ops.object.select_all(action='DESELECT')
for o in S.objects:
    if o.type in {'MESH','CURVE','EMPTY'}:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(out/'mcu-armor.glb'),export_format='GLB',use_selection=True,export_apply=True,export_animations=False)
S.cycles.samples=40;S.render.resolution_x=900;S.render.resolution_y=1100
cam=S.camera
for name,pos,target,scale in [('front',(0,-5,1.05),(0,0,.925),2.12),('back',(0,5,1.05),(0,0,.925),2.12),('three-quarter',(2.4,-5,1.5),(0,0,.925),2.12),('torso-detail',(1.3,-4,1.65),(0,0,1.31),.72)]:
    cam.location=pos;cam.data.ortho_scale=scale;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    S.render.filepath=str(out/f'{name}.png');bpy.ops.render.render(write_still=True)
(out/'validation.json').write_text(json.dumps({'height_m':height,'repaired_shells':count,'finite_geometry':True,'animation':'Rigid named joints, static export','previous_stages':'../mcu-body-v001'},indent=2))
print('FINAL_BODY_COMPLETE',out,'height',height,'repaired',count,flush=True)

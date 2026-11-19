"""Increase armor volume without stretching its height or replacing the source."""
import bpy,json,sys,runpy
from pathlib import Path
from mathutils import Vector,Matrix

PROJECT=Path(__file__).resolve().parents[1]
base=PROJECT/'app/static/models'
revision=1
while (base/f'wire-reference-bulk-v{revision:03}').exists():revision+=1
OUT=base/f'wire-reference-bulk-v{revision:03}';OUT.mkdir()
bpy.ops.wm.open_mainfile(filepath=str(base/'wire-reference-v005/reference-armor.blend'))
S=bpy.context.scene;root=bpy.data.objects['WireReference_Armor_METERS']
bpy.context.preferences.filepaths.save_version=0

def bounds(obj):
    deps=bpy.context.evaluated_depsgraph_get()
    p=[obj.matrix_world@Vector(c) for c in obj.evaluated_get(deps).bound_box]
    return [max(v[i] for v in p)-min(v[i] for v in p) for i in range(3)]

bpy.context.view_layer.update()
before=bounds(bpy.data.objects['Thorax burgundy foundation'])
for obj in list(root.children_recursive):
    if obj.type not in {'MESH','CURVE'}:continue
    parent=obj.parent.name if obj.parent else ''
    sx=sy=1
    if parent==root.name:
        sx,sy=(1.06,1.06) if obj.name.startswith('Neck') else (1.10,1.12)
    elif parent.startswith('Shoulder_'):sx,sy=1.12,1.14
    elif parent.startswith('Elbow_'):sx,sy=1.12,1.14
    elif parent.startswith('Hip_'):sx,sy=1.12,1.13
    elif parent.startswith('Knee_'):sx,sy=1.12,1.12
    if sx!=1 or sy!=1:
        obj.data=obj.data.copy()
        obj.data.transform(Matrix.Diagonal((sx,sy,1,1)))
        obj.location.x*=sx;obj.location.y*=sy
for side,sign in [('L',-1),('R',1)]:
    bpy.data.objects['Shoulder_'+side].location.x=sign*.238
    bpy.data.objects['Hip_'+side].location.x=sign*.104
    wrist=bpy.data.objects['Wrist_'+side];wrist.scale.x*=1.06;wrist.scale.y*=1.06
    ankle=bpy.data.objects['Ankle_'+side];ankle.scale.x*=1.06;ankle.scale.y*=1.04

bpy.context.view_layer.update()
after=bounds(bpy.data.objects['Thorax burgundy foundation'])
deps=bpy.context.evaluated_depsgraph_get()
points=[o.matrix_world@Vector(c) for o in root.children_recursive if o.type=='MESH' for c in o.evaluated_get(deps).bound_box]
height=max(p.z for p in points)-min(p.z for p in points)
assert abs(height-1.85)<.001,height
report={'height_m':height,'chest_before_m':before,'chest_after_m':after,
        'chest_width_increase_percent':10,'chest_depth_increase_percent':12,
        'arm_width_increase_percent':12,'thigh_width_increase_percent':12,
        'calf_width_increase_percent':12,'head_scale_changed':False}
root['bulk_revision']=json.dumps(report)
camera=S.camera;camera.location=(2.5,-5,1.5);camera.data.ortho_scale=2.10
camera.rotation_euler=(Vector((0,0,.925))-camera.location).to_track_quat('-Z','Y').to_euler()
S.render.resolution_x=1000;S.render.resolution_y=1200
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'reference-armor.blend'))
bpy.ops.object.select_all(action='DESELECT')
for o in [root]+list(root.children_recursive):o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'reference-armor.glb'),export_format='GLB',use_selection=True,export_apply=True,export_animations=False)
for name,pos in [('front',(0,-5,1.02)),('three-quarter',(2.5,-5,1.5)),('back',(0,5,1.02))]:
    camera.location=pos;camera.rotation_euler=(Vector((0,0,.925))-camera.location).to_track_quat('-Z','Y').to_euler()
    S.render.filepath=str(OUT/f'{name}.png');bpy.ops.render.render(write_still=True)
(OUT/'validation.json').write_text(json.dumps(report,indent=2))
# Reuse the tested runtime-pose pipeline and model-derived glow anchors.
sys.argv=['render_mcu_game_poses.py','--',OUT.name,'reference-armor.blend']
runpy.run_path(str(PROJECT/'tools/render_mcu_game_poses.py'),run_name='__main__')
print('BULK_ARMOR_COMPLETE',OUT,report,flush=True)

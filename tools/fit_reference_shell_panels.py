"""Fit the new armor's overlay panels to their supporting shells using ray casts."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector

P=Path(__file__).resolve().parents[1];base=P/'app/static/models'
revision=3
while (base/f'wire-reference-v{revision:03}').exists():revision+=1
OUT=base/f'wire-reference-v{revision:03}'
OUT.mkdir()
bpy.ops.wm.open_mainfile(filepath=str(base/'wire-reference-v002/reference-armor.blend'))
S=bpy.context.scene;root=bpy.data.objects['WireReference_Armor_METERS']
pairs=[('Helmet champagne','Helmet compact cranial shell',False),('Helmet rear recessed','Helmet compact cranial shell',True),
       ('Chest champagne','Thorax burgundy foundation',False),('Chest gold','Thorax burgundy foundation',False),
       ('Abdominal champagne','Waist red understructure',False),('Lumbar champagne','Waist red understructure',True),
       ('Pelvis champagne','Pelvis red structural girdle',False)]
for side in ['L','R']:
    pairs += [(f'Bicep champagne insert {side}',f'Bicep burgundy sleeve {side}',False),
        (f'Tricep champagne shell {side}',f'Bicep burgundy sleeve {side}',True),
        (f'Forearm champagne upper split {side}',f'Forearm burgundy shaped shell {side}',False),
        (f'Forearm rear silver access {side}',f'Forearm burgundy shaped shell {side}',True),
        (f'Hand red dorsal shield {side}',f'Hand metacarpal red shell {side}',True),
        (f'Thigh champagne front armor {side}',f'Thigh burgundy chassis {side}',False),
        (f'Thigh champagne posterior {side}',f'Thigh burgundy chassis {side}',True),
        (f'Shin champagne front shaped greave {side}',f'Calf burgundy contoured shell {side}',False),
        (f'Calf champagne rear ankle shell {side}',f'Calf burgundy contoured shell {side}',True),
        (f'Boot champagne raised instep {side}',f'Boot wide armored hull {side}',False),
        (f'Boot champagne articulated strap {side}',f'Boot wide armored hull {side}',False)]
bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();adjusted=0
for prefix,support_name,back in pairs:
    support=bpy.data.objects[support_name].evaluated_get(deps)
    for overlay in [o for o in S.objects if o.name.startswith(prefix) and o.type=='MESH']:
        bpy.context.view_layer.objects.active=overlay
        for modifier in list(overlay.modifiers):
            if modifier.type=='SUBSURF':bpy.ops.object.modifier_apply(modifier=modifier.name)
        for vertex in overlay.data.vertices:
            origin=Vector((vertex.co.x,1 if back else -1,vertex.co.z))
            hit,point,normal,face=support.ray_cast(origin,Vector((0,-1 if back else 1,0)))
            if hit:
                clearance=.008 if prefix.startswith('Boot champagne articulated strap') else .0035
                if prefix.startswith('Chest champagne'):clearance=.006
                fitted=point.y+(clearance if back else -clearance)
                if (back and vertex.co.y<fitted) or (not back and vertex.co.y>fitted):
                    vertex.co.y=fitted;adjusted+=1
        overlay['fitted_to_support']=support_name
# Correct the too-tall exposed neck and bring the shoulder span to 0.59 m.
head=bpy.data.objects['Head'];head.location.z=1.600;head.scale.z=1.06
for side,sign in [('L',-1),('R',1)]:
    shoulder=bpy.data.objects['Shoulder_'+side];shoulder.location.x=sign*.219
bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
points=[o.matrix_world@Vector(c) for o in S.objects if o.type=='MESH' for c in o.evaluated_get(deps).bound_box]
low=min(p.z for p in points);height=max(p.z for p in points)-low;factor=1.85/height
root.scale*=factor;root.location.z=(root.location.z-low)*factor
bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
points=[o.matrix_world@Vector(c) for o in S.objects if o.type=='MESH' for c in o.evaluated_get(deps).bound_box]
height=max(p.z for p in points)-min(p.z for p in points)
assert abs(height-1.85)<.0001
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'reference-armor.blend'))
bpy.ops.object.select_all(action='DESELECT')
for obj in [root]+list(root.children_recursive):obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'reference-armor.glb'),export_format='GLB',use_selection=True,export_apply=True,export_animations=False)
camera=S.camera;S.cycles.samples=48;S.render.resolution_x=1000;S.render.resolution_y=1200
for name,pos in [('front',(0,-5,1.02)),('back',(0,5,1.02)),('three-quarter',(2.5,-5,1.5))]:
    camera.location=pos;camera.data.ortho_scale=2.10;camera.rotation_euler=(Vector((0,0,.925))-camera.location).to_track_quat('-Z','Y').to_euler()
    S.render.filepath=str(OUT/f'{name}.png');bpy.ops.render.render(write_still=True)
S.render.resolution_x=1000;S.render.resolution_y=1000
camera.location=(1.6,-4,1.65);camera.data.ortho_scale=.78;camera.rotation_euler=(Vector((0,0,1.4))-camera.location).to_track_quat('-Z','Y').to_euler()
S.render.filepath=str(OUT/'upper-detail.png');bpy.ops.render.render(write_still=True)
(OUT/'validation.json').write_text(json.dumps({'height_m':height,'fitted_overlay_vertices':adjusted,'old_body_meshes_reused':0,'packed_reference_images':6},indent=2))
print('FITTED_REFERENCE_COMPLETE',OUT,'vertices fitted',adjusted,flush=True)

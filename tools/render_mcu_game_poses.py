"""Render runtime poses from the saved MCU armor without modifying the master."""
import bpy
import json
import sys
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

P=Path(__file__).resolve().parents[1]
arguments=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
source=P/'app/static/models'/arguments[0] if arguments else P/'app/static/models/mcu-body-v002'
out=source/'runtime'
assert not out.exists(),'Preserve existing runtime renders'
bpy.ops.wm.open_mainfile(filepath=str(source/(arguments[1] if len(arguments)>1 else 'mcu-armor.blend')))
out.mkdir()
S=bpy.context.scene
S.frame_set(1)
camera=S.camera
camera.location=(.7,-5,1.35)
camera.data.type='ORTHO';camera.data.ortho_scale=2.35
camera.rotation_euler=(Vector((0,0,.97))-camera.location).to_track_quat('-Z','Y').to_euler()
S.render.resolution_x=512;S.render.resolution_y=512;S.render.resolution_percentage=100
S.render.film_transparent=True;S.cycles.samples=40
metadata={}
for pose in ['hover','fire']:
    shoulder=bpy.data.objects['Shoulder_R'];elbow=bpy.data.objects['Elbow_R']
    shoulder.animation_data_clear();elbow.animation_data_clear()
    shoulder.rotation_euler=(.1,-1.15,0) if pose=='fire' else (0,-.12,0)
    elbow.rotation_euler=(0,-.25,0) if pose=='fire' else (0,0,0)
    bpy.context.view_layer.update()
    def project(name):
        point=world_to_camera_view(S,camera,bpy.data.objects[name].matrix_world.translation)
        return [round((point.x-.5)*216,2),round((1-point.y)*216-110,2)]
    metadata[pose]={'palm':project('Palm repulsor cyan lens R'),
                    'boots':[project('Boot flight thruster L'),project('Boot flight thruster R')]}
    S.render.filepath=str(out/f'{pose}.png');bpy.ops.render.render(write_still=True)
(out/'anchors.json').write_text(json.dumps(metadata,indent=2))
print('RUNTIME_POSES_COMPLETE',metadata)

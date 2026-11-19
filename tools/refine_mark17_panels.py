"""Correct panel coverage after inspecting the reference-rebuild render."""
import bpy,ast,math,json
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

P=Path(__file__).resolve().parents[1];base=P/'app/static/models'
out=base/'mark17-reference-v002'
assert not out.exists(),'Preserve review revisions'
out.mkdir()
bpy.ops.wm.open_mainfile(filepath=str(base/'mark17-reference-v001/mark17-armor.blend'))
S=bpy.context.scene;root=bpy.data.objects['Armor_Root_METERS']
red=bpy.data.materials['Candy apple multilayer red'];gold=bpy.data.materials['Gold champagne brushed alloy']
ti=bpy.data.materials['Dark titanium mechanisms'];gap=bpy.data.materials['Black recessed panel channels']
cyan=bpy.data.materials['Cyan ion emission'];white=bpy.data.materials['Reactor luminous core']
champagne=bpy.data.materials['Mark XVII pale champagne armor'];silver=bpy.data.materials['Mark XVII machined silver']
for script in ['build_cinematic_armor.py','build_mark17_reference.py']:
    for definition in ast.parse((P/'tools'/script).read_text()).body:
        if isinstance(definition,ast.FunctionDef):exec(compile(ast.Module(body=[definition],type_ignores=[]),'reused_panel_helpers','exec'))
exec(compile((P/'tools/armor_shell_quality.py').read_text(),'shell_quality','exec'))
remove(['XVII red thigh front inset','Forearm raised spear','XVII champagne forearm upper insert','XVII shin silver angular border'])
for side in ['L','R']:
    elbow=bpy.data.objects['Elbow_'+side];knee=bpy.data.objects['Knee_'+side];ankle=bpy.data.objects['Ankle_'+side]
    curved('XVII broad champagne forearm insert '+side,[(.025,-.17,.057,.009,0),(.035,-.15,.068,.014,0),(.041,-.08,.074,.018,0),(.033,-.033,.059,.012,0)],champagne,elbow)
    curved('XVII shin upper silver cuff '+side,[(.037,-.211,.080,.014,0),(.042,-.205,.082,.016,0),(.049,-.182,.080,.02,0),(.047,-.178,.078,.019,0)],silver,knee)
    ankle.scale.x=1.24;ankle.scale.y=1.08
    hip=bpy.data.objects['Hip_'+side]
    for s in [-1,1]:
        panel('XVII thigh perimeter gold '+side+str(s),[(s*.046,-.14),(s*.052,-.15),(s*.047,-.29),(s*.031,-.317),(s*.028,-.308),(s*.040,-.282)],-.071,.003,gold,hip,bulge=.002)
# Reuse the existing export, review-render and runtime-pose pipeline verbatim.
source=(P/'tools/build_mark17_reference.py').read_text()
exec(compile(source[source.index('# Normalize the complete'):],'mark17_export_pipeline','exec'))

"""Reconstruct supplied Mark XVII views using existing armor geometry and joints."""
import bpy, ast, math, json
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

P=Path(__file__).resolve().parents[1]
base=P/'app/static/models'
rev=1
while (base/f'mark17-reference-v{rev:03}').exists():rev+=1
out=base/f'mark17-reference-v{rev:03}';out.mkdir()
bpy.ops.wm.open_mainfile(filepath=str(base/'mcu-body-v002/mcu-armor.blend'))
S=bpy.context.scene;S.frame_set(1)
root=bpy.data.objects['Armor_Root_METERS']
red=bpy.data.materials['Candy apple multilayer red'];gold=bpy.data.materials['Gold champagne brushed alloy']
ti=bpy.data.materials['Dark titanium mechanisms'];gap=bpy.data.materials['Black recessed panel channels']
cyan=bpy.data.materials['Cyan ion emission'];white=bpy.data.materials['Reactor luminous core']
for definition in ast.parse((P/'tools/build_cinematic_armor.py').read_text()).body:
    if isinstance(definition,ast.FunctionDef):exec(compile(ast.Module(body=[definition],type_ignores=[]),'reused_mesh_helpers','exec'))
exec(compile((P/'tools/armor_shell_quality.py').read_text(),'shell_quality','exec'))
for m in bpy.data.materials:
    if m.name.startswith('Candy apple'):
        p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.21,.012,.018,1);p.inputs['Roughness'].default_value=.22
champagne=material('Mark XVII pale champagne armor',(.64,.58,.46),.88,.25)
silver=material('Mark XVII machined silver',(.32,.35,.37),.86,.31)
for m in [champagne,silver]:
    for n in m.node_tree.nodes:
        if n.type=='BUMP':n.inputs['Strength'].default_value=.045

def remove(prefixes):
    for o in list(S.objects):
        if any(o.name.startswith(n) for n in prefixes):bpy.data.objects.remove(o,do_unlink=True)

def paint(obj,mat):
    obj.data.materials.clear();obj.data.materials.append(mat)

def curved(name,rows,mat,parent=root,back=False):
    us=[-1,-.98,-.86,-.68,-.45,-.22,0,.22,.45,.68,.86,.98,1]
    verts=[]
    for w,z,y,wrap,edge in rows:
        for u in us:verts.append((u*w,(1 if back else -1)*(y-wrap*abs(u)**1.7),z+edge*abs(u)**1.4))
    n=len(us);faces=[(j*n+k,j*n+k+1,(j+1)*n+k+1,(j+1)*n+k) for j in range(len(rows)-1) for k in range(n-1)]
    o=mesh(name,verts,faces,mat,parent,2)
    mod=o.modifiers.new('Armor thickness','SOLIDIFY');mod.thickness=.003;mod.offset=-1
    mod=o.modifiers.new('Machined edge bevel','BEVEL');mod.width=.0007;mod.segments=2
    return o

def save(name):
    repair_shells(S)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/f'{name}.blend'))
    print('STAGE_SAVED',name,flush=True)

def mirror(s,pts):return [(s*x,z) for x,z in pts]

# Helmet: retain shaped cranial shell, replace V forehead with the reference's U crown.
head=bpy.data.objects['MCU_Helmet_Root']
for o in list(head.children_recursive):
    if o.type not in {'MESH','CURVE'}:continue
    if any(k in o.name for k in ['Gold','gold']):paint(o,champagne)
    if o.name.startswith('Gold forehead'):
        for v in o.data.vertices:
            z=v.co.z
            if z>.18:
                u=abs(v.co.x)/.074
                v.co.z=.197+max(0,u-.43)*.066+(z-.193)*.12
                v.co.y=-.095+.043*u**1.6
    if o.name.startswith('Temple') and o.type=='MESH':
        o.scale.y*=.83;o.scale.z*=.83
for s in [-1,1]:
    panel('XVII helmet cheek titanium cutout '+str(s),mirror(s,[(.042,.047),(.054,.086),(.071,.097),(.068,.062),(.053,.031)]),-.067,.005,gap,head,bulge=.003)
    panel('XVII helmet red cheek edge '+str(s),mirror(s,[(.049,.035),(.062,.074),(.072,.079),(.067,.045),(.058,.024)]),-.060,.006,red,head,bulge=.002)
save('01-helmet')

# Torso: burgundy foundation, champagne Y breastplate and circular reactor.
remove(['MCU reactor','MCU triangular reactor','MCU chest swept seam','MCU raised clavicle',
        'MCU neck gold insert','MCU fitted abdominal','MCU intercostal','MCU rib titanium',
        'MCU back scapula','MCU back gold','MCU back red wing','MCU dorsal','Dorsal spinal','Spinal hydraulic'])
for o in S.objects:
    if o.name.startswith('Thoracic titanium'):paint(o,red)
curved('XVII gold underlay Y breastplate',[
    (.078,1.276,.139,.021,.013),(.084,1.284,.148,.022,.012),(.090,1.36,.177,.033,.009),
    (.143,1.426,.177,.055,.015),(.187,1.474,.147,.061,.013),(.174,1.493,.135,.056,.012)],gold)
curved('XVII champagne swept Y chest',[
    (.069,1.278,.145,.017,.010),(.075,1.285,.153,.02,.011),(.079,1.36,.182,.025,.008),
    (.13,1.425,.183,.049,.014),(.177,1.474,.154,.059,.011),(.165,1.488,.141,.053,.011)],champagne)
panel('XVII collar gold bib',[(-.14,1.524),(-.071,1.549),(-.055,1.523),(.055,1.523),(.071,1.549),(.14,1.524),(.125,1.479),(.058,1.457),(0,1.475),(-.058,1.457),(-.125,1.479)],-.096,.009,gold,bulge=.008)
panel('XVII inset collar burgundy',[(-.101,1.538),(-.065,1.546),(-.052,1.523),(.052,1.523),(.065,1.546),(.101,1.538),(.091,1.507),(-.091,1.507)],-.108,.006,red,bulge=.002)
disk('XVII circular reactor black socket',(0,-.183,1.413),.049,.009,gap)
disk('XVII circular reactor silver bezel',(0,-.190,1.413),.044,.008,silver,vertices=64)
disk('XVII circular reactor cyan edge',(0,-.196,1.413),.039,.004,cyan,vertices=64)
disk('XVII circular white reactor',(0,-.199,1.413),.035,.003,white,vertices=64)
for s in [-1,1]:
    panel('XVII silver side rib frame '+str(s),mirror(s,[(.102,1.286),(.112,1.367),(.147,1.408),(.188,1.386),(.2,1.321),(.16,1.27),(.147,1.283),(.178,1.327),(.17,1.366),(.15,1.377),(.132,1.354),(.127,1.291)]),-.078,.009,silver,bulge=.003)
    panel('XVII lower lateral champagne '+str(s),mirror(s,[(.095,1.281),(.15,1.26),(.185,1.30),(.192,1.281),(.151,1.23),(.097,1.255)]),-.071,.009,champagne,bulge=.003)
    panel('XVII shoulder silver bracket '+str(s),mirror(s,[(.165,1.516),(.196,1.529),(.218,1.49),(.213,1.433),(.198,1.428),(.202,1.484),(.187,1.506)]),-.064,.008,silver,bulge=.002)
    for i in range(4):
        disk('XVII collar fastener '+str((s,i)),(s*(.172+i*.009),-.076,1.503-i*.015),.0035,.003,ti,vertices=12)
    # Back matches the supplied central champagne spine and crossed red plates.
    panel('XVII champagne back upper wing '+str(s),mirror(s,[(.014,1.49),(.07,1.543),(.16,1.528),(.19,1.49),(.12,1.442),(.036,1.39)]),.118,.012,champagne,bulge=.012)
    panel('XVII crossed dorsal red plate '+str(s),mirror(s,[(.067,1.49),(.17,1.514),(.2,1.474),(.158,1.407),(.075,1.33),(.043,1.35),(.113,1.425)]),.137,.012,red,bulge=.01)
    panel('XVII dorsal silver access '+str(s),mirror(s,[(.125,1.401),(.157,1.431),(.172,1.395),(.123,1.324),(.102,1.35)]),.126,.008,silver,bulge=.002)
    for i in range(3):
        z=1.08+i*.052
        panel('XVII lumbar side champagne '+str((s,i)),mirror(s,[(.057,z),(.12,z-.008),(.148,z+.019),(.133,z+.047),(.072,z+.034)]),.088,.007,champagne,bulge=.004)
        disk('XVII abdominal hinge '+str((s,i)),(s*.113,-.071,z+.025),.011,.005,silver)
        panel('XVII abdominal hinge linkage '+str((s,i)),mirror(s,[(.075,z+.009),(.103,z+.019),(.126,z+.028),(.124,z+.037),(.1,z+.028),(.07,z+.018)]),-.082,.004,silver,bulge=0)
curved('XVII central champagne spine',[(.024,1.296,.131,.003,0),(.03,1.307,.135,.004,0),(.041,1.411,.151,.007,.005),(.065,1.469,.155,.011,.009),(.052,1.491,.149,.008,0)],champagne,back=True)
panel('XVII red spinal inset',[(-.01,1.423),(-.012,1.544),(.012,1.544),(.01,1.423)],.16,.004,red,bulge=0)
for i in range(4):
    z=1.065+i*.048
    w=.089+i*.002
    curved('XVII champagne abdominal lamella '+str(i),[
        (w*.83,z,.116,.020,.012),(w*.92,z+.006,.123,.023,.013),
        (w,z+.043,.128,.028,.012),(w*.97,z+.047,.126,.027,.012)],champagne)
curved('XVII champagne pelvic belt',[(.109,1.005,.105,.025,.01),(.125,1.024,.108,.028,.01),(.112,1.067,.108,.023,.004),(.095,1.073,.105,.021,0)],champagne)
save('02-torso')

# Arms and hands: reference red sleeves, pale arm inserts, split forearm panels.
remove(['MCU bicep inset','MCU finger gold','MCU pauldron titanium edge'])
for s,side in [(-1,'L'),(1,'R')]:
    shoulder=bpy.data.objects['Shoulder_'+side];elbow=bpy.data.objects['Elbow_'+side];wrist=bpy.data.objects['Wrist_'+side]
    for o in shoulder.children_recursive:
        if o.type!='MESH':continue
        if any(k in o.name for k in ['gold shoulder','Gold bicep','red tricep']):paint(o,champagne)
        if 'Upper arm mechanical' in o.name:paint(o,red)
        if o.name.startswith('Finger phalanx'):paint(o,champagne)
    # Keep short champagne bicep insert within the long burgundy sleeve.
    bicep=bpy.data.objects.get('Gold bicep anatomical armor '+side)
    if bicep:
        for v in bicep.data.vertices:v.co.x*=.72;v.co.z=-.18+(v.co.z+.18)*.70
    loft('XVII burgundy upper arm sleeve '+side,[(-.274,.039,.045,0,0),(-.22,.054,.057,0,0),(-.11,.065,.067,0,0),(-.075,.05,.052,0,0)],red,shoulder,start=-1.85,end=1.85,sub=2)
    curved('XVII bicep champagne inset '+side,[(.025,-.254,.050,.008,0),(.036,-.232,.065,.013,0),(.037,-.144,.073,.014,0),(.026,-.124,.068,.009,0)],champagne,shoulder)
    for i in range(5):
        loft('XVII elbow silver flexure '+side+str(i),[(-.027-i*.009,.041,.046,0,0),(-.033-i*.009,.042,.047,0,0)],silver,elbow,sub=0)
    curved('XVII champagne forearm upper insert '+side,[(.025,-.102,.064,.013,0),(.037,-.086,.071,.018,0),(.039,-.038,.064,.018,0),(.026,-.025,.049,.010,0)],champagne,elbow)
    panel('XVII forearm diagonal champagne '+side,[(-.035,-.198),(-.028,-.15),(.035,-.203),(.028,-.232),(-.026,-.213)],-.049,.005,champagne,elbow,bulge=.003)
    for f in range(5):
        for j in range(3):
            digit=bpy.data.objects[f'Digit_{side}_{f}_{j}']
            digit.rotation_euler.x=.28 if j==0 else .6
    for f in range(4):
        panel('XVII knuckle red shield '+side+str(f),[(f*.017-.032,-.103),(f*.017-.018,-.103),(f*.017-.018,-.087),(f*.017-.032,-.087)],.025,.003,red,wrist,bulge=.002)
save('03-arms-hands')

# Legs: red chassis, champagne thigh plates, gold borders, pale shin and boot shells.
remove(['MCU shin central ridge','MCU calf overlapping band','MCU thigh red hip flange'])
for s,side in [(-1,'L'),(1,'R')]:
    hip=bpy.data.objects['Hip_'+side];knee=bpy.data.objects['Knee_'+side];ankle=bpy.data.objects['Ankle_'+side]
    for o in hip.children_recursive:
        if o.type!='MESH':continue
        if any(k in o.name for k in ['Thigh gold main','Rear thigh gold','MCU armored boot instep']):paint(o,champagne)
        if 'Gold articulated patella' in o.name:paint(o,red)
        if o.name.startswith('Thigh mechanical'):paint(o,red)
    for i,(z,w) in enumerate([(-.29,.059),(-.345,.052)]):
        panel('XVII thigh gold lower border '+side+str(i),[(-w,z+.016),(-w*.7,z-.014),(0,z-.025),(w*.7,z-.014),(w,z+.016),(w*.79,z+.008),(0,z-.012),(-w*.79,z+.008)],-.074,.004,gold,hip,bulge=.003)
        panel('XVII thigh stepped champagne '+side+str(i),[(-w,z),(-w*.72,z-.026),(0,z-.036),(w*.72,z-.026),(w,z),(w*.8,z-.008),(0,z-.025),(-w*.8,z-.008)],-.076,.004,champagne,hip,bulge=.003)
    curved('XVII red thigh front inset '+side,[(.022,-.32,.077,.004,0),(.027,-.307,.080,.005,0),(.031,-.103,.097,.008,0),(.024,-.074,.092,.005,0)],red,hip)
    curved('XVII champagne shin front greave '+side,[(.033,-.427,.053,.008,0),(.039,-.41,.058,.011,0),(.044,-.25,.077,.015,0),(.045,-.205,.079,.017,0),(.038,-.19,.077,.013,0)],champagne,knee)
    for i in range(3):
        panel('XVII shin silver angular border '+side+str(i),[(-.047,-.17-i*.011),(-.028,-.19-i*.011),(.028,-.19-i*.011),(.047,-.17-i*.011),(.046,-.176-i*.011),(.027,-.198-i*.011),(-.027,-.198-i*.011),(-.046,-.176-i*.011)],-.073,.003,silver,knee,bulge=0)
    curved('XVII champagne calf lower cuff '+side,[(.031,-.427,.051,.01,0),(.037,-.41,.062,.012,0),(.043,-.352,.075,.017,0),(.04,-.34,.071,.014,0)],champagne,knee,back=True)
    curved('XVII boot champagne toe '+side,[(.039,-.093,.143,.01,0),(.043,-.080,.147,.012,0),(.041,-.05,.123,.012,0),(.033,-.027,.083,.009,0)],champagne,ankle)
    ankle.scale.x=1.10
save('04-full-armor')

# Normalize the complete evaluated assembly to 1.85 meters and save before rendering.
root.animation_data_clear();bpy.context.view_layer.update()
d=bpy.context.evaluated_depsgraph_get()
pts=[o.matrix_world@Vector(c) for o in S.objects if o.type=='MESH' for c in o.evaluated_get(d).bound_box]
low=min(p.z for p in pts);factor=1.85/(max(p.z for p in pts)-low)
root.scale*=factor;root.location.z=(root.location.z-low)*factor
root['reference_design']='User supplied Mark XVII front, back, closeups and wireframes'
save('mark17-armor')
bpy.ops.object.select_all(action='DESELECT')
for o in S.objects:
    if o.type in {'MESH','CURVE','EMPTY'}:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(out/'mark17-armor.glb'),export_format='GLB',use_selection=True,export_apply=True,export_animations=False)
S.render.engine='CYCLES';S.cycles.samples=40;S.cycles.use_denoising=True;S.render.film_transparent=True
S.render.resolution_x=900;S.render.resolution_y=1100;S.render.resolution_percentage=100
camera=S.camera
def view(name,pos,target,scale):
    camera.location=pos;camera.data.type='ORTHO';camera.data.ortho_scale=scale
    camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    S.render.filepath=str(out/f'{name}.png');bpy.ops.render.render(write_still=True)
for name,pos in [('front',(0,-5,1.05)),('back',(0,5,1.05)),('three-quarter',(2.4,-5,1.5))]:view(name,pos,(0,0,.925),2.12)
runtime=out/'runtime';runtime.mkdir()
S.render.resolution_x=512;S.render.resolution_y=512
metadata={}
for pose in ['hover','fire']:
    shoulder=bpy.data.objects['Shoulder_R'];elbow=bpy.data.objects['Elbow_R']
    shoulder.animation_data_clear();elbow.animation_data_clear()
    shoulder.rotation_euler=(.1,-1.15,0) if pose=='fire' else (0,-.12,0)
    elbow.rotation_euler=(0,-.25,0) if pose=='fire' else (0,0,0)
    if pose=='fire':
        for f in range(5):
            for j in range(3):bpy.data.objects[f'Digit_R_{f}_{j}'].rotation_euler.x=-.08
    camera.location=(.7,-5,1.35);camera.data.ortho_scale=2.35
    camera.rotation_euler=(Vector((0,0,.97))-camera.location).to_track_quat('-Z','Y').to_euler()
    bpy.context.view_layer.update()
    def project(name):
        pt=world_to_camera_view(S,camera,bpy.data.objects[name].matrix_world.translation)
        return [round((pt.x-.5)*216,2),round((1-pt.y)*216-110,2)]
    metadata[pose]={'palm':project('Palm repulsor cyan lens R'),'boots':[project('Boot flight thruster L'),project('Boot flight thruster R')]}
    S.render.filepath=str(runtime/f'{pose}.png');bpy.ops.render.render(write_still=True)
(runtime/'anchors.json').write_text(json.dumps(metadata,indent=2))
(out/'validation.json').write_text(json.dumps({'height_m':1.85,'reference':'Supplied Mark XVII images','source_mesh':'Reconstructed, not the artist original','stages_saved':5},indent=2))
print('MARK17_REFERENCE_COMPLETE',out,flush=True)

"""Refine the existing armor sequentially; preserve source files and stage saves."""
import bpy
import ast
import math
import json
from pathlib import Path
from mathutils import Vector

P=Path(__file__).resolve().parents[1]
base=P/'app/static/models'
revision=1
while (base/f'mcu-body-v{revision:03}').exists():revision+=1
out=base/f'mcu-body-v{revision:03}'
out.mkdir()
bpy.ops.wm.open_mainfile(filepath=str(base/'cinematic/ironman-cinematic.blend'))
S=bpy.context.scene
S.frame_set(1)
root=bpy.data.objects['Armor_Root_METERS']
red=bpy.data.materials['Candy apple multilayer red']
gold=bpy.data.materials['Gold champagne brushed alloy']
ti=bpy.data.materials['Dark titanium mechanisms']
gap=bpy.data.materials['Black recessed panel channels']
cyan=bpy.data.materials['Cyan ion emission']
white=bpy.data.materials['Reactor luminous core']
tree=ast.parse((P/'tools/build_cinematic_armor.py').read_text())
for definition in tree.body:
    if isinstance(definition,ast.FunctionDef):
        exec(compile(ast.Module(body=[definition],type_ignores=[]),'reused_armor_helpers','exec'))
bpy.context.preferences.filepaths.save_version=0
exec(compile((P/'tools/armor_shell_quality.py').read_text(),'armor_shell_quality','exec'))

def remove_prefixes(prefixes):
    for o in list(S.objects):
        if any(o.name.startswith(p) for p in prefixes):bpy.data.objects.remove(o,do_unlink=True)

def surface(name,rows,mat,parent=root,side=-1):
    """Curved quad shell with controlled edge wrap and a closed thickness."""
    us=[-1,-.97,-.85,-.65,-.4,-.18,0,.18,.4,.65,.85,.97,1]
    vs=[]
    for width,z,depth,wrap,drop in rows:
        for u in us:vs.append((u*width,side*(depth-wrap*abs(u)**1.7),z+drop*abs(u)**1.5))
    n=len(us)
    fs=[(j*n+i,j*n+i+1,(j+1)*n+i+1,(j+1)*n+i) for j in range(len(rows)-1) for i in range(n-1)]
    o=mesh(name,vs,fs,mat,parent,2)
    mod=o.modifiers.new('Shell thickness','SOLIDIFY');mod.thickness=.003
    mod=o.modifiers.new('Soft machined edges','BEVEL');mod.width=.0008;mod.segments=2
    return o

def stage(name):
    repair_shells(S)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/f'{name}.blend'))
    print('STAGE_SAVED',name,flush=True)

def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
S.render.engine='CYCLES';S.cycles.samples=40;S.cycles.use_denoising=True
S.render.film_transparent=True
S.render.resolution_percentage=100
camera=S.camera
def render(name,target,scale,pos,res=(800,900)):
    camera.location=pos;camera.data.ortho_scale=scale;aim(camera,target)
    S.render.resolution_x,S.render.resolution_y=res
    S.render.filepath=str(out/f'{name}.png')
    bpy.ops.render.render(write_still=True)

# Stage 1: continuous sculpted chest, nested reactor and closely seated abdomen.
remove_prefixes(['Sculpted pectoral','Clavicle gold accent','Oblique interlocking rib',
    'Central sculpted sternum','Triangular reactor','Reactor machined','Reactor cyan',
    'Reactor triangular','Abdominal overlapping','Back scapular','Back swept wing',
    'Back gold rail','Scapula vent','Integrated back thruster','Back ion nozzle'])
surface('MCU swept continuous breastplate',[
    (.105,1.285,.115,.029,.025),(.114,1.291,.128,.032,.028),
    (.155,1.33,.153,.051,.021),(.192,1.39,.165,.075,.002),
    (.207,1.448,.157,.076,-.014),(.195,1.49,.128,.060,-.015),
    (.15,1.516,.101,.040,-.006),(.145,1.518,.100,.039,-.006)],red)
for s in [-1,1]:
    def mir(points):return [(s*x,z) for x,z in points]
    panel('MCU raised clavicle '+str(s),mir([(.018,1.49),(.055,1.537),(.137,1.545),(.19,1.514),(.173,1.503),(.13,1.525),(.063,1.52),(.036,1.489)]),-.077,.009,red,bulge=.007)
    panel('MCU neck gold insert '+str(s),mir([(.037,1.535),(.05,1.55),(.121,1.559),(.151,1.541),(.12,1.544),(.055,1.541)]),-.059,.006,gold,bulge=.002)
    for i in range(5):
        z=1.10+i*.042
        # Separate, overlapping side lamellae follow the tapered rib cage.
        panel('MCU intercostal red lamella '+str((s,i)),mir([(.102,z),(.133,z+.018),(.164,z+.062),(.148,z+.068),(.121,z+.031),(.099,z+.022)]),-.058,.015,red,bulge=.004)
        tube('MCU rib titanium separator '+str((s,i)),[(s*.129,-.065,z+.022),(s*.15,-.063,z+.055)],.0018,ti)
    tube('MCU chest swept seam '+str(s),[(s*.066,-.13,1.314),(s*.145,-.119,1.344),(s*.185,-.103,1.4)],.0011,gap)
    panel('MCU back scapula '+str(s),mir([(.012,1.50),(.05,1.544),(.125,1.549),(.185,1.516),(.197,1.463),(.13,1.437),(.03,1.46)]),.103,.024,red,bulge=.023)
    panel('MCU back gold Y rail '+str(s),mir([(.014,1.445),(.133,1.438),(.185,1.474),(.166,1.425),(.056,1.395),(.027,1.337),(.012,1.343)]),.12,.012,gold,bulge=.008)
    panel('MCU back red wing '+str(s),mir([(.065,1.40),(.18,1.43),(.177,1.348),(.135,1.265),(.054,1.207),(.042,1.245),(.085,1.332)]),.118,.019,red,bulge=.015)
    for i in range(4):
        panel('MCU dorsal exhaust louver '+str((s,i)),mir([(.101+i*.013,1.36),(.107+i*.013,1.36),(.125+i*.01,1.394),(.119+i*.01,1.394)]),.143,.004,ti,bulge=0)
    disk('MCU recessed dorsal thruster '+str(s),(s*.15,.132,1.407),.018,.006,gap)
    disk('MCU dorsal ion emitter '+str(s),(s*.15,.137,1.407),.011,.003,cyan)

tri=[(-.044,1.413),(-.035,1.421),(.035,1.421),(.044,1.413),(.009,1.335),(0,1.33),(-.009,1.335)]
for scale,y,mat,name in [(1.13,-.163,gap,'MCU reactor recessed seat'),(1,-.169,ti,'MCU reactor titanium bezel'),(.88,-.174,gold,'MCU reactor champagne rim'),(.78,-.179,cyan,'MCU triangular reactor glass'),(.52,-.183,white,'MCU triangular reactor core')]:
    panel(name,[(x*scale,1.383+(z-1.383)*scale) for x,z in tri],y,.004,mat,bulge=0)
for s in [-1,1]:
    tube('MCU reactor lattice '+str(s),[(s*.027,-.184,1.407),(0,-.184,1.346),(-s*.027,-.184,1.407)],.0009,ti)
tube('MCU reactor crossbar',[(-.026,-.185,1.391),(.026,-.185,1.391)],.0009,ti)
for i in range(5):
    z=1.055+i*.043
    w=.097+i*.004
    surface('MCU fitted abdominal segment '+str(i),[
        (w*.81,z,.095+i*.003,.018,.014),
        (w*.88,z+.005,.105+i*.003,.021,.014),
        (w,z+.037,.108+i*.003,.024,.008),
        (w,z+.04,.106+i*.003,.023,.008)],red)
stage('01-torso')
render('01-torso-review',(0,0,1.31),.72,(1.3,-4,1.65))

# Stage 2: retain articulated limbs; replace blunt caps and add mechanical shells.
remove_prefixes(['Shoulder gold contoured cap','Pauldron red crown'])
for s,side in [(-1,'L'),(1,'R')]:
    shoulder=bpy.data.objects['Shoulder_'+side]
    elbow=bpy.data.objects['Elbow_'+side]
    wrist=bpy.data.objects['Wrist_'+side]
    loft('MCU gold shoulder swept shell '+side,[(-.075,.065,.075,0,0),(-.04,.081,.088,0,0),(.025,.078,.088,0,0),(.064,.049,.058,0,0),(.07,.02,.028,0,0)],gold,shoulder,start=-1.7,end=1.7,steps=32,sub=2)
    loft('MCU pauldron titanium edge '+side,[(-.082,.066,.077,0,0),(-.072,.069,.080,0,0)],ti,shoulder,start=-1.72,end=1.72,steps=32,sub=1)
    loft('MCU red upper shoulder cap '+side,[(.012,.081,.091,0,0),(.04,.067,.078,0,0),(.074,.023,.032,0,0)],red,shoulder,start=1.55,end=4.73,steps=28,sub=2)
    panel('MCU bicep inset channel '+side,[(-.019,-.108),(-.011,-.098),(.008,-.173),(.017,-.206),(.006,-.233),(-.006,-.206)],-.068,.003,ti,shoulder,bulge=0)
    surface('MCU red tricep armor '+side,[(.036,-.258,.047,.012,0),(.052,-.20,.060,.016,0),(.053,-.12,.062,.017,0),(.035,-.09,.048,.012,0)],red,shoulder,side=1)
    surface('MCU rear forearm access panel '+side,[(.029,-.22,.042,.008,0),(.038,-.18,.052,.01,0),(.046,-.08,.062,.014,0),(.036,-.055,.05,.009,0)],red,elbow,side=1)
    for i in range(4):
        panel('MCU wrist overlapping shell '+side+str(i),[(-.025,-.022-i*.012),(-.029,-.012-i*.012),(.029,-.012-i*.012),(.025,-.022-i*.012)],.029,.004,red,wrist,bulge=.002)
    for f in range(5):
        for j in range(3):
            digit=bpy.data.objects[f'Digit_{side}_{f}_{j}']
            panel('MCU finger gold knuckle '+str((side,f,j)),[(-.005,-.003),(-.006,-.009),(.006,-.009),(.005,-.003)],.009,.002,gold,digit,bulge=0)
stage('02-arms-hands')
render('02-arm-review',(.23,0,1.22),.85,(1.2,-4,1.4))

# Stage 3: preserve hip/knee/ankle pivots and replace narrow greaves with shaped shells.
remove_prefixes(['Red sculpted shin greave','Rear calf armored thruster cowling','Shin panel channel'])
for s,side in [(-1,'L'),(1,'R')]:
    hip=bpy.data.objects['Hip_'+side];knee=bpy.data.objects['Knee_'+side];ankle=bpy.data.objects['Ankle_'+side]
    loft('MCU flared red shin carapace '+side,[(-.428,.036,.044,0,0),(-.38,.043,.055,0,0),(-.24,.055,.068,0,.005),(-.12,.068,.076,0,0),(-.055,.059,.064,0,0),(-.035,.042,.045,0,0)],red,knee,start=-1.8,end=1.8,steps=36,sub=2)
    loft('MCU red calf curved armor '+side,[(-.405,.038,.047,0,0),(-.29,.048,.068,0,.008),(-.15,.068,.085,0,.011),(-.07,.051,.06,0,0)],red,knee,start=1.84,end=4.44,steps=32,sub=2)
    surface('MCU shin central ridge '+side,[(.011,-.397,.053,.002,0),(.014,-.33,.063,.003,0),(.022,-.17,.077,.004,0),(.023,-.12,.081,.005,0)],red,knee)
    for i in range(2):
        z=-.12-i*.11
        panel('MCU calf overlapping band '+side+str(i),[(-.04,z),(-.045,z+.016),(.045,z+.016),(.04,z)],.077,.004,red,knee,bulge=.002)
    for i in range(4):
        disk('MCU knee side fastener '+side+str(i),(s*.058,.02*math.sin(i*math.pi/2),.02*math.cos(i*math.pi/2)),.003,.003,gold,knee,'X',12)
    panel('MCU thigh red hip flange '+side,[(-.058,-.04),(-.037,.005),(.04,.008),(.066,-.05),(.053,-.136),(.033,-.11),(.019,-.038)],-.058,.009,red,hip,bulge=.009)
    surface('MCU armored boot instep '+side,[(.030,-.085,.136,.005,0),(.037,-.065,.128,.01,0),(.036,-.025,.076,.008,0),(.028,.012,.045,.006,0)],red,ankle)
stage('03-legs-boots')
render('03-leg-review',(0,0,.49),1.05,(1,-4,.7))

# Stage 4: bring in the separately reviewed helmet, retaining all its meshes/materials.
old=bpy.data.objects.get('Head')
if old:
    for o in list(old.children_recursive)+[old]:bpy.data.objects.remove(o,do_unlink=True)
with bpy.data.libraries.load(str(base/'helmet-review-v005/helmet.blend'),link=False) as (src,dst):
    dst.objects=[name for name in src.objects if name not in ['Key','Fill','Rim','Helmet review camera']]
for o in dst.objects:
    if o is not None:S.collection.objects.link(o)
helmet=next(o for o in dst.objects if o and o.name.startswith('Helmet_Root_METERS'))
helmet.parent=root;helmet.location=(0,0,1.58)
helmet.name='MCU_Helmet_Root'
root.animation_data_clear()
bpy.context.view_layer.update()
d=bpy.context.evaluated_depsgraph_get()
points=[o.matrix_world@Vector(c) for o in S.objects if o.type=='MESH' for c in o.evaluated_get(d).bound_box]
lo=min(v.z for v in points);hi=max(v.z for v in points);factor=1.85/(hi-lo)
root.scale*=factor;root.location.z=(root.location.z-lo)*factor
root['height_m']=1.85
stage('04-complete-armor')
bpy.ops.object.select_all(action='DESELECT')
for o in S.objects:
    if o.type in {'MESH','CURVE','EMPTY'}:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(out/'mcu-armor.glb'),export_format='GLB',use_selection=True,export_apply=True,export_animations=False)
render('front',(0,0,.925),2.12,(0,-5,1.05),(900,1100))
render('back',(0,0,.925),2.12,(0,5,1.05),(900,1100))
render('three-quarter',(0,0,.925),2.12,(2.4,-5,1.5),(900,1100))
(out/'validation.json').write_text(json.dumps({'height_m':1.85,'stage_saves':4,'geometry':'Rigid articulated custom armor panels','reference':'User supplied MCU front/back image; interpreted model'},indent=2))
print('MCU_BODY_REFINEMENT_COMPLETE',out,flush=True)

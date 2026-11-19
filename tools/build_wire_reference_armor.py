"""Fresh armor geometry from the six supplied wireframe views; no old body meshes."""
import bpy, ast, math, json
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

PROJECT=Path(__file__).resolve().parents[1]
revision=1
while (PROJECT/f'app/static/models/wire-reference-v{revision:03}').exists():revision+=1
OUT=PROJECT/f'app/static/models/wire-reference-v{revision:03}'
OUT.mkdir()
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
S=bpy.context.scene;S.unit_settings.system='METRIC';S.unit_settings.scale_length=1
bpy.context.preferences.filepaths.save_version=0
root=None
# Reuse only material creation and mesh plumbing, never prior geometry.
definitions=ast.parse((PROJECT/'tools/build_cinematic_armor.py').read_text()).body
for definition in definitions:
    if isinstance(definition,ast.FunctionDef) and definition.name in {'material','joint'}:
        exec(compile(ast.Module(body=[definition],type_ignores=[]),'reused_helpers','exec'))
root=joint('WireReference_Armor_METERS',(0,0,0))
for definition in definitions:
    if isinstance(definition,ast.FunctionDef) and definition.name=='mesh':
        exec(compile(ast.Module(body=[definition],type_ignores=[]),'reused_mesh_helper','exec'))
red=material('Reference burgundy lacquer',(.19,.009,.014),.82,.24)
cream=material('Reference satin champagne',(.58,.52,.41),.87,.28)
gold=material('Reference gold inset trim',(.44,.26,.055),.88,.28)
silver=material('Reference machined silver',(.26,.29,.31),.85,.30)
dark=material('Reference recessed titanium',(.028,.034,.04),.7,.39)
black=material('Reference panel recess',(.008,.009,.012),.25,.5)
cyan=material('Reference pale cyan light',(.4,.85,1),.1,.2,4)
white=material('Reference reactor core',(.82,.96,1),.1,.15,6)

def section(name,rows,mat,parent=root,segments=24,power=.66,bevel=.0015):
    # Anatomical cross-sections with broad flat faces and rounded chamfers.
    verts=[]
    for z,rx,ry,cx,cy in rows:
        for i in range(segments):
            a=i*math.tau/segments
            sx,sy=math.sin(a),math.cos(a)
            verts.append((cx+rx*math.copysign(abs(sx)**power,sx),cy-ry*math.copysign(abs(sy)**power,sy),z))
    faces=[(j*segments+i,j*segments+(i+1)%segments,(j+1)*segments+(i+1)%segments,(j+1)*segments+i)
        for j in range(len(rows)-1) for i in range(segments)]
    faces += [tuple(range(segments-1,-1,-1)),tuple((len(rows)-1)*segments+i for i in range(segments))]
    o=mesh(name,verts,faces,mat,parent,0,bevel)
    for p in o.data.polygons:
        p.use_smooth=len(p.vertices)==4
    weighted=o.modifiers.new('Controlled metal normals','WEIGHTED_NORMAL');weighted.keep_sharp=True
    return o

def plate(name,points,y,mat,parent=root,depth=.004,bevel=.002,curve=0):
    # Tessellated outline allows the angular cutouts visible in the reference.
    flat=[Vector((x,0,z)) for x,z in points]
    tris=tessellate_polygon([flat]);n=len(points)
    verts=[(x,y+curve*x*x,z) for x,z in points]+[(x,y+depth+curve*x*x,z) for x,z in points]
    indices={tuple(v):i for i,v in enumerate(flat)}
    faces=[tuple(v if isinstance(v,int) else indices[tuple(v)] for v in tri) for tri in tris]
    faces += [tuple(n+i for i in reversed(f)) for f in faces.copy()]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    o=mesh(name,verts,faces,mat,parent,0,bevel)
    for p in o.data.polygons:p.use_smooth=False
    mod=o.modifiers.new('Panel normals','WEIGHTED_NORMAL');mod.keep_sharp=True
    return o

def patch(name,rows,mat,parent=root,back=False):
    # Quad sheet with tightly spaced support rows for clean armor-panel edges.
    us=[-1,-.98,-.86,-.67,-.44,-.22,0,.22,.44,.67,.86,.98,1]
    verts=[]
    for z,w,depth,wrap,edge,cx in rows:
        for u in us:verts.append((cx+u*w,(1 if back else -1)*(depth-wrap*abs(u)**1.6),z+edge*abs(u)**1.4))
    n=len(us);faces=[(j*n+k,j*n+k+1,(j+1)*n+k+1,(j+1)*n+k) for j in range(len(rows)-1) for k in range(n-1)]
    o=mesh(name,verts,faces,mat,parent,2)
    mod=o.modifiers.new('Physical shell thickness','SOLIDIFY');mod.thickness=.003;mod.offset=-1
    mod=o.modifiers.new('Machined border','BEVEL');mod.width=.0006;mod.segments=2
    return o

def cylinder(name,point,radius,length,mat,parent=root,axis='Y',vertices=32):
    o=section(name,[(-length/2,radius*.96,radius*.96,0,0),(-length*.3,radius,radius,0,0),
                   (length*.3,radius,radius,0,0),(length/2,radius*.96,radius*.96,0,0)],mat,parent,vertices,1,.0005)
    o.location=point
    if axis=='Y':o.rotation_euler.x=math.pi/2
    elif axis=='X':o.rotation_euler.y=math.pi/2
    return o

def line(name,points,mat,r=.001,parent=root):
    curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.bevel_depth=r;curve.bevel_resolution=2
    p=curve.splines.new('POLY');p.points.add(len(points)-1)
    for v,co in zip(p.points,points):v.co=(*co,1)
    o=bpy.data.objects.new(name,curve);S.collection.objects.link(o);o.parent=parent;o.data.materials.append(mat)
    return o

def mirrored(sign,points):return [(sign*x,z) for x,z in points]
def save(stage):
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/f'{stage}.blend'))
    print('SAVED_STAGE',stage,flush=True)

# Measurements chosen from the full-body color reference and wireframe landmarks.
landmarks={'height':1.85,'helmet_bottom':1.615,'shoulder':1.485,'elbow':1.175,
           'wrist':.915,'pelvis':1.015,'knee':.555,'ankle':.115,'shoulder_width':.58}
root['landmarks_m']=json.dumps(landmarks)

# Stage 1. Helmet: compact head, inset U-shaped crown, cheek cutouts and rear banding.
head=joint('Head',(0,0,1.615),root)
section('Helmet compact cranial shell',[(0,.043,.058,0,.003),(.025,.061,.077,0,.005),(.072,.078,.091,0,.008),
    (.133,.084,.095,0,.009),(.185,.081,.087,0,.012),(.216,.058,.063,0,.014),(.233,.021,.024,0,.014),(.235,.002,.003,0,.014)],red,head,40,.85,.002)
patch('Helmet champagne upper brow',[(.117,.068,.105,.027,0,0),(.12,.07,.106,.027,0,0),
    (.153,.073,.107,.032,0,0),(.185,.071,.096,.041,.005,0),(.195,.068,.09,.040,.023,0),(.197,.067,.089,.039,.023,0)],cream,head)
patch('Helmet champagne lower face',[(.025,.033,.087,.009,0,0),(.028,.035,.09,.01,0,0),(.059,.05,.104,.018,.001,0),
    (.086,.062,.109,.025,.003,0),(.108,.068,.107,.027,0,0),(.111,.067,.105,.026,0,0)],cream,head)
for s in [-1,1]:
    plate('Helmet optical black socket '+str(s),mirrored(s,[(.011,.114),(.062,.118),(.066,.113),(.014,.108)]),-.109,black,head,depth=.003,bevel=.0007,curve=5)
    plate('Helmet cyan eye '+str(s),mirrored(s,[(.014,.114),(.059,.117),(.06,.113),(.016,.111)]),-.112,cyan,head,depth=.001,bevel=.0003,curve=5)
    plate('Helmet jaw black cutout '+str(s),mirrored(s,[(.041,.036),(.045,.064),(.065,.088),(.072,.072),(.061,.028)]),-.064,black,head,curve=1)
    plate('Helmet mandible red frame '+str(s),mirrored(s,[(.049,.022),(.064,.039),(.075,.078),(.079,.063),(.067,.024),(.055,.012)]),-.055,red,head,bevel=.0015)
    plate('Helmet angular temple '+str(s),mirrored(s,[(.076,.088),(.088,.105),(.085,.137),(.073,.152),(.067,.13)]),-.003,red,head,depth=.032,bevel=.002)
plate('Helmet chin frame',[(-.038,.025),(-.031,.007),(0,0),(.031,.007),(.038,.025),(.027,.032),(-.027,.032)],-.081,cream,head,depth=.005)
for z in [.067,.109]:
    patch('Helmet rear recessed band '+str(z),[(z,.065,.087,.016,0,0),(z+.003,.067,.088,.017,0,0),
        (z+.015,.072,.091,.018,0,0),(z+.018,.071,.09,.018,0,0)],red,head,back=True)
section('Neck compact titanium seal',[(1.55,.048,.047,0,0),(1.615,.047,.047,0,0)],dark,root,24,.9)
for z in [1.565,1.583,1.601]:
    section('Neck interlocking collar '+str(z),[(z,.052,.051,0,0),(z+.012,.052,.051,0,0)],red)
save('01-helmet')

# Stage 2. Torso: broad, short thorax; the Y panel wraps around side cutouts.
section('Thorax burgundy foundation',[(1.255,.126,.086,0,0),(1.31,.165,.103,0,0),(1.4,.197,.113,0,0),
    (1.475,.205,.105,0,0),(1.525,.144,.074,0,0)],red,segments=32,power=.78)
patch('Chest gold border Y',[(1.272,.089,.127,.02,.014,0),(1.279,.091,.132,.022,.015,0),
    (1.36,.085,.158,.025,.018,0),(1.422,.155,.161,.053,.024,0),(1.46,.184,.143,.058,.033,0),(1.464,.181,.14,.056,.034,0)],gold)
patch('Chest champagne Y face',[(1.277,.079,.134,.016,.013,0),(1.284,.082,.138,.018,.014,0),
    (1.361,.076,.164,.02,.016,0),(1.423,.146,.167,.049,.023,0),(1.46,.175,.150,.055,.032,0),(1.464,.171,.148,.054,.033,0)],cream)
plate('Chest collar silver frame',[(-.133,1.53),(-.085,1.558),(-.055,1.529),(.055,1.529),(.085,1.558),(.133,1.53),(.116,1.496),(.045,1.481),(-.045,1.481),(-.116,1.496)],-.084,silver,depth=.008,curve=.7)
plate('Chest collar inset burgundy',[(-.108,1.533),(-.084,1.548),(-.058,1.521),(.058,1.521),(.084,1.548),(.108,1.533),(.098,1.509),(.04,1.494),(-.04,1.494),(-.098,1.509)],-.095,red,curve=.5)
cylinder('Reactor recessed circular seat',(0,-.168,1.413),.044,.008,dark)
cylinder('Reactor silver bezel',(0,-.174,1.413),.041,.006,silver,vertices=64)
cylinder('Reactor cyan gasket',(0,-.178,1.413),.0365,.003,cyan,vertices=64)
cylinder('Reactor luminous core',(0,-.18,1.413),.033,.002,white,vertices=64)
for s in [-1,1]:
    plate('Thorax side machined frame '+str(s),mirrored(s,[(.105,1.28),(.115,1.365),(.143,1.4),(.173,1.38),(.187,1.324),(.156,1.275),(.145,1.288),(.17,1.328),(.159,1.368),(.144,1.376),(.132,1.351),(.123,1.288)]),-.077,silver,depth=.007,bevel=.0015)
    plate('Thorax lower champagne corner '+str(s),mirrored(s,[(.098,1.28),(.148,1.262),(.177,1.29),(.186,1.274),(.149,1.24),(.098,1.258)]),-.072,cream)
    for x,z in [(.126,1.36),(.153,1.29)]:cylinder('Thorax socket fastener '+str((s,x)),(s*x,-.085,z),.005,.003,dark,vertices=16)
    plate('Back champagne scapula '+str(s),mirrored(s,[(.012,1.506),(.058,1.551),(.134,1.54),(.186,1.496),(.139,1.457),(.058,1.413),(.024,1.431)]),.11,cream,depth=.009,curve=-.25)
    plate('Back overlapping burgundy wing '+str(s),mirrored(s,[(.074,1.507),(.161,1.52),(.198,1.476),(.153,1.405),(.073,1.332),(.047,1.354),(.119,1.431)]),.125,red,depth=.009,curve=-.3)
    plate('Back silver mechanical inset '+str(s),mirrored(s,[(.132,1.427),(.158,1.44),(.176,1.405),(.129,1.332),(.109,1.353)]),.112,silver)
patch('Back champagne central spine',[(1.305,.021,.126,.002,0,0),(1.312,.028,.128,.004,0,0),
    (1.419,.04,.14,.006,.005,0),(1.48,.071,.144,.014,.01,0),(1.486,.068,.143,.013,.01,0)],cream,back=True)
plate('Back red spinal inset',[(-.009,1.423),(-.012,1.551),(.012,1.551),(.009,1.423)],.148,red,depth=.004)
save('02-thorax')

# Stage 3. Three closely seated abdominal bands, circular side hinges, pelvis.
section('Waist red understructure',[(1.035,.13,.083,0,0),(1.15,.126,.086,0,0),(1.278,.14,.091,0,0)],red)
for i in range(3):
    z=1.085+i*.060
    patch('Abdominal champagne overlapping band '+str(i),[(z,.086,.107,.02,.013,0),(z+.004,.093,.113,.022,.013,0),
        (z+.05,.1,.119,.027,.012,0),(z+.054,.097,.117,.026,.012,0)],cream)
    for s in [-1,1]:
        plate('Abdominal articulated side band '+str((s,i)),mirrored(s,[(.085,z+.004),(.118,z-.003),(.143,z+.025),(.132,z+.052),(.091,z+.04)]),-.062,red,depth=.008)
        cylinder('Abdominal exposed side hinge '+str((s,i)),(s*.118,-.077,z+.026),.010,.005,silver,vertices=24)
        line('Abdominal silver hinge link '+str((s,i)),[(s*.09,-.087,z+.014),(s*.11,-.085,z+.024),(s*.133,-.066,z+.04)],silver,.003)
        patch('Lumbar champagne return '+str((s,i)),[(z,.027,.09,.003,0,s*.102),(z+.004,.035,.096,.004,0,s*.101),
            (z+.049,.039,.099,.005,0,s*.097),(z+.052,.035,.096,.004,0,s*.097)],cream,back=True)
    plate('Lumbar central red chevron '+str(i),[(-.066,z+.015),(0,z+.005),(.066,z+.015),(.066,z+.037),(0,z+.026),(-.066,z+.037)],.094,red)
section('Pelvis red structural girdle',[(.94,.108,.078,0,0),(.986,.15,.094,0,0),(1.042,.142,.088,0,0),(1.075,.124,.081,0,0)],red,segments=32)
patch('Pelvis champagne front belt',[(1.012,.114,.101,.025,.002,0),(1.017,.124,.105,.027,.004,0),
    (1.058,.112,.108,.025,.007,0),(1.062,.105,.105,.022,.006,0)],cream)
plate('Pelvis central burgundy codpiece',[(-.065,1.012),(-.063,.969),(-.038,.92),(0,.905),(.038,.92),(.063,.969),(.065,1.012)],-.098,red,depth=.015,bevel=.005)
plate('Pelvis back sacral shield',[(-.103,1.039),(-.117,.995),(-.064,.946),(0,.932),(.064,.946),(.117,.995),(.103,1.039)],.098,red,depth=.012,bevel=.004)
for s in [-1,1]:
    cylinder('Pelvis recessed hip bearing '+str(s),(s*.15,0,.982),.037,.014,dark,axis='X')
    cylinder('Pelvis silver hip rim '+str(s),(s*.158,0,.982),.028,.005,silver,axis='X')
    plate('Pelvis lateral red shield '+str(s),mirrored(s,[(.111,1.053),(.158,1.05),(.176,1.006),(.16,.97),(.142,.984),(.142,1.02),(.113,1.024)]),-.04,red,depth=.075)
save('03-abdomen-pelvis')

# Stage 4. Arms with angular pauldron shells and separate joint brackets.
for s,side in [(-1,'L'),(1,'R')]:
    arm=joint('Shoulder_'+side,(s*.235,0,1.485),root)
    arm.rotation_euler.y=-s*.10
    cylinder('Shoulder drive '+side,(0,0,0),.055,.09,dark,arm,'X')
    section('Shoulder angular champagne cap '+side,[(-.088,.051,.064,s*.012,0),(-.074,.073,.083,s*.013,0),
        (.02,.082,.086,s*.008,0),(.065,.059,.066,0,0),(.074,.031,.035,0,0)],cream,arm,24,.55,.003)
    section('Shoulder silver lower rim '+side,[(-.094,.055,.067,s*.012,0),(-.083,.069,.08,s*.012,0)],silver,arm,24,.6)
    plate('Shoulder burgundy inner block '+side,[(-.038,.042),(-.035,.072),(.032,.069),(.047,.04),(.028,.029),(-.026,.029)],-.063,red,arm,depth=.025)
    plate('Shoulder silver articulated bracket '+side,[(-.057,.011),(-.048,.038),(-.028,.023),(-.035,-.028),(-.018,-.061),(-.027,-.073),(-.05,-.04)],-.085,silver,arm,depth=.008)
    for j in range(3):cylinder('Shoulder bracket screw '+side+str(j),(-.04,-.092,.016-j*.024),.0035,.002,dark,arm,vertices=16)
    section('Bicep burgundy sleeve '+side,[(-.289,.036,.043,0,0),(-.25,.051,.057,0,0),(-.125,.061,.068,0,0),(-.075,.048,.054,0,0)],red,arm,24,.69)
    patch('Bicep champagne insert '+side,[(-.263,.025,.051,.007,0,0),(-.256,.035,.06,.012,0,0),
        (-.16,.042,.072,.015,0,0),(-.139,.034,.068,.012,0,0)],cream,arm)
    patch('Tricep champagne shell '+side,[(-.25,.03,.05,.009,0,0),(-.23,.044,.06,.013,0,0),
        (-.125,.049,.067,.014,0,0),(-.105,.035,.054,.01,0,0)],cream,arm,back=True)
    elbow=joint('Elbow_'+side,(0,0,-.31),arm)
    cylinder('Elbow transverse bearing '+side,(0,0,0),.038,.088,dark,elbow,'X')
    for j in range(4):
        section('Elbow silver flexible band '+side+str(j),[(-.012-j*.011,.039,.045,0,0),(-.02-j*.011,.04,.046,0,0)],silver,elbow,24,.9,.0006)
    section('Forearm burgundy shaped shell '+side,[(-.252,.032,.037,0,0),(-.22,.041,.047,0,0),
        (-.11,.061,.063,0,0),(-.061,.056,.059,0,0),(-.036,.038,.043,0,0)],red,elbow,24,.61,.0025)
    patch('Forearm champagne upper split '+side,[(-.15,.026,.062,.009,0,-.012),(-.144,.033,.067,.013,0,-.013),
        (-.077,.037,.068,.015,0,-.013),(-.053,.027,.059,.01,0,-.012)],cream,elbow)
    plate('Forearm champagne diagonal '+side,[(-.036,-.2),(-.039,-.163),(.033,-.213),(.027,-.236),(-.028,-.216)],-.049,cream,elbow,depth=.004,bevel=.0015)
    patch('Forearm rear silver access '+side,[(-.215,.022,.046,.007,0,0),(-.207,.029,.051,.009,0,0),
        (-.112,.037,.067,.013,0,0),(-.095,.029,.06,.009,0,0)],cream,elbow,back=True)
    wrist=joint('Wrist_'+side,(0,0,-.26),elbow)
    cylinder('Wrist silver bearing '+side,(0,0,0),.031,.014,silver,wrist,'Z')
    section('Hand metacarpal red shell '+side,[(-.096,.03,.024,0,0),(-.081,.041,.028,0,0),(-.021,.037,.03,0,0),(-.006,.028,.024,0,0)],red,wrist,24,.57,.002)
    patch('Hand red dorsal shield '+side,[(-.097,.028,.028,.004,0,0),(-.089,.036,.034,.006,0,0),
        (-.026,.033,.036,.006,0,0),(-.015,.025,.03,.004,0,0)],red,wrist,back=True)
    cylinder('Palm repulsor bezel '+side,(0,-.032,-.055),.022,.006,silver,wrist)
    cylinder('Palm repulsor cyan lens '+side,(0,-.037,-.055),.017,.003,cyan,wrist)
    for finger in range(5):
        base=joint('Finger_'+side+'_'+str(finger),((finger-1.5)*.019 if finger<4 else s*.041,0,-.095 if finger<4 else -.04),wrist)
        if finger==4:base.rotation_euler.y=-s*.65
        for j,length in enumerate([.028,.023,.018]):
            digit=joint(f'Digit_{side}_{finger}_{j}',(0,0,0 if j==0 else -previous),base)
            cylinder('Finger hinge '+str((side,finger,j)),(0,0,0),.007,.015,dark,digit,'X',16)
            section('Finger champagne phalanx '+str((side,finger,j)),[(-length,.006,.006,0,0),(-length+.003,.008,.008,0,0),(-.004,.008,.009,0,0),(0,.006,.006,0,0)],cream,digit,12,.65,.0007)
            digit.rotation_euler.x=.4 if j==0 else .8
            previous=length;base=digit
save('04-arms-hands')

# Stage 5. Shorter, fuller thighs, recessed knee windows, wider armored feet.
for s,side in [(-1,'L'),(1,'R')]:
    hip=joint('Hip_'+side,(s*.095,0,.99),root)
    section('Thigh burgundy chassis '+side,[(-.41,.048,.058,0,0),(-.35,.065,.076,0,0),(-.12,.082,.091,0,0),(-.018,.071,.077,0,0)],red,hip,28,.66,.0025)
    patch('Thigh champagne front armor '+side,[(-.325,.043,.077,.018,.008,0),(-.319,.05,.083,.022,.008,0),
        (-.14,.061,.099,.028,.004,0),(-.09,.056,.094,.024,.004,0),(-.085,.052,.091,.023,.004,0)],cream,hip)
    patch('Thigh champagne posterior '+side,[(-.331,.043,.073,.014,.005,0),(-.32,.051,.082,.02,.005,0),
        (-.115,.066,.094,.029,.004,0),(-.075,.055,.085,.022,.003,0)],cream,hip,back=True)
    for i in range(2):
        z=-.321-i*.044
        plate('Thigh gold stepped border '+side+str(i),[(-.052,z+.009),(-.041,z-.015),(0,z-.028),(.041,z-.015),(.052,z+.009),(.045,z+.008),(.035,z-.007),(0,z-.018),(-.035,z-.007),(-.045,z+.008)],-.08,gold,hip,depth=.003,bevel=.001)
        plate('Thigh champagne stepped border '+side+str(i),[(-.055,z),(-.047,z-.023),(0,z-.041),(.047,z-.023),(.055,z),(.047,z-.009),(.039,z-.017),(0,z-.031),(-.039,z-.017),(-.047,z-.009)],-.078,cream,hip,depth=.004,bevel=.001)
    knee=joint('Knee_'+side,(0,0,-.435),hip)
    cylinder('Knee recessed bearing '+side,(0,0,0),.037,.1,dark,knee,'X')
    cylinder('Knee silver actuator rim '+side,(s*.051,0,0),.028,.005,silver,knee,'X')
    plate('Knee red angular patella '+side,[(-.046,.04),(-.055,.019),(-.044,-.065),(-.021,-.079),(.03,-.071),(.049,-.025),(.046,.036)],-.061,red,knee,depth=.015,bevel=.004)
    for j in range(7):
        plate('Knee posterior sliding rib '+side+str(j),[(-.03,.026-j*.013),(-.033,.02-j*.013),(-.032,.011-j*.013),(.032,.011-j*.013),(.033,.02-j*.013),(.03,.026-j*.013)],.056,silver,knee,depth=.006,bevel=.0015)
    section('Calf burgundy contoured shell '+side,[(-.425,.042,.047,0,0),(-.37,.048,.059,0,.005),(-.22,.063,.082,0,.012),
        (-.13,.068,.084,0,.01),(-.075,.052,.063,0,0)],red,knee,28,.7,.0025)
    patch('Shin champagne front shaped greave '+side,[(-.426,.039,.057,.01,0,0),(-.42,.043,.061,.012,0,0),
        (-.27,.049,.074,.016,0,0),(-.205,.05,.081,.018,.007,0),(-.194,.044,.077,.015,.006,0)],cream,knee)
    plate('Shin silver upper angular frame '+side,[(-.052,-.169),(-.027,-.197),(.027,-.197),(.052,-.169),(.051,-.18),(.029,-.207),(-.029,-.207),(-.051,-.18)],-.074,silver,knee,depth=.004,bevel=.001)
    patch('Calf champagne rear ankle shell '+side,[(-.426,.037,.056,.01,0,0),(-.416,.044,.062,.012,0,0),
        (-.346,.049,.073,.016,0,0),(-.338,.046,.071,.014,0,0)],cream,knee,back=True)
    plate('Calf rear silver service surround '+side,[(-.035,-.21),(-.045,-.225),(-.04,-.344),(.04,-.344),(.045,-.225),(.035,-.21)],.093,silver,knee,depth=.005,bevel=.0025)
    plate('Calf red inset service hatch '+side,[(-.029,-.226),(-.035,-.238),(-.031,-.331),(.031,-.331),(.035,-.238),(.029,-.226)],.1,red,knee,depth=.004,bevel=.002)
    ankle=joint('Ankle_'+side,(0,0,-.44),knee)
    section('Boot wide armored hull '+side,[(-.114,.051,.119,0,-.055),(-.102,.058,.133,0,-.058),(-.061,.059,.132,0,-.057),
        (-.025,.052,.105,0,-.035),(.025,.044,.065,0,-.008),(.04,.038,.049,0,0)],red,ankle,28,.5,.003)
    section('Boot silver sole '+side,[(-.115,.053,.121,0,-.055),(-.108,.057,.13,0,-.057)],silver,ankle,28,.55,.001)
    patch('Boot champagne raised instep '+side,[(-.095,.046,.185,.012,0,0),(-.087,.049,.189,.013,0,0),
        (-.05,.05,.163,.013,0,0),(-.008,.044,.108,.011,0,0),(.031,.036,.061,.007,0,0)],cream,ankle)
    for j in range(2):
        z=-.051+j*.032
        patch('Boot champagne articulated strap '+side+str(j),[(z-.01,.049,.155-j*.036,.014,0,0),(z-.007,.053,.159-j*.036,.015,0,0),
            (z+.009,.051,.146-j*.034,.014,0,0),(z+.011,.047,.14-j*.032,.012,0,0)],cream,ankle)
    cylinder('Boot flight emitter bezel '+side,(0,-.03,-.116),.027,.004,dark,ankle,'Z')
    cylinder('Boot flight thruster '+side,(0,-.03,-.119),.02,.002,cyan,ankle,'Z')
save('05-legs-boots')

# Real reference files are packed into an out-of-render collection in the master.
references=bpy.data.collections.new('SUPPLIED_REFERENCE_IMAGES');S.collection.children.link(references)
names=['front-up-wire','backupwire','front-mid-wire','backmid-wire','front-down-wire','backdown-wire']
for index,name in enumerate(names):
    filename=Path('C:/Users/Anabhayan/Downloads')/f'jacek-krzesinski-{name}.jpg'
    image=bpy.data.images.load(str(filename),check_existing=True);image.pack()
    empty=bpy.data.objects.new('REFERENCE '+name,None);references.objects.link(empty)
    empty.empty_display_type='IMAGE';empty.data=image;empty.empty_display_size=1.5
    empty.location=(2+index*1.6,0,1);empty.rotation_euler.x=math.pi/2;empty.hide_render=True
references.hide_render=True

# Scale is measured on the evaluated body only, excluding the reference empties.
bpy.context.view_layer.update();d=bpy.context.evaluated_depsgraph_get()
pts=[o.matrix_world@Vector(c) for o in S.objects if o.type=='MESH' for c in o.evaluated_get(d).bound_box]
low=min(v.z for v in pts);factor=1.85/(max(v.z for v in pts)-low)
root.scale=(factor,)*3;root.location.z=-low*factor
root['fresh_geometry']=True
root['reference_notes']='Six supplied wireframe JPGs and earlier color reference; rebuilt, not recovered source mesh'

# Studio renders show shape at a much larger scale than a runtime sprite.
S.render.engine='CYCLES';S.cycles.samples=48;S.cycles.use_denoising=True
S.render.film_transparent=True;S.view_settings.view_transform='AgX'
S.world.use_nodes=True;S.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.35
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
for name,pos,power,size,col in [('Key',(-2,-3,4),420,2.5,(1,.88,.75)),('Fill',(2,-2,2),260,2,(.72,.85,1)),('Rim',(1,3,3),550,2,(1,.9,.8)),('Back fill',(-2,3,2),260,2,(.8,.88,1))]:
    bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.name=name
    o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.data.color=col;aim(o,(0,0,1))
bpy.ops.object.camera_add(location=(2.5,-5,1.5));camera=bpy.context.object;camera.name='Reference comparison camera'
camera.data.type='ORTHO';camera.data.ortho_scale=2.10;aim(camera,(0,0,.925));S.camera=camera
S.render.resolution_x=1000;S.render.resolution_y=1200;S.render.resolution_percentage=100
save('reference-armor')
bpy.ops.object.select_all(action='DESELECT')
for o in [root]+list(root.children_recursive):o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'reference-armor.glb'),export_format='GLB',use_selection=True,export_apply=True,export_animations=False)
for name,pos in [('front',(0,-5,1.02)),('back',(0,5,1.02)),('three-quarter',(2.5,-5,1.5))]:
    camera.location=pos;aim(camera,(0,0,.925));S.render.filepath=str(OUT/f'{name}.png');bpy.ops.render.render(write_still=True)
S.render.resolution_x=1000;S.render.resolution_y=1000
camera.location=(1.6,-4,1.65);camera.data.ortho_scale=.78;aim(camera,(0,0,1.4))
S.render.filepath=str(OUT/'upper-detail.png');bpy.ops.render.render(write_still=True)
(OUT/'measurements.json').write_text(json.dumps({'target_height_m':1.85,'landmarks_unscaled_m':landmarks,'body_scale':factor,'reused_body_meshes':0,'packed_reference_images':6},indent=2))
print('FRESH_REFERENCE_ARMOR_COMPLETE',OUT,flush=True)

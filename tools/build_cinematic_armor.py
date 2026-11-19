"""Reference-informed 1.85 m armor. Run with Blender 5.2 --background --python."""
import bpy
import math
import json
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'app/static/models/cinematic'
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
S = bpy.context.scene
S.unit_settings.system = 'METRIC'
S.unit_settings.scale_length = 1
bpy.context.preferences.filepaths.save_version = 0

def material(name, color, metal, rough, emit=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    nodes = m.node_tree.nodes
    p = nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Metallic'].default_value = metal
    p.inputs['Roughness'].default_value = rough
    p.inputs['Coat Weight'].default_value = .38 if 'Candy' in name else .12
    p.inputs['Coat Roughness'].default_value = .18
    p.inputs['Emission Color'].default_value = (*color, 1)
    p.inputs['Emission Strength'].default_value = emit
    if not emit:
        noise = nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = 240
        bump = nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = .11
        bump.inputs['Distance'].default_value = .00012
        m.node_tree.links.new(noise.outputs['Fac'], bump.inputs['Height'])
        m.node_tree.links.new(bump.outputs['Normal'], p.inputs['Normal'])
        for socket in p.inputs:
            if socket.name in {'Anisotropic', 'Anisotropic IOR Level'}:
                socket.default_value = .25 if 'Gold' in name else .05
    return m

red = material('Candy apple multilayer red', (.36,.008,.016), .82,.23)
gold = material('Gold champagne brushed alloy', (.69,.48,.19), .86,.29)
ti = material('Dark titanium mechanisms', (.065,.075,.089), .8,.34)
gap = material('Black recessed panel channels', (.008,.012,.017), .35,.44)
cyan = material('Cyan ion emission', (.10,.82,1), .3,.2, 5)
white = material('Reactor luminous core', (.65,.94,1), .1,.2, 8)

def joint(name, pos, parent=None):
    o = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(o)
    o.parent = parent
    o.location = pos
    return o

root = joint('Armor_Root_METERS', (0,0,0))
root['height_m'] = 1.85
root['reference'] = 'User supplied front/back image; interpreted geometry, no image textures'

def mesh(name, verts, faces, mat, parent=root, sub=0, bevel=0):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    o = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(o)
    o.parent = parent
    o.data.materials.append(mat)
    # Consistent outward normals for closed custom geometry.
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    o.select_set(False)
    for p in data.polygons:
        p.use_smooth = True
    if sub:
        mod = o.modifiers.new('Curvature subdivision', 'SUBSURF')
        mod.levels = sub
        mod.render_levels = sub
    if bevel:
        mod = o.modifiers.new('Machined micro edge', 'BEVEL')
        mod.width = bevel
        mod.segments = 3
    return o

def loft(name, rings, mat, parent=root, start=0, end=math.tau, steps=32, sub=1):
    # Each ring: z, x radius, y radius, x offset, y offset.
    verts = []
    for z,rx,ry,cx,cy in rings:
        for k in range(steps+1):
            a = start+(end-start)*k/steps
            verts.append((cx+rx*math.sin(a), cy-ry*math.cos(a), z))
    n = steps+1
    faces = [(j*n+k,j*n+k+1,(j+1)*n+k+1,(j+1)*n+k)
             for j in range(len(rings)-1) for k in range(steps)]
    faces += [tuple(range(n-1,-1,-1)), tuple((len(rings)-1)*n+k for k in range(n))]
    faces += [(j*n,(j+1)*n,(j+2)*n-1,(j+1)*n-1) for j in range(len(rings)-1)]
    return mesh(name, verts, faces, mat, parent, sub)

def panel(name, points, y, depth, mat, parent=root, bulge=.012):
    # Rounded, crowned polygon plate with an inset control loop and closed back.
    cx = sum(x for x,z in points)/len(points)
    cz = sum(z for x,z in points)/len(points)
    n = len(points)
    outward = -1 if y < 0 else 1
    verts = [(x,y,z) for x,z in points]
    verts += [(cx+(x-cx)*.86,y+outward*bulge,cz+(z-cz)*.86) for x,z in points]
    verts += [(x,y-outward*depth,z) for x,z in points]
    verts += [(cx,y+outward*bulge,cz)]
    faces = []
    for i in range(n):
        j = (i+1)%n
        faces.extend([(i,j,n+j,n+i),(n+i,n+j,3*n),(i,2*n+i,2*n+j,j)])
    faces.append(tuple(2*n+i for i in range(n-1,-1,-1)))
    return mesh(name,verts,faces,mat,parent,0,.002)

def tube(name, points, radius, mat, parent=root):
    c = bpy.data.curves.new(name,'CURVE')
    c.dimensions = '3D'
    c.bevel_depth = radius
    c.bevel_resolution = 2
    sp = c.splines.new('POLY')
    sp.points.add(len(points)-1)
    for p,co in zip(sp.points,points):
        p.co = (*co,1)
    o = bpy.data.objects.new(name,c)
    bpy.context.collection.objects.link(o)
    o.parent = parent
    o.data.materials.append(mat)
    return o

def disk(name, pos, radius, depth, mat, parent=root, axis='Y', vertices=32):
    # Lathed mechanical component, bevelled at its rim.
    rings = [(-depth/2,radius*.91),(-depth*.35,radius),(depth*.35,radius),(depth/2,radius*.91)]
    o = loft(name, [(z,r,r,0,0) for z,r in rings], mat, parent, steps=vertices, sub=0)
    o.location = pos
    if axis == 'Y': o.rotation_euler.x = math.pi/2
    if axis == 'X': o.rotation_euler.y = math.pi/2
    return o

# Torso: tapered anatomical hull and separately crowned pectoral plates.
loft('Thoracic titanium underframe',[(1.12,.125,.085,0,0),(1.18,.14,.092,0,0),(1.33,.19,.115,0,0),(1.46,.222,.11,0,0),(1.52,.16,.075,0,0)],gap)
for s in [-1,1]:
    def mirror(points): return [(s*x,z) for x,z in points]
    panel('Sculpted pectoral '+str(s),mirror([(.008,1.415),(.04,1.50),(.145,1.515),(.205,1.465),(.202,1.37),(.142,1.294),(.053,1.29),(.014,1.33)]),-.115,.038,red,bulge=.033)
    panel('Clavicle gold accent '+str(s),mirror([(.035,1.515),(.145,1.535),(.205,1.493),(.183,1.477),(.139,1.507),(.05,1.499)]),-.089,.012,gold)
    for i in range(5):
        z=1.17+i*.041
        panel('Oblique interlocking rib '+str((s,i)),mirror([(.10,z),(.153,z+.023),(.18,z+.067),(.151,z+.062),(.11,z+.023)]),-.078,.025,red,bulge=.008)
    panel('Back scapular shell '+str(s),mirror([(.015,1.50),(.085,1.538),(.178,1.514),(.213,1.458),(.145,1.399),(.035,1.43)]),.103,.025,red,bulge=.023)
    panel('Back swept wing '+str(s),mirror([(.045,1.407),(.17,1.458),(.192,1.385),(.143,1.28),(.072,1.215),(.055,1.29)]),.115,.025,red)
    panel('Back gold rail '+str(s),mirror([(.18,1.401),(.19,1.386),(.14,1.268),(.085,1.204),(.072,1.217),(.13,1.292)]),.143,.008,gold)
    for i in range(5):
        tube('Scapula vent '+str((s,i)),[(s*(.11+i*.011),.151,1.377),(s*(.09+i*.011),.151,1.34)],.003,ti)
    disk('Integrated back thruster housing '+str(s),(s*.118,.133,1.365),.033,.022,ti)
    disk('Back ion nozzle '+str(s),(s*.118,.148,1.365),.021,.008,cyan)

# Nested triangular reactor, oriented point down as in the supplied reference.
panel('Central sculpted sternum',[(-.052,1.448),(0,1.466),(.052,1.448),(.063,1.355),(.036,1.292),(-.036,1.292),(-.063,1.355)],-.125,.024,red,bulge=.018)
triangle=[(-.049,1.408),(.049,1.408),(0,1.316)]
panel('Triangular reactor black recess',triangle,-.159,.018,gap,bulge=0)
for scale,y,mat,name in [(1,-.174,gold,'Reactor machined rim'),(.82,-.180,cyan,'Reactor cyan lens'),(.57,-.185,white,'Reactor triangular core')]:
    panel(name,[(x*scale,1.374+(z-1.374)*scale) for x,z in triangle],y,.006,mat,bulge=0)
for i in range(6):
    z=1.055+i*.043
    w=.102+i*.004
    panel('Abdominal overlapping chevron '+str(i),[(-w,z+.038),(-w*.84,z-.002),(0,z-.018),(w*.84,z-.002),(w,z+.038),(0,z+.022)],-.086-i*.003,.025,red,bulge=.013)
    panel('Dorsal spinal vertebra '+str(i),[(-.028,z),(-.033,z+.027),(0,z+.038),(.033,z+.027),(.028,z),(0,z-.007)],.105,.022,red)
    for s in [-1,1]:
        tube('Spinal hydraulic '+str((s,i)),[(s*.043,.105,z),(s*.047,.107,z+.032)],.006,ti)

loft('Pelvic titanium core',[(.925,.105,.074,0,0),(.97,.15,.09,0,0),(1.065,.128,.082,0,0)],ti)
panel('Pelvis central armored shield',[(-.117,1.06),(-.13,1.01),(-.057,.946),(0,.91),(.057,.946),(.13,1.01),(.117,1.06),(0,1.032)],-.093,.025,red)
panel('Rear sacral shell',[(-.13,1.058),(-.15,.984),(-.09,.933),(0,.922),(.09,.933),(.15,.984),(.13,1.058),(0,1.041)],.094,.024,red)

# Neck and helmet: shaped lathed shell plus purpose-built faceplate zones.
neck=joint('Neck', (0,0,1.52),root)
loft('Neck flexible seal',[(0,.056,.048,0,0),(.07,.054,.05,0,0)],gap,neck)
for i in range(4):
    loft('Neck segmented collar '+str(i),[(i*.018,.059,.054,0,0),(i*.018+.012,.06,.055,0,0)],red,neck,sub=0)
head=joint('Head', (0,0,1.585),root)
loft('Helmet red sculpted cranial shell',[(0,.043,.058,0,0),(.025,.065,.071,0,0),(.08,.083,.080,0,0),(.15,.088,.083,0,0),(.202,.077,.073,0,0),(.232,.047,.049,0,0),(.24,.006,.009,0,0)],red,head,steps=48,sub=2)
panel('Gold upper faceplate',[(-.073,.167),(-.058,.218),(-.032,.212),(0,.184),(.032,.212),(.058,.218),(.073,.167),(.064,.119),(.025,.111),(0,.119),(-.025,.111),(-.064,.119)],-.075,.014,gold,head,bulge=.012)
panel('Gold cheek and jaw faceplate',[(-.066,.109),(-.024,.101),(0,.109),(.024,.101),(.066,.109),(.056,.067),(.033,.027),(-.033,.027),(-.056,.067)],-.081,.015,gold,head,bulge=.018)
for s in [-1,1]:
    pts=[(s*x,z) for x,z in [(.012,.116),(.065,.128),(.06,.116),(.021,.107)]]
    panel('Eye socket '+str(s),pts,-.093,.009,gap,head,bulge=0)
    cx=sum(x for x,z in pts)/4;cz=sum(z for x,z in pts)/4
    panel('Illuminated eye '+str(s),[(cx+(x-cx)*.82,cz+(z-cz)*.62) for x,z in pts],-.098,.003,cyan,head,bulge=0)
    disk('Temple actuator '+str(s),(s*.081,.001,.12),.034,.014,ti,head,'X')
    disk('Temple red cover '+str(s),(s*.089,.001,.12),.025,.006,red,head,'X')
    tube('Jaw cheek seam '+str(s),[(s*.068,-.067,.099),(s*.057,-.073,.055),(s*.033,-.079,.021)],.002,gap,head)
panel('Mechanical gold chin',[(-.033,.021),(-.026,.002),(.026,.002),(.033,.021),(.02,.032),(-.02,.032)],-.071,.012,gold,head)
for i in range(3):
    panel('Rear helmet nape '+str(i),[(-.04,i*.026),(-.045,i*.026+.019),(.045,i*.026+.019),(.04,i*.026)],.070,.01,red,head)

shoulders=[];elbows=[];hips=[];knees=[]
for s,side in [(-1,'L'),(1,'R')]:
    shoulder=joint('Shoulder_'+side,(s*.235,0,1.477),root)
    shoulders.append(shoulder)
    shoulder.rotation_euler.y=s*-.12
    disk('Shoulder drive '+side,(0,0,0),.068,.10,ti,shoulder,'X')
    loft('Shoulder gold contoured cap '+side,[(-.084,.065,.077,0,0),(-.045,.082,.091,0,0),(.02,.083,.091,0,0),(.063,.051,.058,0,0),(.07,.018,.025,0,0)],gold,shoulder,start=-1.85,end=1.85,steps=28,sub=2)
    loft('Pauldron red crown '+side,[(.012,.087,.094,0,0),(.043,.072,.079,0,0),(.073,.025,.033,0,0)],red,shoulder,start=1.65,end=4.63,steps=28,sub=1)
    loft('Upper arm mechanical understructure '+side,[(-.275,.04,.045,0,0),(-.23,.056,.058,0,0),(-.10,.06,.065,0,0),(-.06,.05,.05,0,0)],ti,shoulder)
    loft('Gold bicep anatomical armor '+side,[(-.26,.038,.044,0,0),(-.23,.055,.063,0,0),(-.13,.067,.073,0,0),(-.085,.05,.057,0,0)],gold,shoulder,start=-1.8,end=1.8,sub=2)
    elbow=joint('Elbow_'+side,(0,0,-.285),shoulder)
    elbows.append(elbow)
    disk('Elbow hinge '+side,(0,0,0),.042,.094,ti,elbow,'X')
    for i in range(5):
        loft('Elbow bellows '+side+str(i),[(-.025-i*.009,.041,.043,0,0),(-.03-i*.009,.043,.045,0,0)],gap,elbow,sub=0)
    loft('Forearm titanium shell '+side,[(-.245,.032,.037,0,0),(-.19,.043,.048,0,0),(-.08,.057,.058,0,0),(-.03,.039,.043,0,0)],ti,elbow)
    loft('Swept red forearm carapace '+side,[(-.24,.033,.041,0,0),(-.20,.045,.055,0,0),(-.08,.064,.068,0,0),(-.02,.045,.048,0,0)],red,elbow,start=-1.9,end=1.9,sub=2)
    panel('Forearm raised spear '+side,[(-.038,-.075),(0,-.032),(.038,-.075),(.03,-.17),(0,-.225),(-.03,-.17)],-.061,.008,red,elbow)
    for i in range(3):
        tube('Forearm recessed seam '+side+str(i),[(-.035,.052,-.10-i*.025),(0,.062,-.112-i*.025),(.035,.052,-.10-i*.025)],.0025,gap,elbow)
    wrist=joint('Wrist_'+side,(0,0,-.25),elbow)
    disk('Wrist bearing '+side,(0,0,0),.033,.023,ti,wrist,'Z')
    loft('Hand contoured metacarpal armor '+side,[(-.10,.031,.022,0,0),(-.08,.041,.026,0,0),(-.022,.037,.028,0,0),(0,.029,.022,0,0)],red,wrist,sub=2)
    disk('Palm repulsor titanium bezel '+side,(0,-.027,-.054),.024,.012,ti,wrist)
    disk('Palm repulsor cyan lens '+side,(0,-.035,-.054),.017,.005,cyan,wrist)
    for f in range(5):
        finger=joint('Finger_'+side+'_'+str(f),( (f-1.5)*.019 if f<4 else s*.044, 0, -.096 if f<4 else -.047),wrist)
        if f==4: finger.rotation_euler.y=s*-.65
        lengths=[.026,.022,.018] if f<4 else [.023,.02,.016]
        for j,l in enumerate(lengths):
            knuckle=joint('Digit_'+side+'_'+str(f)+'_'+str(j),(0,0,0 if j==0 else -lengths[j-1]),finger)
            disk('Finger hinge '+side+str((f,j)),(0,0,0),.008,.018,ti,knuckle,'X',16)
            loft('Finger phalanx '+side+str((f,j)),[(-l,.006,.006,0,0),(-l+.003,.008,.009,0,0),(-.004,.008,.009,0,0),(0,.006,.006,0,0)],red,knuckle,steps=12,sub=1)
            knuckle.rotation_euler.x = -.11 if j else 0
            finger=knuckle
    hip=joint('Hip_'+side,(s*.095,0,.965),root)
    hips.append(hip)
    loft('Thigh mechanical core '+side,[(-.40,.047,.051,0,0),(-.34,.061,.069,0,0),(-.12,.079,.089,0,0),(-.02,.067,.074,0,0)],ti,hip)
    loft('Thigh gold main armor '+side,[(-.385,.047,.054,0,0),(-.32,.064,.076,0,0),(-.13,.083,.096,0,0),(-.035,.062,.073,0,0)],gold,hip,start=-1.40,end=1.40,steps=28,sub=2)
    for sign in [-1,1]:
        loft('Thigh red outer rail '+side+str(sign),[(-.32,.067,.077,0,0),(-.15,.087,.098,0,0),(-.035,.072,.08,0,0),(.015,.048,.06,0,0)],red,hip,start=sign*1.45-.25,end=sign*1.45+.25,steps=10,sub=1)
    loft('Rear thigh gold plate '+side,[(-.34,.055,.06,0,0),(-.13,.077,.087,0,0),(-.04,.066,.073,0,0)],gold,hip,start=2.1,end=4.18,steps=24,sub=2)
    knee=joint('Knee_'+side,(0,0,-.415),hip)
    knees.append(knee)
    disk('Mechanical knee axle '+side,(0,0,0),.043,.108,ti,knee,'X')
    panel('Gold articulated patella '+side,[(-.045,.021),(0,.037),(.045,.021),(.04,-.036),(0,-.063),(-.04,-.036)],-.063,.019,gold,knee,bulge=.012)
    for i in range(4):
        tube('Rear knee flexure '+side+str(i),[(-.034,.048,-.025+i*.012),(0,.062,-.031+i*.012),(.034,.048,-.025+i*.012)],.004,ti,knee)
    loft('Calf mechanical core '+side,[(-.42,.033,.042,0,0),(-.32,.044,.053,0,.012),(-.15,.064,.075,0,.014),(-.055,.044,.051,0,0)],ti,knee)
    loft('Red sculpted shin greave '+side,[(-.425,.038,.046,0,0),(-.34,.044,.058,0,0),(-.18,.057,.076,0,.006),(-.08,.063,.070,0,0),(-.04,.043,.047,0,0)],red,knee,start=-1.8,end=1.8,steps=32,sub=2)
    loft('Rear calf armored thruster cowling '+side,[(-.39,.037,.046,0,0),(-.26,.049,.069,0,.013),(-.13,.066,.081,0,.01),(-.06,.043,.055,0,0)],red,knee,start=1.86,end=4.42,steps=28,sub=2)
    for i in range(3):
        tube('Shin panel channel '+side+str(i),[(-.052,-.035,-.10-i*.087),(0,-.078+i*.008,-.13-i*.087),(.052,-.035,-.10-i*.087)],.002,gap,knee)
    panel('Calf titanium service panel '+side,[(-.022,-.27),(.022,-.27),(.019,-.389),(-.019,-.389)],.071,.006,ti,knee)
    ankle=joint('Ankle_'+side,(0,0,-.444),knee)
    # Foot hull has a forward toe, narrow heel, and rounded custom sections.
    loft('Armored boot contoured shell '+side,[(-.101,.039,.091,0,-.04),(-.091,.047,.108,0,-.049),(-.055,.047,.105,0,-.046),(-.014,.037,.063,0,-.012),(.018,.031,.041,0,0)],red,ankle,steps=40,sub=2)
    loft('Boot titanium sole '+side,[(-.105,.039,.092,0,-.04),(-.10,.043,.102,0,-.045),(-.09,.044,.102,0,-.045)],ti,ankle,sub=1)
    disk('Boot flight thruster bezel '+side,(0,-.025,-.104),.031,.006,gold,ankle,'Z')
    disk('Boot flight thruster '+side,(0,-.025,-.108),.022,.004,cyan,ankle,'Z')
    for i in range(3):
        tube('Toe articulation seam '+side+str(i),[(-.032,-.10-i*.012,-.047),(0,-.112-i*.012,-.04),(.032,-.10-i*.012,-.047)],.0015,gap,ankle)

# Normalize actual evaluated bounding box to precisely 1.85 m, soles at ground.
for o in S.objects:
    if o.type == 'MESH' and any(word in o.name for word in ['Thigh mechanical core','Calf mechanical core','Upper arm mechanical understructure']):
        for vertex in o.data.vertices:
            vertex.co.x *= .82
            vertex.co.y *= .82
bpy.context.view_layer.update()
deps=bpy.context.evaluated_depsgraph_get()
points=[o.matrix_world @ Vector(c) for o in S.objects if o.type=='MESH' for c in o.evaluated_get(deps).bound_box]
zmin=min(p.z for p in points);zmax=max(p.z for p in points)
scale=1.85/(zmax-zmin)
root.scale=(scale,scale,scale)
root.location.z=-zmin*scale
rest=root.location.z

# A single scene animation drives rigid armor joints without stretching plates.
S.render.fps=24
S.frame_start=1; S.frame_end=72
for frame in [1,24,40,56,72]:
    root.location.z=rest+(.012 if frame==24 else 0)
    root.keyframe_insert(data_path='location',frame=frame)
    for i,o in enumerate(shoulders):
        o.rotation_euler.y=(-1 if i==0 else 1)*-.12
        o.rotation_euler.x=0
        if i==1 and frame in [40,56]:
            o.rotation_euler.y=-1.1
            o.rotation_euler.x=.32
        o.keyframe_insert(data_path='rotation_euler',frame=frame)
    for i,o in enumerate(elbows):
        o.rotation_euler.y=-.30 if i==1 and frame in [40,56] else 0
        o.keyframe_insert(data_path='rotation_euler',frame=frame)
S.frame_set(1)

# Export evaluated geometry with supported metallic/roughness and emission.
bpy.ops.object.select_all(action='DESELECT')
for o in S.objects:
    if o.type in {'MESH','EMPTY','CURVE'}:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'ironman-cinematic.glb'),export_format='GLB',use_selection=True,export_apply=True,export_animations=True,export_animation_mode='SCENE',export_frame_range=True)
import runpy
runpy.run_path(str(ROOT/'tools/validate_cinematic_armor.py'), run_name='__main__')

# Studio lighting, front/back review cameras, and transparent runtime sprites.
S.render.engine='CYCLES'
S.cycles.samples=48
S.cycles.use_denoising=True
S.world.use_nodes=True
S.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.16,.19,.24,1)
S.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.45
S.render.film_transparent=True
S.view_settings.view_transform='AgX'
def aim(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
for name,pos,power,size,color in [('Warm key',(-2,-3,4),500,3,(1,.87,.74)),('Cool fill',(2,-1,2.5),380,2,(.65,.82,1)),('Rim strip',(1,2,3),650,2,(1,.9,.78)),('Back fill',(-2,3,2),450,2,(.65,.8,1))]:
    bpy.ops.object.light_add(type='AREA',location=pos)
    o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.data.color=color;aim(o,(0,0,1))
bpy.ops.object.camera_add(location=(0,-5,1.05))
cam=bpy.context.object;cam.name='Front review camera';cam.data.type='ORTHO';cam.data.ortho_scale=2.13;aim(cam,(0,0,.925));S.camera=cam
S.render.resolution_x=800;S.render.resolution_y=1000;S.render.resolution_percentage=100
for name,pos in [('front',(0,-5,1.05)),('back',(0,5,1.05)),('three-quarter',(2.4,-5,1.6))]:
    cam.location=pos;aim(cam,(0,0,.925));S.render.filepath=str(OUT/f'{name}.png');bpy.ops.render.render(write_still=True)
S.render.resolution_x=512;S.render.resolution_y=512;cam.data.ortho_scale=2.35
cam.location=(1.6,-5,1.4);aim(cam,(0,0,.97))
for name,frame in [('hover',1),('fire',48)]:
    S.frame_set(frame);S.render.filepath=str(OUT/f'ironman-{name}.png');bpy.ops.render.render(write_still=True)
S.frame_set(1)
cam.location=(2.4,-5,1.6);cam.data.ortho_scale=2.13;aim(cam,(0,0,.925))
S.render.resolution_x=800;S.render.resolution_y=1000
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'ironman-cinematic.blend'))
stats={'height_m':1.85,'mesh_objects':sum(o.type=='MESH' for o in S.objects),'joint_nodes':sum(o.type=='EMPTY' for o in S.objects),'notes':'Custom lofts and crowned polygon panels; rigid articulated hierarchy; procedural microfinish is Blender-only, GLB uses PBR constants.'}
(OUT/'build-report.json').write_text(json.dumps(stats,indent=2))
print('CINEMATIC_ARMOR_COMPLETE',stats)

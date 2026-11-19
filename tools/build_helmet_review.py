"""Build only a helmet, reusing cinematic mesh helpers. Outputs a new review revision."""
import bpy
import math
import sys
from pathlib import Path
from mathutils import Vector

PROJECT = Path(__file__).resolve().parents[1]
# Execute only reusable materials/functions; the body generation is never run.
source = (PROJECT/'tools/build_cinematic_armor.py').read_text()
exec(compile(source.split('# Torso:')[0], 'cinematic_mesh_helpers', 'exec'))
revision = 1
while (PROJECT/f'app/static/models/helmet-review-v{revision:03}').exists():
    revision += 1
OUT = PROJECT/f'app/static/models/helmet-review-v{revision:03}'
OUT.mkdir()
root.name = 'Helmet_Root_METERS'
root['height_m'] = .26
root['intended_suit_height_m'] = 1.85
root['stage'] = 'Helmet only; awaiting user review'

# Smooth closed quad shell; rings wrap without duplicate seam vertices.
def shell():
    rings = [(0,.041,.060,.005),(.012,.054,.072,.005),(.038,.069,.085,.004),
             (.080,.083,.094,.004),(.13,.091,.100,.007),(.182,.091,.100,.009),
             (.218,.083,.091,.012),(.244,.061,.068,.013),(.257,.029,.033,.013),
             (.259,.012,.014,.013)]
    n=64
    verts=[(rx*math.sin(i*math.tau/n),cy-ry*math.cos(i*math.tau/n),z)
           for z,rx,ry,cy in rings for i in range(n)]
    faces=[(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i)
           for j in range(len(rings)-1) for i in range(n)]
    verts += [(0,.005,-.003),(0,.013,.26)]
    bottom=len(verts)-2;top=bottom+1
    faces += [(bottom,(i+1)%n,i) for i in range(n)]
    faces += [(top,(len(rings)-1)*n+i,(len(rings)-1)*n+(i+1)%n) for i in range(n)]
    return mesh('Continuous red cranial shell',verts,faces,red,root,2)
shell()

# Swept quad patch: variable depth and row profiles shape the face, no flat fan.
def face(name, rows, mat, thickness=.003, smooth=2):
    us=[-1,-.94,-.78,-.57,-.32,-.13,0,.13,.32,.57,.78,.94,1]
    verts=[]
    for width,z,front,edge,v in rows:
        for u in us:
            verts.append((u*width,front+edge*abs(u)**1.65,z+v*abs(u)))
    n=len(us)
    faces=[(j*n+i,j*n+i+1,(j+1)*n+i+1,(j+1)*n+i)
           for j in range(len(rows)-1) for i in range(n-1)]
    o=mesh(name,verts,faces,mat,root,smooth)
    solid=o.modifiers.new('Machined shell thickness','SOLIDIFY');solid.thickness=thickness
    bevel=o.modifiers.new('Faceplate edge highlights','BEVEL');bevel.width=.0007;bevel.segments=3
    return o

face('Gold forehead with swept crown horns',[
    (.070,.136,-.111,.029,-.001),(.072,.138,-.112,.029,-.001),
    (.076,.163,-.112,.032,0),(.077,.191,-.106,.027,.005),
    (.074,.191,-.097,.055,.040),(.073,.193,-.096,.055,.040)],gold)
face('Gold sculpted cheeks nose and lower face',[
    (.038,.034,-.094,.009,0),(.039,.036,-.097,.010,0),
    (.049,.063,-.110,.019,.002),(.063,.086,-.115,.030,.005),
    (.071,.107,-.115,.034,.010),(.071,.122,-.113,.033,.003),
    (.070,.124,-.112,.032,.002)],gold)

face('Black continuous recessed visor channel',[
    (.070,.123,-.109,.030,.001),(.071,.138,-.108,.030,-.001)],gap,smooth=1)

# Eyes follow the curved front, placed wholly ahead of the red shell.
def eye_points(s, scale=1):
    points=[(.014,.128),(.063,.133),(.067,.136),(.015,.132)]
    cx=.039;cz=.131
    return [(s*(cx+(x-cx)*scale),cz+(z-cz)*scale) for x,z in points]
for s in [-1,1]:
    panel('Recessed eye socket '+str(s),eye_points(s,1.15),-.110,.007,gap,bulge=0)
    eye=panel('Cyan optical slit '+str(s),eye_points(s,.82),-.114,.002,cyan,bulge=0)
    # Bend sockets and lenses around the facial contour.
    for obj in [eye,bpy.data.objects['Recessed eye socket '+str(s)]]:
        for vertex in obj.data.vertices:
            vertex.co.y += .030*(abs(vertex.co.x)/.074)**1.65
    # Side plates wrap cheek-to-temple and retain red border channels.
    face('Red mandible rail '+str(s),[
        (.053,.014,-.052,.004,0),(.059,.027,-.059,.005,0),
        (.072,.062,-.065,.006,0),(.082,.10,-.060,.003,0)],red,smooth=1)
    # Keep only the corresponding side of each rail patch.
    obj=bpy.data.objects['Red mandible rail '+str(s)]
    for index,vertex in enumerate(obj.data.vertices):
        row=index//13
        width=[.053,.059,.072,.082][row]
        t=(vertex.co.x/width+1)*.5
        inner=[.032,.040,.052,.067][row]
        outer=[.047,.058,.076,.085][row]
        front=[-.072,-.080,-.082,-.071][row]
        vertex.co.x=s*(inner+(outer-inner)*t)
        vertex.co.y=front+.052*t
    tube('Faceplate perimeter channel '+str(s),[(s*.038,-.093,.034),(s*.051,-.094,.064),(s*.067,-.085,.09),(s*.073,-.073,.118),(s*.076,-.069,.17),(s*.073,-.042,.226)],.0009,gap)
    # Reuse lathed disk function for the concentric temporal drive.
    disk('Temple black recess '+str(s),(s*.087,.002,.139),.027,.008,gap,axis='X')
    disk('Temple titanium ring '+str(s),(s*.091,.002,.139),.023,.005,ti,axis='X')
    disk('Temple red inset '+str(s),(s*.094,.002,.139),.019,.003,red,axis='X')
    for i in range(3):
        tube('Temple radial seam '+str((s,i)),[(s*.096,-.011+i*.009,.127),(s*.096,-.008+i*.007,.149)],.0008,gap)
    # Jaw hydraulic rails and recessed vents.
    tube('Jaw titanium actuator '+str(s),[(s*.062,-.028,.021),(s*.074,-.025,.071)],.003,ti)
    for i in range(4):
        z=.037+i*.006
        blend=(z-.027)/(.062-.027)
        inner=.040+(.052-.040)*blend
        outer=.058+(.076-.058)*blend
        front=-.080+(-.082+.080)*blend
        tube('Jaw cooling vent '+str((s,i)),[
            (s*(inner+(outer-inner)*t),front+.052*t-.0015,z)
            for t in [.28,.52,.78]],.001,gap)

face('Gold separate mechanical chin',[(.029,.004,-.075,.004,0),(.033,.007,-.084,.006,0),(.036,.025,-.095,.008,0),(.034,.03,-.095,.008,0)],gold,thickness=.004,smooth=1)
tube('Chin separation seam',[(-.033,-.087,.031),(0,-.099,.032),(.033,-.087,.031)],.0012,gap)
for i in range(3):
    z=.009+i*.018
    y=.080+i*.008
    face('Rear segmented nape plate '+str(i),[
        (.038,z,y,-.013,0),(.043,z+.003,y+.002,-.014,0),
        (.043,z+.014,y+.006,-.015,0),(.039,z+.017,y+.006,-.015,0)],red,thickness=.003,smooth=1)

# Validate helmet-scale bounds and finite geometry before export or rendering.
bpy.context.view_layer.update()
deps=bpy.context.evaluated_depsgraph_get()
points=[o.matrix_world@Vector(c) for o in S.objects if o.type=='MESH' for c in o.evaluated_get(deps).bound_box]
dimensions=[max(p[i] for p in points)-min(p[i] for p in points) for i in range(3)]
assert .24<dimensions[2]<.28,dimensions
assert .17<dimensions[0]<.23,dimensions
assert all(math.isfinite(c) for o in S.objects if o.type=='MESH' for v in o.data.vertices for c in v.co)
S['helmet_dimensions_m']=dimensions
S['review_status']='HELMET ONLY - awaiting approval before body work'
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(OUT/'helmet.glb'),export_format='GLB',use_selection=True,export_apply=True,export_animations=False)

S.render.engine='CYCLES';S.cycles.samples=64;S.cycles.use_denoising=True
S.render.film_transparent=True
S.world.use_nodes=True
S.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.13,.16,.20,1)
S.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.3
S.view_settings.view_transform='AgX'
def aim(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
for name,pos,power,size,col in [('Key',(-.45,-.65,.65),18,.45,(1,.88,.72)),('Fill',(.4,-.3,.25),7,.45,(.70,.84,1)),('Rim',(.2,.45,.5),22,.4,(1,.82,.64))]:
    bpy.ops.object.light_add(type='AREA',location=pos)
    lamp=bpy.context.object;lamp.name=name;lamp.data.energy=power;lamp.data.shape='DISK';lamp.data.size=size;lamp.data.color=col;aim(lamp,(0,0,.13))
bpy.ops.object.camera_add(location=(0,-.8,.145))
camera=bpy.context.object;camera.name='Helmet review camera';camera.data.type='ORTHO';camera.data.ortho_scale=.33
S.camera=camera
S.render.resolution_x=800;S.render.resolution_y=800;S.render.resolution_percentage=100
aim(camera,(0,0,.13))
# Save the completed component before any render begins.
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'helmet.blend'))
for name,pos in [('front',(0,-.8,.14)),('three-quarter',(.42,-.8,.23)),('back',(.25,.8,.19))]:
    camera.location=pos;aim(camera,(0,0,.13));S.render.filepath=str(OUT/f'{name}.png');bpy.ops.render.render(write_still=True)
print('HELMET_REVIEW_COMPLETE',OUT,'dimensions_m',dimensions)

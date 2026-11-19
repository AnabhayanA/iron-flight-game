"""Rebuild the original AUREL suit with Blender --background --python this_file."""
import bpy
import math
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'app/static/models'
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

def material(name, color, metal=0.0, emission=0.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Metallic'].default_value = metal
    p.inputs['Roughness'].default_value = .3
    p.inputs['Emission Color'].default_value = (*color, 1)
    p.inputs['Emission Strength'].default_value = emission
    return m

red = material('Ceramic crimson', (.48, .018, .035), .7)
gold = material('Brushed champagne alloy', (.83, .46, .10), .8)
dark = material('Graphite joint seals', (.025, .035, .05), .5)
light = material('Ion cyan emission', (.12, .8, 1), .15, 6)

def pivot(name, pos, parent=None):
    o = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(o)
    o.location = pos
    o.parent = parent
    return o

root = pivot('AUREL_Root', (0, 0, 0))

def plate(name, pos, size, mat, parent=root, bevel=.04):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.object
    o.name = name
    o.parent = parent
    o.location = pos
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    mod = o.modifiers.new('Machined edges', 'BEVEL')
    mod.width = bevel
    mod.segments = 2
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier=mod.name)
    o.data.materials.append(mat)
    return o

def sphere(name, pos, size, mat, parent=root):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6)
    o = bpy.context.object
    o.name = name
    o.parent = parent
    o.location = pos
    o.scale = size
    o.data.materials.append(mat)
    return o

def ring(name, pos, radius, depth, mat, parent=root, front=True):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=radius, depth=depth)
    o = bpy.context.object
    o.name = name
    o.parent = parent
    o.location = pos
    if front:
        o.rotation_euler.x = math.pi / 2
    o.data.materials.append(mat)
    return o

plate('Thorax core', (0, 0, 1.53), (.68, .36, .54), dark)
for s in [-1, 1]:
    o = plate('Split swept breastplate', (s*.19, -.17, 1.64), (.35, .14, .31), red)
    o.rotation_euler.y = s * -.18
    plate('Clavicle gold rail', (s*.19, -.25, 1.78), (.3, .05, .055), gold)
    plate('Dorsal thruster', (s*.23, .22, 1.58), (.16, .18, .4), red)
    ring('Dorsal exhaust', (s*.23, .23, 1.35), .055, .03, light, front=False)
ring('Hex reactor bezel', (0, -.265, 1.59), .13, .07, gold)
ring('Reactor graphite inset', (0, -.31, 1.59), .102, .025, dark)
ring('Ion reactor', (0, -.329, 1.59), .077, .018, light)
for z in [1.23, 1.31, 1.39]:
    plate('Overlapping abdominal lamella', (0, -.05, z), (.40, .3, .065), red)
plate('Pelvis girdle', (0, 0, 1.12), (.49, .32, .17), gold)
plate('Pelvis central shield', (0, -.18, 1.08), (.23, .08, .22), red)
head = pivot('Helmet_Pivot', (0, 0, 1.86), root)
ring('Neck bearing', (0, 0, 0), .115, .13, dark, head, False)
plate('Helmet armored shell', (0, 0, .22), (.38, .34, .42), red, head, .075)
plate('Faceted gold visor', (0, -.178, .23), (.29, .07, .27), gold, head, .055)
plate('Single split brow visor', (0, -.222, .27), (.27, .018, .042), dark, head, .009)
for s in [-1, 1]:
    o = plate('Cyan optical slit', (s*.078, -.235, .28), (.10, .014, .018), light, head, .003)
    o.rotation_euler.y = s * -.16
    ring('Helmet temple bearing', (s*.193, 0, .22), .066, .03, gold, head)
plate('Visor central ridge', (0, -.24, .19), (.04, .025, .19), gold, head, .008)

arms, elbows, hips, knees = [], [], [], []
for s, side in [(-1, 'L'), (1, 'R')]:
    arm = pivot('Shoulder_'+side, (s*.43, 0, 1.72), root)
    arms.append(arm)
    sphere('Shoulder bearing '+side, (0, 0, 0), (.13, .13, .13), dark, arm)
    plate('Floating pauldron '+side, (s*.025, 0, .025), (.28, .38, .22), red, arm)
    plate('Pauldron gold crest '+side, (s*.04, -.195, .05), (.18, .03, .06), gold, arm)
    plate('Upper arm '+side, (0, 0, -.23), (.19, .23, .3), gold, arm)
    elbow = pivot('Elbow_'+side, (0, 0, -.42), arm)
    elbows.append(elbow)
    sphere('Elbow bearing '+side, (0, 0, 0), (.10, .11, .10), dark, elbow)
    plate('Forearm vambrace '+side, (0, -.015, -.19), (.24, .27, .31), red, elbow)
    plate('Forearm accent '+side, (0, -.158, -.18), (.10, .025, .21), gold, elbow)
    hand = pivot('Wrist_'+side, (0, 0, -.40), elbow)
    plate('Palm armor '+side, (0, 0, -.055), (.19, .15, .17), red, hand)
    ring('Palm repulsor bezel '+side, (0, -.085, -.05), .063, .025, gold, hand)
    ring('Palm repulsor '+side, (0, -.105, -.05), .043, .015, light, hand)
    for f in range(4):
        plate('Finger '+side+str(f), ((f-1.5)*.045, -.005, -.17), (.035, .11, .095), gold, hand, .009)
    hip = pivot('Hip_'+side, (s*.16, 0, 1.08), root)
    hips.append(hip)
    sphere('Hip bearing '+side, (0, 0, -.02), (.12, .12, .12), dark, hip)
    plate('Thigh armor '+side, (0, 0, -.22), (.25, .29, .38), red, hip)
    plate('Thigh gold inlay '+side, (s*.06, -.155, -.22), (.09, .025, .27), gold, hip)
    knee = pivot('Knee_'+side, (0, 0, -.46), hip)
    knees.append(knee)
    sphere('Knee bearing '+side, (0, 0, 0), (.10, .11, .10), dark, knee)
    plate('Knee shield '+side, (0, -.12, 0), (.22, .10, .15), gold, knee)
    plate('Shin greave '+side, (0, 0, -.23), (.23, .27, .35), red, knee)
    plate('Shin raised spine '+side, (0, -.15, -.23), (.10, .05, .28), gold, knee)
    foot = pivot('Ankle_'+side, (0, 0, -.44), knee)
    plate('Boot '+side, (0, -.075, -.02), (.26, .41, .16), red, foot)
    ring('Boot repulsor '+side, (0, -.03, -.105), .08, .025, light, foot, False)

# Rigid joint hierarchy retains clean armor deformation and exports as animated nodes.
def pose(shoot=False):
    for o in arms+elbows+hips+knees:
        o.rotation_euler = (0, 0, 0)
    arms[0].rotation_euler.y = -.14
    arms[1].rotation_euler.y = .14
    if shoot:
        arms[1].rotation_euler.y = -1.05
        arms[1].rotation_euler.x = .35
        elbows[1].rotation_euler.y = -.35
    else:
        elbows[0].rotation_euler.x = -.22
        elbows[1].rotation_euler.x = -.22
    hips[0].rotation_euler.x = -.12
    knees[0].rotation_euler.x = .24

scene = bpy.context.scene
scene.render.fps = 24
for frame, shooting in [(1, False), (24, False), (32, True), (48, True), (56, False)]:
    pose(shooting)
    root.location.z = .025 if frame == 24 else 0
    for o in [root]+arms+elbows+hips+knees:
        o.keyframe_insert(data_path='rotation_euler', frame=frame)
        o.keyframe_insert(data_path='location', frame=frame)
scene.frame_start, scene.frame_end = 1, 56
scene.frame_set(1)
bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
    if o.type in {'MESH', 'EMPTY'}:
        o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'aurel.glb'), export_format='GLB', use_selection=True, export_animations=True)

scene.render.engine = 'CYCLES'
scene.cycles.samples = 24
scene.render.film_transparent = True
scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.resolution_percentage = 100
scene.world.color = (.25, .25, .25)
def aim(o, target):
    o.rotation_euler = (Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(3.1, -7, 2.5))
camera = bpy.context.object
camera.name = 'Sprite camera'
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 2.9
aim(camera, (0, 0, 1.1))
scene.camera = camera
for pos, energy, size in [((1,-4,5), 750, 4), ((-3,-1,2), 550, 3), ((2,3,4), 1000, 3)]:
    bpy.ops.object.light_add(type='AREA', location=pos)
    lamp = bpy.context.object
    lamp.data.energy, lamp.data.shape, lamp.data.size = energy, 'DISK', size
    aim(lamp, (0,0,1))
for name, frame in [('hover', 1), ('fire', 40)]:
    scene.frame_set(frame)
    scene.render.filepath = str(OUT/f'aurel-{name}.png')
    bpy.ops.render.render(write_still=True)
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'aurel.blend'))
print('AUREL_BUILD_COMPLETE')

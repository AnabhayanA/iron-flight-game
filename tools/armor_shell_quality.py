"""Repair legacy loft topology without changing the armor's joint hierarchy."""
import bpy
import bmesh

def repair_shells(scene):
    repaired=0
    for obj in list(scene.objects):
        if obj.type!='MESH' or obj.get('shell_topology_repaired'):continue
        data=obj.data
        caps=[p for p in data.polygons if len(p.vertices)>8]
        if len(caps)!=2 or len(caps[0].vertices)!=len(caps[1].vertices):continue
        n=len(caps[0].vertices)
        if len(data.vertices)%n:continue
        rows=len(data.vertices)//n
        if rows<2:continue
        original=[v.co.copy() for v in data.vertices]
        closed=all((original[j*n]-original[j*n+n-1]).length<1e-5 for j in range(rows))
        count=n-1 if closed else n
        verts=[original[j*n+k] for j in range(rows) for k in range(count)]
        faces=[(j*count+k,j*count+(k+1)%count,(j+1)*count+(k+1)%count,(j+1)*count+k)
               for j in range(rows-1) for k in range(count if closed else count-1)]
        if closed:
            faces += [tuple(range(count-1,-1,-1)),tuple((rows-1)*count+k for k in range(count))]
        fresh=bpy.data.meshes.new(data.name+'_clean_shell')
        fresh.from_pydata(verts,[],faces);fresh.update()
        for mat in data.materials:fresh.materials.append(mat)
        bm=bmesh.new();bm.from_mesh(fresh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(fresh);bm.free()
        for poly in fresh.polygons:poly.use_smooth=len(poly.vertices)==4
        obj.data=fresh
        if not closed:
            mod=obj.modifiers.new('Physical armor shell thickness','SOLIDIFY');mod.thickness=.0025;mod.offset=-1
            mod=obj.modifiers.new('Rounded shell perimeter','BEVEL');mod.width=.0007;mod.segments=2
        obj['shell_topology_repaired']=True
        repaired+=1
    return repaired

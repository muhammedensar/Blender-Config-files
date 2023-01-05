import bpy
import bmesh

from mathutils import Vector, Matrix

from ..... utility import addon, mesh
from ..... utility.modifier import apply, sort, new, unmodified_bounds, bevels, move_to_index

sort_types = [
    'ARRAY',
    'MIRROR',
    'BEVEL',
    'SOLIDIFY',
    'DISPLACE',
    'LATTICE',
    'DECIMATE'
    'SCREW',
]

if bpy.app.version[:2] >= (2, 82):
    sort_types.insert(4, 'WELD')


def shape_bool(obj):
    bc = bpy.context.scene.bc

    if obj:
        for mod in reversed(obj.modifiers):
            if mod.type == 'BOOLEAN' and mod.object == bc.shape and (not hasattr(mod, 'operand_type') or mod.operand_type != 'COLLECTION'):
                return mod

    return None


def update(op, context, force_edit_mode=True):
    bc = context.scene.bc
    original_active = context.active_object

    slices = op.datablock['slices']
    targets = op.datablock['targets']

    if not op.datablock['overrides']:
        bpy.ops.mesh.select_all(action='DESELECT')
        overrides = targets + slices

        for obj in overrides:
            bm = bmesh.from_edit_mesh(obj.data)
            obj.update_from_editmode()

        op.datablock['overrides'] = [obj.data.copy() for obj in overrides]

        for obj in op.datablock['slices']:
            for mod in obj.modifiers:
                if mod.type == 'BOOLEAN' and mod.object == bc.shape:
                    mod.show_viewport = True

    evaluated_objs = []

    evaluated = bc.shape.evaluated_get(context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    evaluated_objs.append(evaluated)

    for poly in mesh.polygons:
        poly.select = True

    for index, obj in enumerate(targets):
        override = op.datablock['overrides'][index]

        bm = bmesh.from_edit_mesh(obj.data)
        cutter_mesh = mesh
        matrix = obj.matrix_world.inverted() @ bc.shape.matrix_world

        if op.mode == 'INSET':
            evaluated = op.datablock['insets'][index].evaluated_get(context.evaluated_depsgraph_get())
            cutter_mesh = evaluated.to_mesh()
            matrix = Matrix()

            for poly in cutter_mesh.polygons:
                poly.select = True

            evaluated_objs.append(evaluated)

        bmesh.ops.delete(bm, geom=bm.verts, context='VERTS')

        bm.from_mesh(cutter_mesh)

        bevel = bm.edges.layers.bevel_weight.verify()

        for edge in bm.edges:
            edge[bevel] = False

        bmesh.ops.transform(bm, matrix=matrix, verts=bm.verts)
        bm.from_mesh(override)
        bm.faces.active = None # XXX: prevents active face flicker
        bmesh.update_edit_mesh(obj.data)

    operation = 'UNION' if op.mode == 'JOIN' else 'INTERSECT'

    if op.mode in {'CUT', 'INSET', 'SLICE', 'EXTRACT'}:
        operation = 'DIFFERENCE'

    # elif op.mode == 'JOIN':
    #     operation = 'UNION'

    # elif op.mode == 'INTERSECT':
    #     operation = 'INTERSECT'

    if bpy.app.version[:2] < (2, 91):
        bpy.ops.mesh.intersect_boolean(operation=operation)
    else:
        bpy.ops.mesh.intersect_boolean(operation=operation, solver='FAST')

    if op.mode in {'SLICE', 'EXTRACT', 'INSET'}:
        evaluated = bc.shape.evaluated_get(context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()

        for poly in mesh.polygons:
            poly.select = True

        overrides = op.datablock['overrides'][len(slices)-1:]

        for index, obj in enumerate(slices):
            override = overrides[index]

            bm = bmesh.from_edit_mesh(obj.data)
            cutter_mesh = mesh
            matrix = obj.matrix_world.inverted() @ bc.shape.matrix_world

            if op.mode == 'INSET':
                evaluated = op.datablock['insets'][index].evaluated_get(context.evaluated_depsgraph_get())
                cutter_mesh = evaluated.to_mesh()
                matrix = Matrix()

                for poly in cutter_mesh.polygons:
                    poly.select = True

                evaluated_objs.append(evaluated)

            bmesh.ops.delete(bm, geom=bm.verts, context='VERTS')

            bm.from_mesh(cutter_mesh)

            bevel = bm.edges.layers.bevel_weight.verify()

            for edge in bm.edges:
                edge[bevel] = False

            bmesh.ops.transform(bm, matrix=matrix, verts=bm.verts)
            bm.from_mesh(override)
            bm.faces.active = None # XXX: prevents active face flicker
            bmesh.update_edit_mesh(obj.data)

        if bpy.app.version[:2] < (2, 91):
            bpy.ops.mesh.intersect_boolean(operation='INTERSECT')

        else:
            bpy.ops.mesh.intersect_boolean(operation='INTERSECT', solver='FAST')

    for obj in evaluated_objs:
        obj.to_mesh_clear()

    context.view_layer.objects.active = original_active

    if not force_edit_mode:
        bpy.ops.object.mode_set(mode='OBJECT')


def clean(op, modifier_only=False):
    for obj in op.datablock['targets']:
        if shape_bool(obj):
            obj.modifiers.remove(shape_bool(obj))

    if not modifier_only:
        for obj in op.datablock['slices']:
            bpy.data.meshes.remove(obj.data)

        for obj in op.datablock['insets']:
            bpy.data.meshes.remove(obj.data)

        op.datablock['slices'] = list()
        op.datablock['insets'] = list()


# TODO: move array here
class create:


    def __init__(self, op):
        self.boolean(op)


    @staticmethod
    def boolean(op, show=False):
        wm = bpy.context.window_manager
        preference = addon.preference()
        bc = bpy.context.scene.bc

        if not op.datablock['targets'] or (not op.live and not show):
            return

        if shape_bool(op.datablock['targets'][0]):
            for obj in op.datablock['targets']:
                if shape_bool(obj):
                    obj.modifiers.remove(shape_bool(obj))

            for obj in op.datablock['slices']:
                bpy.data.meshes.remove(obj.data)

            for obj in op.datablock['insets']:
                bpy.data.meshes.remove(obj.data)

            op.datablock['slices'] = []
            op.datablock['insets'] = []

        bc.shape.display_type = 'WIRE' if op.mode != 'MAKE' else 'TEXTURED'
        bc.shape.hide_set(True)

        for obj in op.datablock['targets']:
            if not op.active_only or obj == bpy.context.view_layer.objects.active:
                mod = obj.modifiers.new(name='Boolean', type='BOOLEAN')

                if hasattr(mod, 'solver'):
                    mod.solver = addon.preference().behavior.boolean_solver

                mod.show_viewport = show
                mod.show_expanded = False

                if bpy.app.version[:2] >= (2, 91):
                    mod.show_in_editmode = True

                mod.object = bc.shape
                mod.operation = 'DIFFERENCE' if op.mode not in {'JOIN', 'INTERSECT'} else 'UNION' if op.mode == 'JOIN' else 'INTERSECT'

                if op.mode != 'EXTRACT' or (op.mode == 'EXTRACT' and not preference.behavior.surface_extract):
                    ignore_weight = preference.behavior.sort_bevel_ignore_weight
                    ignore_vgroup = preference.behavior.sort_bevel_ignore_vgroup
                    ignore_verts = preference.behavior.sort_bevel_ignore_only_verts
                    props = {'use_only_vertices': True} if bpy.app.version[:2] < (2, 90) else {'affect': 'VERTICES'}
                    bvls = bevels(obj, weight=ignore_weight, vertex_group=ignore_vgroup, props=props if ignore_verts else {})
                    sort(obj, option=preference.behavior, ignore=bvls, sort_depth=preference.behavior.sort_depth)
                else:
                    sort(obj, sort_types={'WEIGHTED_NORMAL'})

                if op.mode in {'INSET', 'SLICE', 'EXTRACT'}:
                    new = obj.copy()
                    new.data = obj.data.copy()

                    if op.mode in {'SLICE', 'EXTRACT'}:
                        if obj.users_collection:
                            for collection in obj.users_collection:
                                if bpy.context.scene.rigidbody_world and collection == bpy.context.scene.rigidbody_world.collection:
                                    continue

                                collection.objects.link(new)
                        else:
                            bpy.context.scene.collection.objects.link(new)

                        bc.slice = new

                    else:
                        bc.collection.objects.link(new)
                        new.bc.inset = True

                    new.select_set(True)

                    new.name = op.mode.title()
                    new.data.name = op.mode.title()

                    if op.mode == 'SLICE' and preference.behavior.recut:
                        for mod in new.modifiers:
                            if mod.type == 'BOOLEAN' and mod != shape_bool(new):
                                new.modifiers.remove(mod)

                    if op.mode not in {'SLICE', 'EXTRACT'}:
                        new.hide_set(True)

                    shape_bool(new).operation = 'INTERSECT'

                    if op.mode == 'INSET':
                        if op.original_mode == 'EDIT_MESH' or preference.behavior.recut:
                            new.modifiers.clear()

                        else:
                            for mod in reversed(new.modifiers):
                                if mod.type == 'BOOLEAN' and mod.object == bc.shape:
                                    new.modifiers.remove(mod)
                                    break
                                new.modifiers.remove(mod)

                            apply(new)

                    if op.mode == 'INSET':
                        new.display_type = 'WIRE'
                        new.hide_render = True
                        # new.data.use_customdata_vertex_bevel = False
                        # new.data.use_customdata_edge_bevel = False
                        # new.data.use_customdata_edge_crease = False

                        if hasattr(new, 'cycles_visibility'):
                            new.cycles_visibility.camera = False
                            new.cycles_visibility.diffuse = False
                            new.cycles_visibility.glossy = False
                            new.cycles_visibility.transmission = False
                            new.cycles_visibility.scatter = False
                            new.cycles_visibility.shadow = False
                            new.cycles.is_shadow_catcher = False
                            new.cycles.is_holdout = False

                        solidify = new.modifiers.new(name='Solidify', type='SOLIDIFY')
                        solidify.thickness = op.last['thickness']
                        solidify.offset = 0
                        solidify.show_on_cage = True
                        solidify.use_even_offset = True
                        solidify.use_quality_normals = True

                        default_boolean = shape_bool(new)

                        if default_boolean:
                            new.modifiers.remove(default_boolean)

                        mod = new.modifiers.new(name='Boolean', type='BOOLEAN')
                        mod.show_viewport = show
                        mod.show_expanded = False
                        if bpy.app.version[:2] >= (2, 91):
                            mod.show_in_editmode = True
                        mod.object = bc.shape
                        mod.operation = 'INTERSECT'

                        for mod in bc.shape.modifiers:
                            if mod.type == 'SOLIDIFY':
                                bc.shape.modifiers.remove(mod)

                        bool = None
                        for mod in reversed(obj.modifiers):
                            if mod.type == 'BOOLEAN' and mod.object == new:
                                bool = mod
                                break

                        if not bool:
                            mod = obj.modifiers.new(name='Boolean', type='BOOLEAN')

                            if hasattr(mod, 'solver'):
                                mod.solver = addon.preference().behavior.boolean_solver

                            mod.show_viewport = show
                            mod.show_expanded = False
                            if bpy.app.version[:2] >= (2, 91):
                                mod.show_in_editmode = True
                            mod.object = new
                            mod.operation = 'DIFFERENCE'

                            if hasattr(wm, 'Hard_Ops_material_options'):
                                new.hops.status = 'BOOLSHAPE'

                            ignore_weight = preference.behavior.sort_bevel_ignore_weight
                            ignore_vgroup = preference.behavior.sort_bevel_ignore_vgroup
                            ignore_verts = preference.behavior.sort_bevel_ignore_only_verts
                            props = {'use_only_vertices': True} if bpy.app.version[:2] < (2, 90) else {'affect': 'VERTICES'}
                            bvls = bevels(obj, weight=ignore_weight, vertex_group=ignore_vgroup, props=props if ignore_verts else {})
                            sort(obj, option=preference.behavior, ignore=bvls, sort_depth=preference.behavior.sort_depth)

                        bc.inset = new

                        for mod in bc.inset.modifiers:
                            if mod.type == 'WEIGHTED_NORMAL':
                                bc.inset.modifiers.remove(mod)

                        original_active = bpy.context.active_object
                        bpy.context.view_layer.objects.active = new
                        bpy.ops.mesh.customdata_custom_splitnormals_clear()
                        bpy.context.view_layer.objects.active = original_active

                        if preference.behavior.inset_slice:
                            slice_inset = obj.copy()
                            slice_inset.data = obj.data.copy()

                            for mod in slice_inset.modifiers:
                                if mod.type == 'BOOLEAN':
                                    if mod.object is new:
                                        mod.operation = 'INTERSECT'

                                    elif mod.object == bc.shape:
                                        slice_inset.modifiers.remove(mod)

                            for col in obj.users_collection:
                                col.objects.link(slice_inset)

                            op.datablock['slices'].append(slice_inset)

                    if op.mode == 'INSET':
                        op.datablock['insets'].append(new)

                    else:
                        op.datablock['slices'].append(new)

        hops = getattr(wm, 'Hard_Ops_material_options', False)

        if not len(bpy.data.materials[:]):
            hops = False

        if hops and hops.active_material:
            active_material = bpy.data.materials[hops.active_material]

            bc.shape.data.materials.clear()

            if op.mode not in {'SLICE', 'INSET', 'KNIFE', 'EXTRACT'}:
                bc.shape.data.materials.append(active_material)

                if op.mode != 'MAKE':
                    for obj in op.datablock['targets']:
                        mats = [slot.material for slot in obj.material_slots if slot.material]

                        obj.data.materials.clear()

                        for index, mat in enumerate(mats):
                            if not index or (mat != active_material or mat in op.existing[obj]['materials']):
                                obj.data.materials.append(mat)

                        if active_material not in obj.data.materials[:]:
                            obj.data.materials.append(active_material)

            elif op.mode in {'SLICE', 'INSET'}:
                for obj in op.datablock['targets']:
                    mats = [slot.material for slot in obj.material_slots if slot.material]

                    obj.data.materials.clear()

                    for index, mat in enumerate(mats):
                        if not index or (mat != active_material or mat in op.existing[obj]['materials']):
                            obj.data.materials.append(mat)

                    if op.mode == 'INSET' and active_material not in obj.data.materials[:]:
                        obj.data.materials.append(active_material)

                for obj in op.datablock['slices']:
                    obj.data.materials.clear()
                    obj.data.materials.append(active_material)

                for obj in op.datablock['insets']:
                    obj.data.materials.append(active_material)
                    mats = [slot.material for slot in obj.material_slots]
                    index = mats.index(active_material)

                    for mod in obj.modifiers:
                        if mod.type == 'SOLIDIFY':
                            mod.material_offset = index

                            break

        # XXX: ensure edit mode state
        if op.datablock['slices'] and op.original_mode == 'EDIT_MESH':
            for obj in op.datablock['slices']:
                obj.select_set(True)

            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.mode_set(mode='EDIT')

import bpy
import bmesh

from mathutils import *

from . import addon, lattice, mesh, modal, modifier

from .. import topbar


def create(ot, context, event, custom=None):
    mesh.create.shape(ot, context, event)
    lattice.create(ot, context, event)

    if custom:
        modal.cutter.cycle(ot, context, event, custom=custom)


def clean(ot, context, all=False):
    preference = addon.preference()
    bc = bpy.context.window_manager.bc
    type_to_custom = False

    for obj in context.selected_objects:
        obj.select_set(False)

    bc.shape.hide_set(False)
    bc.lattice.hide_set(False)

    context.view_layer.objects.active = bc.shape
    bc.shape.select_set(True)

    bpy.ops.object.mode_set(mode='EDIT')
    context.view_layer.update()
    bpy.ops.object.mode_set(mode='OBJECT')

    if not ot.live and ot.mode in {'CUT', 'SLICE', 'INSET', 'JOIN', 'EXTRACT'}:
        modifier.create.boolean(ot, show=True)

    for mod in bc.shape.modifiers:
        mod.show_viewport = True

        if mod.type == 'BEVEL':
            preference.shape['bevel_segments'] = mod.segments

    for obj in ot.datablock['targets']:
        for mod in obj.modifiers:
            if mod.type == 'BOOLEAN':
                mod.show_viewport = True

    for obj in ot.datablock['slices']:
        for mod in obj.modifiers:
            if mod.type == 'BOOLEAN':
                mod.show_viewport = True

    keep_modifiers = [type for type in ('ARRAY', 'BEVEL', 'SOLIDIFY', 'SCREW', 'MIRROR', 'LATTICE') if getattr(preference.behavior, F'keep_{type.lower()}')] if preference.behavior.keep_modifiers else []
    modifier.apply(bc.shape, exclude=[mod for mod in bc.shape.modifiers if mod.type in keep_modifiers], hard_apply=False)

    if ot.lazorcut:
        if ot.mode not in {'MAKE', 'KNIFE'} and ot.original_mode == 'EDIT_MESH':
            modifier.update(ot, bpy.context)

        elif ot.mode == 'KNIFE':
            if not ot.align_to_view:
                ot.extruded = True
                mesh.knife(ot, bpy.context, None)

            else:
                all = True

                modifier.apply(bc.shape)

                bpy.ops.object.mode_set(mode='EDIT')

                original_selection_mode = tuple(bpy.context.tool_settings.mesh_select_mode)

                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.remove_doubles(threshold=0.0006)

                bpy.ops.object.mode_set(mode='OBJECT')

                for obj in ot.datablock['targets']:
                    context.view_layer.objects.active = obj
                    obj.select_set(True)

                    context.view_layer.update()

                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.knife_project(cut_through=True)
                    bpy.ops.object.mode_set(mode='OBJECT')

                    obj.select_set(False)

                context.view_layer.objects.active = bc.shape

                if ot.original_mode == 'EDIT_MESH':
                    bpy.ops.object.mode_set(mode='EDIT')

                    bpy.context.tool_settings.mesh_select_mode = original_selection_mode

    modal.bevel_modifiers = list()

    if not all:
        if ot.mode == 'EXTRACT':
            type_to_custom = True
            for obj in ot.datablock['targets']:
                for mod in obj.modifiers:
                    if mod.type == 'BOOLEAN' and mod.object == bc.shape:
                        obj.modifiers.remove(mod)

            slice_duplicates = []
            for obj in ot.datablock['slices']:

                for mod in obj.modifiers:
                    if mod.type in {'BEVEL', 'MIRROR'}:
                        obj.modifiers.remove(mod)

                bpy.context.view_layer.update()

                new = obj.copy()
                slice_duplicates.append(new)
                obj.data = obj.data.copy()

                bc.collection.objects.link(new)

                modifier.apply(obj, hard_apply=False)

            for obj in slice_duplicates:
                for mod in obj.modifiers:
                    if mod.type == 'BOOLEAN' and mod.operation != 'INTERSECT':
                        obj.modifiers.remove(mod)

            for obj in slice_duplicates:
                modifier.apply(obj, hard_apply=False)

            for obj in slice_duplicates:
                center = 0.125 * sum((obj.matrix_world @ Vector(bound) for bound in obj.bound_box), Vector())
                obj.location = center
                obj.data.transform(Matrix.Translation(-center))
                obj.data.transform(Matrix.Scale(0.998, 4, Vector((-1, 0, 0)) ) )
                obj.data.transform(Matrix.Scale(0.998, 4, Vector((0, -1, 0)) ) )
                obj.data.transform(Matrix.Scale(0.998, 4, Vector((0, 0, -1)) ) )

            me = bpy.data.meshes.new(name='Extraction')

            bm = bmesh.new()

            for obj in slice_duplicates:
                obj.data.transform(Matrix.Translation(obj.location))
                bm.from_mesh(obj.data)

            bm.to_mesh(me)
            bm.free()

            for obj in slice_duplicates:
                bpy.data.objects.remove(obj)

            obj = bpy.data.objects.new(name='Extraction', object_data=me)
            bc.collection.objects.link(obj)

            # for face in obj.data.polygons:
            #     face.use_smooth = True
            #
            # obj.data.use_auto_smooth = True
            # obj.data.use_customdata_vertex_bevel = True
            # obj.data.use_customdata_edge_bevel = True
            # obj.data.use_customdata_edge_crease = True

            for slice in ot.datablock['slices']:
                mod = obj.modifiers.new(name='Boolean', type='BOOLEAN')
                mod.operation = 'DIFFERENCE'
                mod.object = slice

            modifier.apply(obj, hard_apply=False)

            bpy.context.view_layer.update()

            if sum(obj.dimensions) > 0.001:
                bc.stored_shape = obj
                obj.data.transform(bc.shape.matrix_world.inverted())
                obj.location = Vector((0, 0, 0))

                bpy.context.view_layer.update()

                center = 0.125 * sum((obj.matrix_world @ Vector(bound) for bound in obj.bound_box), Vector())
                obj.location = center
                obj.data.transform(Matrix.Translation(-center))

                obj.location = Vector((0, 0, 0))

            else:
                bpy.data.objects.remove(obj)

            bpy.data.objects.remove(bc.shape)
            bc.shape = None

            for obj in ot.datablock['slices']:
                bpy.data.objects.remove(obj)

            if bc.original_active:
                bpy.context.view_layer.objects.active = bc.original_active

            for obj in ot.original_selected:
                obj.select_set(True)

        elif ot.mode != 'KNIFE':
            if ot.mode != 'MAKE':
                if ot.original_mode != 'EDIT_MESH':
                    if ot.shape_type in {'CIRCLE', 'NGON'}:
                        bpy.ops.object.mode_set(mode='EDIT')
                        original_selection_mode = tuple(bpy.context.tool_settings.mesh_select_mode)
                        bpy.context.tool_settings.mesh_select_mode = (True, False, False)
                        bpy.ops.mesh.select_all(action='SELECT')
                        bpy.ops.mesh.remove_doubles(threshold=0.0006)

                        if bc.cyclic or ot.shape_type == 'CIRCLE':
                            bpy.ops.mesh.normals_make_consistent(inside=False)

                        bpy.ops.mesh.dissolve_limited(angle_limit=0.008, use_dissolve_boundaries=False, delimit={'NORMAL'})
                        bpy.context.tool_settings.mesh_select_mode = original_selection_mode
                        bpy.ops.object.mode_set(mode='OBJECT')

                        # bpy.context.view_layer.update()

                    if ot.behavior != 'DESTRUCTIVE':
                        bc.shape.bc.applied = True

            else:
                # TODO: if in edit mode join made geo with active object
                bc.collection.objects.unlink(bc.shape)

                if bc.original_active and bc.original_active.users_collection:
                    for collection in bc.original_active.users_collection:
                        collection.objects.link(bc.shape)
                else:
                    bpy.context.scene.collection.objects.link(bc.shape)

                bpy.context.view_layer.objects.active = bc.shape

                if ot.shape_type in {'CIRCLE', 'NGON'}:
                    bpy.ops.object.mode_set(mode='EDIT')
                    original_selection_mode = tuple(bpy.context.tool_settings.mesh_select_mode)
                    bpy.context.tool_settings.mesh_select_mode = (True, False, False)
                    bpy.ops.mesh.select_all(action='SELECT')
                    bpy.ops.mesh.remove_doubles(threshold=0.0006)
                    bpy.ops.mesh.normals_make_consistent(inside=False)
                    bpy.ops.mesh.dissolve_limited(angle_limit=0.008, use_dissolve_boundaries=False, delimit={'NORMAL'})
                    bpy.context.tool_settings.mesh_select_mode = original_selection_mode
                    bpy.ops.object.mode_set(mode='OBJECT')

                    # bpy.context.view_layer.update()

                bc.shape.name = ot.shape_type.title()
                bc.shape.data.name = ot.shape_type.title()
                bc.shape.bc.applied = True
                bc.shape.hide_render = False
                bc.shape.hide_set(False)

                if hasattr(bc.shape, 'cycles_visibility'):
                    bc.shape.cycles_visibility.camera = True
                    bc.shape.cycles_visibility.diffuse = True
                    bc.shape.cycles_visibility.glossy = True
                    bc.shape.cycles_visibility.transmission = True
                    bc.shape.cycles_visibility.scatter = True
                    bc.shape.cycles_visibility.shadow = True

            if ot.show_shape:

                if not preference.behavior.make_active and ot.datablock['targets']:
                    bpy.context.view_layer.objects.active = bc.original_active
                    bc.original_active.select_set(True)

                else:
                    bc.shape.select_set(True)

                    for obj in bpy.context.visible_objects:
                        if obj != bc.shape:
                            obj.select_set(False)
                        elif not bc.original_active:
                            bpy.context.view_layer.objects.active = obj
                            obj.select_set(True)

                if ot.original_mode == 'EDIT_MESH' and ot.datablock['targets']:
                    for pair in zip(ot.datablock['targets'], ot.datablock['overrides']):
                        obj = pair[0]
                        override = pair[1]

                        bpy.context.view_layer.objects.active = obj
                        name = obj.data.name
                        obj.data.name = 'tmp'

                        obj.data = override
                        obj.data.name = name

                    bpy.context.view_layer.objects.active = bc.shape

                    ot.datablock['overrides'] = list()
            else:
                if ot.mode != 'MAKE':
                    bc.shape.hide_set(True)

                    if ot.mode == 'INSET':
                        for obj in ot.datablock['slices']:
                            obj.hide_set(True)

                    if ot.original_mode == 'EDIT_MESH':
                        for obj in ot.datablock['slices']:
                            obj.select_set(True)

                if ot.datablock['targets']:

                    bpy.context.view_layer.objects.active = bc.original_active
                    bc.original_active.select_set(True)

                    bpy.ops.object.mode_set(mode='OBJECT')

                    for obj in ot.original_selected:
                        obj.select_set(True)

                    if ot.behavior == 'DESTRUCTIVE' and ot.original_mode != 'EDIT_MESH':
                        for obj in ot.datablock['targets']:
                            for mod in obj.modifiers:
                                if ot.mode == 'INSET' and mod.type == 'BOOLEAN' and mod.object == bc.shape:
                                    obj.modifiers.remove(mod)

                        for obj in ot.datablock['targets']:
                            modifier.apply(obj, mod=modifier.shape_bool(ot, obj))

                            if ot.mode == 'INSET':
                                for mod in obj.modifiers:
                                    if mod.type == 'BOOLEAN' and mod.object in ot.datablock['slices']:
                                        modifier.apply(obj, mod=mod)

                        for obj in ot.datablock['slices']:
                            modifier.apply(obj, mod=modifier.shape_bool(ot, obj), hard_apply=False)

                        bpy.data.objects.remove(bc.shape)

                        for obj in ot.datablock['slices']:
                            if ot.mode == 'INSET':
                                bpy.data.objects.remove(obj)
                            else:
                                obj.select_set(True)

                    elif ot.mode == 'SLICE' and (preference.behavior.apply_slices or ot.original_mode == 'EDIT_MESH'):
                        for obj in ot.datablock['slices']:
                            modifier.apply(obj, mod=modifier.shape_bool(ot, obj), hard_apply=False)
                            obj.select_set(True)

                    elif ot.mode == 'SLICE':
                        for obj in ot.datablock['slices']:
                            obj.select_set(True)

                    if ot.original_mode == 'EDIT_MESH':
                        for obj in ot.datablock['targets']:
                            for mod in obj.modifiers:
                                if mod.type == 'BOOLEAN':
                                    if mod.object == bc.shape or mod.object in ot.datablock['slices']:
                                        obj.modifiers.remove(mod)

                            bpy.ops.object.mode_set(mode='EDIT')

            if ot.mode == 'INSET':
                for obj in ot.datablock['targets']:
                    for mod in obj.modifiers:
                        if mod.type == 'BOOLEAN' and mod.object == bc.shape:
                            obj.modifiers.remove(mod)
        else:
            bpy.data.objects.remove(bc.shape)

            bpy.context.view_layer.objects.active = bc.original_active
            bc.original_active.select_set(True)

            for obj in ot.original_selected:
                obj.select_set(True)

            if ot.original_mode == 'EDIT_MESH':
                bpy.ops.object.mode_set(mode='EDIT')

        if not preference.behavior.keep_lattice:
            bpy.data.objects.remove(bc.lattice)

        else:
            bc.lattice.data.bc.removeable = False
            bc.lattice.hide_set(not ot.show_shape)

        bpy.data.objects.remove(ot.datablock['plane'])

        for me in bpy.data.meshes:
            if me.bc.removeable:
                bpy.data.meshes.remove(me)

        for lat in bpy.data.lattices:
            if lat.bc.removeable:
                bpy.data.lattices.remove(lat)

    else:
        if bc.original_active:
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.context.view_layer.objects.active = bc.original_active
            bc.original_active.select_set(True)

            if ot.cancelled:
                if ot.datablock['overrides']:
                    for pair in zip(ot.datablock['targets'], ot.datablock['overrides']):
                        obj = pair[0]
                        override = pair[1]

                        name = obj.data.name
                        obj.data.name = 'tmp'

                        obj.data = override
                        obj.data.name = name

                        for mod in obj.modifiers:
                            mod.show_viewport = True

                    ot.datablock['overrides'] = list()

        bpy.data.objects.remove(bc.shape)
        bpy.data.objects.remove(bc.lattice)

        for obj in ot.datablock['slices']:
            bpy.data.objects.remove(obj)

        for obj in ot.datablock['targets']:
            for mod in obj.modifiers:
                if mod.type == 'BOOLEAN' and not mod.object:

                    obj.modifiers.remove(mod)

        if ot.original_mode == 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='EDIT')

    for me in bpy.data.meshes:
        if me.bc.removeable:
            bpy.data.meshes.remove(me)

    for lat in bpy.data.lattices:
        if lat.bc.removeable:
            bpy.data.lattices.remove(lat)

    bc.lattice = None

    for obj in bpy.data.objects:
        for mod in obj.modifiers:
            if mod.type == 'BOOLEAN' and not mod.object:
                obj.modifiers.remove(mod)

        applied_cycle = (obj.bc.shape and obj.bc.shape != bc.shape and obj.bc.applied_cycle)
        if (obj.type == 'MESH' and obj.data.bc.removeable) or obj.users == 0 or applied_cycle:
            bpy.data.objects.remove(obj)

        elif obj.bc.shape and obj.bc.applied_cycle:
            obj.bc.applied = True
            obj.bc.applied_cycle = False

    bc.shape = None if not bc.stored_shape else bc.stored_shape

    bc.slice = None
    bc.inset = None
    bc.plane = None
    bc.location = Vector()

    for me in bpy.data.meshes:
        if me.users == 0:
            bpy.data.meshes.remove(me)

    if preference.surface != ot.last['surface']:
        preference.surface = ot.last['surface']

    if 'Cutters' in bpy.data.collections and not bc.collection.objects:
        bpy.data.collections.remove(bc.collection)

    if type_to_custom:
        topbar.change_prop(bpy.context, 'shape_type', 'CUSTOM')

    if ot.mode != 'KNIFE':
        topbar.change_prop(bpy.context, 'mode', ot.last['start_mode'] if not type_to_custom else 'CUT')

    topbar.change_prop(bpy.context, 'operation', ot.last['start_operation'])

    del ot.tool
    ot.original_selected = []
    ot.original_visible = []
    del ot.datablock
    del ot.last
    del ot.ray
    del ot.start
    del ot.geo
    del ot.mouse
    del ot.view3d

    modal.cutter.clear_sum()

    if ot.snap:
        ot.snap = False

        bpy.ops.bc.display_snap('INVOKE_DEFAULT')

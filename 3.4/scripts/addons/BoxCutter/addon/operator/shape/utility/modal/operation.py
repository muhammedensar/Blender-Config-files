import bpy
from mathutils import Matrix, Vector

from . import refresh, bevel

from ..... import toolbar

from ...... utility import addon, view3d, math
from .. import mesh, lattice
from ... import utility


def change(op, context, event, to='NONE', modified=True, init=False, clear_mods=[], dot=False):
    preference = addon.preference()
    bc = context.scene.bc
    op.modified = modified

    if modified and op.lmb:
        op.modified_lock = True
    else:
        op.modified_lock = False

    if to == 'BEVEL_Q':
        bc.q_bevel = not bc.q_bevel
        bc.shape.data.bc.q_beveled = bc.q_bevel
        to = 'BEVEL'

    if not init:
        op.last['operation'] = op.operation

    for mod in bc.shape.modifiers:
        if mod.type in clear_mods:
            setattr(bc.shape.bc, mod.type.lower(), False)
            bc.shape.modifiers.remove(mod)

    bound_box = bc.shape.bound_box

    op.last['lattice_corner'] = lattice.center(Matrix(), 'front') * 2 - Vector(bc.lattice.bound_box[op.draw_dot_index])
    op.last['lattice_center'] = lattice.center(Matrix(), None)

    # op.ray['location'] = math.vector_sum([bc.shape.matrix_world @ op.bounds[i] for i in (1, 2, 5, 6)]) / 4

    if not init:
        op.last['draw_delta'] = Vector(op.bounds[op.draw_dot_index]) - Vector(bc.lattice.bound_box[op.draw_dot_index]) if op.extruded else Vector((0,0,0))

    preference.shape['dimension_x'] = preference.shape['circle_diameter'] =  bc.lattice.dimensions.x / (bc.lattice.scale.x if bc.lattice.scale.x else 1)
    preference.shape['dimension_y'] = bc.lattice.dimensions.y / (bc.lattice.scale.y if bc.lattice.scale.y else 1)
    preference.shape['dimension_z'] = bc.lattice.dimensions.z / (bc.lattice.scale.z if bc.lattice.scale.z else 1)

    if op.operation == 'DRAW':
        if op.shape_type == 'NGON' and not op.add_point:
            mesh.remove_point(op, context, event)

        op.last['accucut_distance'] = 0.0
        op.last['accucut_depth'] = preference.shape.offset
        op.snap_lock_type = ''

        if not hasattr(op, 'draw_exit_width'):
            op.draw_exit_width = view3d.location2d_to_location3d(*op.mouse['location'], op.ray['location'])

        if to == 'EXTRUDE' and op.live and op.mode not in {'JOIN', 'MAKE'} and not op.modified and preference.behavior.accucut and not op.lazorcut_performed:
            op.last['accucut_distance'], op.last['accucut_depth'] = utility.accucut(op, context, extrude=False, reset=preference.surface != 'VIEW' and not hasattr(bc.snap.operator, 'handler'))

            if not (op.shape_type == 'CUSTOM' and op.proportional_draw) and op.last['accucut_depth'] < min(op.datablock['dimensions'][:]) * 0.1:
                preference.behavior.accucut = False

    elif op.operation in {'EXTRUDE', 'OFFSET', 'SCALE', 'ROTATE', 'MOVE'}:
        bc.plane.matrix_world = bc.shape.matrix_world
        op.start['matrix'] = bc.plane.matrix_world.copy()
        extrude_index = 1 if op.inverted_extrude else 0
        op.start['extrude'] = op.last['depth'] = bc.lattice.bound_box[extrude_index][2]

        # op.ray['location'] = math.vector_sum([bc.shape.matrix_world @ Vector(bound_box[i]) for i in (1, 2, 5, 6)]) / 4

    elif op.operation == 'ARRAY':
        axis_index = [bc.shape.bc.array_axis == axis for axis in 'XYZ'].index(True)

        for mod in bc.shape.modifiers:
            if mod.type == 'ARRAY':
                op.last['modifier']['offset'] = mod.constant_offset_displace[axis_index]
                op.last['modifier']['count'] = mod.count
                break

        if to == 'ARRAY' and not bc.shape.bc.array_circle:
            bc.shape.bc['array_circle'] = True

            mesh.pivot(op, context)

        elif to == 'ARRAY' and op.operation == 'ARRAY' and bc.shape.bc.array_circle:
            bc.shape.bc['array_circle'] = False
            for mod in bc.shape.modifiers:
                if mod.type == 'ARRAY':
                    bc.shape.modifiers.remove(mod)
                elif mod.type == 'DISPLACE':
                    bc.shape.modifiers.remove(mod)

    elif op.operation == 'SOLIDIFY':
        obj = bc.shape if op.mode != 'INSET' else (op.datablock['insets'][-1] if op.datablock['insets'] else None)
        if obj:
            for mod in obj.modifiers:
                if mod.type == 'SOLIDIFY':
                    if op.mode != 'INSET':
                        op.last['modifier']['thickness'] = mod.thickness
                    else:
                        op.last['thickness'] = mod.thickness
                    break

            if modified:
                if to == 'SOLIDIFY': to = 'NONE'

        del obj

    elif op.operation == 'BEVEL':
        for mod in bc.shape.modifiers:
            if mod.type == 'BEVEL' and not init:
                width_type = 'bevel_width'

                if mod.name.startswith('quad'):
                    width_type = 'quad_bevel_width'

                elif mod.name.startswith('front'):
                    width_type = 'front_bevel_width'

                op.last['modifier'][width_type] = mod.width
                op.last['modifier']['segments'] = mod.segments
                op.last['modifier']['limit_method'] = mod.limit_method
                if bpy.app.version[:2] < (2, 90):
                    op.last['modifier']['use_only_vertices'] = mod.use_only_vertices
                else:
                    op.last['modifier']['affect'] = mod.affect
                op.last['modifier']['use_clamp_overlap'] = mod.use_clamp_overlap
                #break

        op.last['mouse'] = op.mouse['location']

        if modified:
            if to == 'BEVEL':
                to = 'NONE'

    elif op.operation == 'TAPER':
        if to == 'TAPER':
            to = 'NONE'

    rebevel = False
    if op.shape_type == 'NGON' or op.ngon_fit:
        if to in {'EXTRUDE', 'OFFSET'} and not op.extruded:
            for mod in bc.shape.modifiers:
                if mod.type == 'BEVEL':
                    bc.shape.modifiers.remove(mod)

                    rebevel = True

            amount = -1
            if op.ngon_fit:
                amount = -0.5

                matrix = Matrix.Translation((0, 0, 0.5))
                bc.shape.data.transform(matrix)

                preference.shape.taper = preference.shape.taper

                op.start['extrude'] = bc.lattice.data.points[lattice.front[0]].co_deform.z

                for i in lattice.back:
                    bc.lattice.data.points[i].co_deform.z = op.start['extrude']

            mesh.extrude(op, context, event, amount=amount)

        if to != 'DRAW' and not op.ngon_fit:
            lattice.fit(op, context)

            if op.extruded:
                preference.shape.taper = preference.shape.taper

            op.shape_type = 'BOX'
            op.ngon_fit = True
            op.last['lattice_corner'] = lattice.center(Matrix(), 'front') * 2 - Vector(bc.lattice.bound_box[op.draw_dot_index])
            op.last['lattice_center'] = lattice.center(Matrix(), None)
            op.bounds = [Vector(c) for c in bc.lattice.bound_box]

    if op.modified and op.alt_lock:
        op.alt_lock = False

    if to == 'ROTATE':
        op.last['mouse'] = op.mouse['location']
        op.last['local_pivot'] = mesh.pivot(op, context, transform=False)
        op.last['global_pivot'] = bc.shape.matrix_world @ op.last['local_pivot']
        op.last['lattice'] = bc.lattice.copy()
        op.last['shape'] = bc.shape.copy()

    if op.operation == 'ROTATE':
        op.rotated = True

    if to == 'SCALE':
        op.last['mouse'] = op.mouse['location']
        op.last['local_pivot'] = mesh.pivot(op, context, transform=False)
        op.last['global_pivot'] = bc.shape.matrix_world @ op.last['local_pivot']
        op.last['lattice'] = bc.lattice.copy()
        op.last['lattice_points'] = [p.co_deform[:] for p in bc.lattice.data.points]
        op.last['shape'] = bc.shape.copy()
        op.last['scale'] = (view3d.location3d_to_location2d(op.last['global_pivot']) - op.last['mouse']).length
        op.last['axis'] = 'XYZ'

    if op.operation == 'SCALE':
        op.scaled = True

    if to == 'MOVE':
        op.last['location'] = bc.shape.matrix_world @ bc.shape.location
        op.last['view3d_location'] = op.view3d['location']
        op.last['lattice'] = bc.lattice.copy()
        op.last['lattice'].bc.removeable = True
        op.last['shape'] = bc.shape.copy()
        op.last['shape'].bc.removeable = True
        op.last['axis'] = 'XY'

    if op.operation == 'MOVE':
        op.translated = True

    value = to

    op.operation = value
    toolbar.change_prop(context, 'operation', value)

    if value in {'EXTRUDE', 'OFFSET'}:
        mouse = op.mouse['location']

        bc.plane.matrix_world = bc.shape.matrix_world
        matrix = bc.plane.matrix_world
        inverse = matrix.inverted()

        if not op.inverted_extrude:
            front = (1, 2, 5, 6)
            back = (0, 3, 4, 7)
        else:
            back = (1, 2, 5, 6)
            front = (0, 3, 4, 7)

        front_center = (0.25 * sum((op.bounds[point] for point in front), Vector()))
        back_center = (0.25 * sum((op.bounds[point] for point in back), Vector()))
        coord = matrix @ (front_center if value == 'OFFSET' else back_center)

        op.start['intersect'] = inverse @ view3d.location2d_to_location3d(mouse.x, mouse.y, coord)

        op.start['offset'] = front_center.z
        op.start['extrude'] = back_center.z
        op.start['matrix'] = bc.shape.matrix_world.copy()

    elif value == 'ROTATE':
        op.angle = 0

        op.last['track'] = op.mouse['location'] - view3d.location3d_to_location2d(bc.lattice.matrix_world.translation)
        op.last['mouse'] = op.mouse['location']

        bc.axis = 'Z' if bc.axis == 'NONE' else bc.axis

    elif value == 'ARRAY':
        bc.shape.bc.array = True
        op.start['displace'] = preference.shape.displace

        if bc.flip:
            bc.flip = False

        axis_index = [bc.shape.bc.array_axis == axis for axis in 'XYZ'].index(True)

        for mod in bc.shape.modifiers:
            if mod.type == 'ARRAY':
                op.last['modifier']['offset'] = mod.constant_offset_displace[axis_index]
                op.last['modifier']['count'] = mod.count
                op.last['mouse'] = op.mouse['location']

                break

    elif value == 'SOLIDIFY':
        bc.shape.bc.solidify = True
        obj = bc.shape if op.mode != 'INSET' else op.datablock['insets'][-1]

        for mod in obj.modifiers:
            if mod.type == 'SOLIDIFY':
                if op.mode != 'INSET':
                    op.last['modifier']['thickness'] = mod.thickness

                else:
                    op.last['thickness'] = mod.thickness

                break

        del obj

        op.last['mouse'] = op.mouse['location']

    elif value == 'BEVEL':
        bc.shape.bc.bevel = True

        for mod in bc.shape.modifiers:
            if mod.type == 'BEVEL':
                if mod.name.startswith('quad'):
                    preference.shape['quad_bevel_segments'] = mod.segments
                    op.last['modifier']['quad_bevel_width'] = mod.width

                elif mod.name.startswith('front'):
                    preference.shape['front_bevel_segments'] = mod.segments
                    op.last['modifier']['front_bevel_width'] = mod.width

                else:
                    preference.shape['bevel_segments'] = mod.segments
                    op.last['modifier']['bevel_width'] = mod.width

                bc.shape.modifiers.remove(mod)

        op.last['mouse'] = op.mouse['location']

    elif value == 'DISPLACE':
        displace = None

        for mod in bc.shape.modifiers:
            if mod.type == 'DISPLACE':
                displace = mod

                break

        if displace:
            op.start['displace'] = displace.strength

    elif value == 'TAPER':
        op.last['taper'] = preference.shape.taper
        op.last['mouse'] = op.mouse['location']

    if not init:
        if value == 'NONE':
            op.report({'INFO'}, 'Shape Locked')

        else:
            op.report({'INFO'}, '{}{}{}'.format(
                'Added ' if value == 'ARRAY' else '',
                value.title()[:-1 if value in {'MOVE', 'ROTATE', 'SCALE', 'EXTRUDE', 'DISPLACE'} else len(value)],
                'ing' if value not in {'ARRAY', 'GRID'} else ''))

        refresh.shape(op, context, event, dot=dot)

    elif value != 'DRAW':
        refresh.shape(op, context, event)

    if rebevel:
        bevel.shape(op, context, event)

    if to != 'MOVE':
        op.move_lock = False


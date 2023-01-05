import bpy

from math import radians
from mathutils import Vector

from .. import mesh
from ...... utility import addon, screen, modifier


# XXX: bevel before array
def shape(op, context, event):
    preference = addon.preference()
    bc = context.scene.bc
    snap = preference.snap.enable and preference.snap.incremental

    straight_edge = preference.shape.straight_edges or bc.q_back_only

    clamp_offset = clamp(op) - 0.0025 if bpy.app.version[:2] < (2, 82) else clamp(op)
    clamped = False

    max_dimension = max(bc.shape.dimensions[:-1])
    width_input = ((op.mouse['location'].x - op.last['mouse'].x) / screen.dpi_factor(ui_scale=False, integer=True)) * max_dimension
    factor = 0.0001 if event and event.shift and op.prior_to_shift == 'NONE' else 0.001
    weld_modifier = None

    if op.shape_type == 'CIRCLE' and preference.shape.circle_type == 'POLYGON' and preference.shape.circle_vertices > 12:
        bc['q_bevel'] = bc.shape.data.bc.q_beveled = True
        bc.q_back_only = False
        op.geo['indices']['mid_edge'] = []

    if preference.shape.quad_bevel:
        if not straight_edge or op.shape_type == 'CIRCLE' or bc.q_back_only:
            mesh.bevel_weight(op, context, event)

        else:
            mesh.vertex_group(op, context, event)
    else:
        mesh.bevel_weight(op, context, event)

    m = None
    for mod in bc.shape.modifiers:
        if mod.type == 'BEVEL':
            m = mod
            break

    if not m:
        for mod in modifier.collect(bc.shape, type='WELD'):
            bc.shape.modifiers.remove(mod)

        vertex_only = (op.shape_type == 'NGON' or op.ngon_fit) and not op.extruded
        quad_bevel = not preference.shape.quad_bevel or (preference.shape.quad_bevel and not straight_edge)

        if vertex_only:
            mod = bc.shape.modifiers.new(name='Bevel', type='BEVEL')
            mod.name = 'main_bevel'
            mod.show_render = False
            mod.show_expanded = False

            if bpy.app.version[:2] < (2, 90):
                mod.use_only_vertices = True

            else:
                mod.affect = 'VERTICES'

            mod.width = op.last['modifier']['bevel_width']
            mod.segments = preference.shape.bevel_segments
            mod.limit_method = 'ANGLE'
            mod.offset_type = 'OFFSET'

            mod = bc.shape.modifiers.new(name='Weld', type='WELD')
            mod.name = 'main_bevel_weld'
            mod.show_render = False
            mod.show_expanded = False

            modifier.sort(bc.shape, sort_types=['LATTICE', 'BEVEL'], first=True, ignore_hidden=False)

        elif quad_bevel or (op.shape_type == 'CIRCLE' and preference.shape.circle_type == 'MODIFIER'):
            mod = bc.shape.modifiers.new(name='Bevel', type='BEVEL')
            mod.name = 'main_bevel'
            mod.show_render = False
            mod.show_expanded = False
            mod.width = op.last['modifier']['bevel_width']
            mod.segments = preference.shape.bevel_segments
            mod.limit_method = 'WEIGHT'
            mod.offset_type = 'OFFSET'

            # if op.mode in {'JOIN', 'MAKE'} and (op.shape_type == 'BOX' and not op.ngon_fit):
            #     mesh.mesh.recalc_normals(bc.shape, face=True, index=4, inside=True)

            mod = bc.shape.modifiers.new(name='Weld', type='WELD')
            mod.name = 'main_bevel_weld'
            mod.show_render = False
            mod.show_expanded = False

            if (op.shape_type == 'NGON' or op.ngon_fit) and not preference.shape.cyclic:
                modifier.sort(bc.shape, sort_types=['LATTICE', 'BEVEL'], first=True, ignore_hidden=False)

        vertex_groups = bc.shape.vertex_groups if not straight_edge else reversed(bc.shape.vertex_groups)

        for group in vertex_groups:
            mod = bc.shape.modifiers.new(name='Bevel', type='BEVEL')
            mod.name = 'quad_bevel' #there is only one group atm tied to q bevel
            mod.show_expanded = False
            mod.width = op.last['modifier']['quad_bevel_width']
            mod.segments = preference.shape.quad_bevel_segments
            mod.limit_method = 'VGROUP'
            mod.vertex_group = group.name
            mod.offset_type = 'OFFSET'

            if mod.vertex_group == 'bottom' and not straight_edge:
                mod.offset_type = 'WIDTH'

            if op.shape_type != 'NGON' and not op.ngon_fit:
                if width_input > clamp(op):
                    mod.width = clamp_offset

            mod = bc.shape.modifiers.new(name='Weld', type='WELD')
            mod.name = 'quad_bevel_weld'
            mod.show_render = False
            mod.show_expanded = False

        if bc.bevel_front_face and (bc.q_bevel and not bc.q_back_only and op.geo['indices']['top_face']):
            mesh.mesh.recalc_normals(bc.shape, face_indices=op.geo['indices']['top_face'], inside=not op.inverted_extrude)

            mod = bc.shape.modifiers.new(name='Bevel', type='BEVEL')
            mod.name = 'front_bevel'
            mod.show_expanded = False
            mod.width = op.last['modifier']['front_bevel_width']
            mod.segments = preference.shape.front_bevel_segments
            mod.limit_method = 'ANGLE'
            mod.offset_type = 'WIDTH'
            mod.angle_limit = radians(50)

            if width_input > clamp(op):
                mod.width = clamp_offset

            mod = bc.shape.modifiers.new(name='Weld', type='WELD')
            mod.name = 'front_bevel_weld'
            mod.show_render = False
            mod.show_expanded = False

        elif not bc.q_bevel:
            mesh.mesh.recalc_normals(bc.shape, inside=op.inverted_extrude)

        return

    segment_state = False
    # width = 0.0
    update = True
    for mod in bc.shape.modifiers:
        if mod.type == 'BEVEL':
            width_type = 'bevel_width'

            if mod.name.startswith('quad'):
                width_type = 'quad_bevel_width'

            elif mod.name.startswith('front'):
                width_type = 'front_bevel_width'

            width = op.last['modifier'][width_type] + width_input * factor if op.last['modifier'][width_type] + width_input * factor > 0.0004 else 0.0004

            if op.shape_type != 'NGON' and not op.ngon_fit and width > clamp(op):
                clamped = True
                width = clamp_offset

            if snap and event and event.ctrl:
                width = round(width, 2 if event and event.shift and op.prior_to_shift == 'NONE' else 1)

            elif not clamped or (op.shape_type == 'NGON' or op.ngon_fit):
                if width < 0.001 and not op.width_state or segment_state:
                    segment_state = True
                    op.width_state = True

                    if mod.segments == 1 and op.segment_state:
                        mod.segments = preference.shape.bevel_segments if preference.shape.bevel_segments != 1 else preference.shape.bevel_segments_default

                    else:
                        op.segment_state = True
                        mod.segments = 1

                elif width > 0.0011 and op.width_state:
                    op.width_state = False

                if update:
                    op.last['modifier'][width_type] = width
                    op.last['mouse'].x = op.mouse['location'].x

            if update:
                preference.shape[width_type] = width

            mod.width = width

    update = False


def clamp(op):
    preference = addon.preference()
    bc = bpy.context.scene.bc

    vector1 = Vector(bc.shape.bound_box[0][:])
    vector2 = Vector(bc.shape.bound_box[1][:])
    vector3 = Vector(bc.shape.bound_box[5][:])
    vector4 = Vector(bc.shape.bound_box[6][:])

    distances = [vector4 - vector3, vector3 - vector2]

    if bc.shape.data.bc.q_beveled:
        distances.append((vector2 - vector1) * 2)

    return max(min(distances)) * 0.5 * preference.shape.taper


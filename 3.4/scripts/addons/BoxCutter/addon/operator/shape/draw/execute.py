import bpy, bmesh

from mathutils import Vector

from ..... utility import addon, object, modifier
# from ... utility.shape.change import last
from .. utility.change import last
# from ... utility import shape
from .. import utility
from .. utility import statusbar
# from .. utility import statusbar
from .... sound import time_code

# from .... property import prop

# TODO: dimension check determine if user made too small of a shape
#  - view distance factored (determining work scale)
#  - create warning dialogue
#  - create pref for displaying warning dialogue
#    - offer in dialogue
#      ~ pref should warn against disable (i.e. garbage cuts)
def operator(op, context):
    preference = addon.preference()
    bc = context.scene.bc
    bc.running = False

    statusbar.remove()

    bc.shape.bc.target = context.active_object if op.mode != 'MAKE' else None

    if op.original_mode == 'EDIT_MESH':
        bpy.ops.object.mode_set(mode='OBJECT')

    for mod in bc.shape.modifiers:
        if mod.type == 'SOLIDIFY':
            mod.show_viewport = True if (op.shape_type == 'NGON' or op.ngon_fit) and not preference.shape.cyclic else False

        if mod.type == 'MIRROR':
            mod.show_viewport = False

    context.view_layer.update()

    # TODO: Use lattice coords instead of dimensions, immediate/accurate lazorcut check
    if bc.shape.dimensions[2] < preference.shape.lazorcut_limit and not op.repeat:
        utility.accucut(op, context)


    if not op.repeat:
        utility.data.repeat(op, context, collect=True)

    if not op.repeat and op.mode == 'KNIFE' and preference.surface == 'VIEW' and bc.shape.dimensions[2] < preference.shape.lazorcut_limit:
        op.lazorcut = True

    for mod in bc.shape.modifiers:
        if mod.type == 'MIRROR':
            mod.show_viewport = True

    last['origin'] = op.origin
    last['points'] = [Vector(point.co_deform) for point in bc.lattice.data.points]

    for mod in bc.shape.modifiers:
        if mod.type == 'ARRAY' and not mod.use_object_offset:
            offsets = [abs(o) for o in mod.constant_offset_displace]
            if sum(offsets) < 0.0005:
                bc.shape.modifiers.remove(mod)

            else:
                index = offsets.index(max(offsets))
                last['modifier']['offset'] = mod.constant_offset_displace[index]
                last['modifier']['count'] = mod.count

        elif mod.type == 'BEVEL':
            if mod.width < 0.0005:
                bc.shape.modifiers.remove(mod)

            else:
                width_type = 'bevel_width'

                if mod.name.startswith('quad'):
                    width_type = 'quad_bevel_width'

                elif mod.name.startswith('front'):
                    width_type = 'front_bevel_width'

                last['modifier'][width_type] = mod.width# if mod.width > last['modifier'][width_type] else last['modifier'][width_type]
                last['modifier']['segments'] = mod.segments

        elif mod.type == 'SOLIDIFY':
            if abs(mod.thickness) < 0.0005:
                bc.shape.modifiers.remove(mod)

            else:
                last['modifier']['thickness'] = mod.thickness

    if op.original_mode == 'EDIT_MESH':
        bpy.ops.object.mode_set(mode='EDIT')

    op.update()

    utility.data.clean(op, context)

    key = preference.display.shape_fade_time_out
    if key in time_code.keys():
        utility.sound.play(time_code[key])

    op.report({'INFO'}, 'Executed')

    return {'FINISHED'}

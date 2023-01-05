# from .... utility import modifier
from .. import modifier
from ...... utility import addon


def verify(context, mirror, bisect=False):
    preference = addon.preference()
    bc = context.scene.bc

    context.view_layer.update()

    if not sum(list(bc.shape.dimensions)):
        for i in range(3):
            if bisect:
                mirror.use_bisect_axis[i] = not mirror.use_bisect_axis[i]
            else:
                mirror.use_bisect_flip_axis[i] = not mirror.use_bisect_flip_axis[i]

            context.view_layer.update()

            if sum(list(bc.shape.dimensions)):
                preference.shape['mirror_axis'] = mirror.use_axis
                preference.shape['mirror_bisect_axis'] = mirror.use_bisect_axis
                preference.shape['mirror_flip_axis'] = mirror.use_bisect_flip_axis

                bc.mirror_axis = mirror.use_axis
                bc.mirror_axis_flip = mirror.use_bisect_flip_axis
                return

            if bisect:
                mirror.use_bisect_axis[i] = not mirror.use_bisect_axis[i]
            else:
                mirror.use_bisect_flip_axis[i] = not mirror.use_bisect_flip_axis[i]

    context.view_layer.update()

    if not sum(list(bc.shape.dimensions)):
        verify(context, mirror, bisect=True)

        return

    preference.shape['mirror_axis'] = mirror.use_axis
    preference.shape['mirror_bisect_axis'] = mirror.use_bisect_axis
    preference.shape['mirror_flip_axis'] = mirror.use_bisect_flip_axis

    bc.mirror_axis = mirror.use_axis
    bc.mirror_axis_flip = mirror.use_bisect_flip_axis


def shape(op, context, event, init=False, to=None, flip=False):
    preference = addon.preference()
    bc = context.scene.bc

    bc.shape.bc.mirror = True

    if init:
        mirror = bc.shape.modifiers.new(name='Mirror', type='MIRROR')
        mirror.use_axis = preference.shape.mirror_axis
        mirror.use_bisect_axis = preference.shape.mirror_bisect_axis
        mirror.use_bisect_flip_axis = preference.shape.mirror_flip_axis

        if context.active_object:
            mirror.mirror_object = context.active_object

        bc.mirror_axis = mirror.use_axis
        bc.mirror_axis_flip = mirror.use_bisect_flip_axis

        context.view_layer.update()

        verify(context, mirror)

        return

    index = {
        'X': 0,
        'Y': 1,
        'Z': 2}

    mirror = None

    for mod in bc.shape.modifiers:
        if mod.type == 'MIRROR':
            mirror = mod

            break

    if not mirror:
        mirror = bc.shape.modifiers.new(name='Mirror', type='MIRROR')
        mirror.use_axis[0] = False

        if context.active_object:
            mirror.mirror_object = context.active_object

    init_enabled = tuple(a for a in mirror.use_axis)

    if not flip:
        for i in range(len(mirror.use_axis)):
            mirror.use_axis[i] = False
            mirror.use_bisect_axis[i] = False

    for i in range(len(mirror.use_bisect_flip_axis)):
        mirror.use_bisect_flip_axis[i] = False

    if not flip:
        if to:
            bc.mirror_axis[index[to]] = int(not bool(bc.mirror_axis[index[to]]))

            if not bc.mirror_axis[index[to]]:
                bc.mirror_axis_flip[index[to]] = False

        for i, a in enumerate(bc.mirror_axis):
            mirror.use_axis[i] = bool(a)
            mirror.use_bisect_axis[i] = bool(a)

        for i, f in enumerate(bc.mirror_axis_flip):
            mirror.use_bisect_flip_axis[i] = bool(f)

    elif True in init_enabled:
        bc.mirror_axis_flip[index[to]] = int(not bool(bc.mirror_axis_flip[index[to]]))

        for i, f in enumerate(bc.mirror_axis_flip):
            mirror.use_bisect_flip_axis[i] = bool(f)

    enabled = tuple(a for a in mirror.use_axis)

    if to and True not in enabled:
        bc.shape.modifiers.remove(mirror)
        if not flip:
            op.report({'INFO'}, 'Removed Mirror')

        return

    elif True not in enabled:
        bc.mirror_axis[0] = True

        mirror.use_axis[0] = True
        mirror.use_bisect_axis[0] = True
        mirror.use_bisect_flip_axis[0] = bool(bc.mirror_axis_flip[0])

        op.report({'INFO'}, 'Mirrored on: X')

    elif to and not flip:
        current = ''
        for i, a in enumerate(index.keys()):
            if mirror.use_axis[i]:
                current += F'{a} | '

        op.report({'INFO'}, F'Mirrored on: {current[:-3]}')

    elif flip and True in init_enabled:
        msg = 'Bisect {}lipped on: {}'.format('Unf' if not mirror.use_bisect_flip_axis[index[to]] else 'F', to)
        op.report({'INFO'}, msg)

    verify(context, mirror)

    del mirror

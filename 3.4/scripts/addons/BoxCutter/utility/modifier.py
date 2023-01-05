import bpy

from mathutils import Vector

sort_types = [
    'ARRAY',
    'MIRROR',
    'SOLIDIFY',
    'BEVEL',
    'WEIGHTED_NORMAL',
    'SIMPLE_DEFORM',
    'TRIANGULATE',
    'DECIMATE',
    'REMESH',
    'SUBSURF',
    'UV_PROJECT',
]

if bpy.app.version[:2] >= (2, 82):
    sort_types.insert(4, 'WELD')


def sort(obj, option=None, ignore=[], sort_types=sort_types, last_types=[], first=False, static_sort=False, ignore_hidden=True, sort_depth=0, ignore_flag=' ', stop_flag='_'):
    modifiers = []
    sortable = obj.modifiers[:]

    if option:
        if not option.sort_modifiers:
            return

    if sort_depth:
        length = len(sortable)

        if length > sort_depth:
            sortable = sortable[length - sort_depth:]

    for index, mod in enumerate(sortable):
        if mod.name[0] == stop_flag:
            sortable = sortable[:index]

    for type in sort_types:
        sort = getattr(option, F'sort_{type.lower()}') if option else True
        sort_last = getattr(option, F'sort_{type.lower()}_last') if option else type in last_types
        last = False

        if not sort:
            continue

        for mod in reversed(sortable):
            visible = (mod.show_viewport and mod.show_render) or not ignore_hidden
            if mod in ignore or not visible or mod.name[0] == ignore_flag:
                continue

            if not last and sort_last and mod.type == type:
                last = True
                modifiers.insert(0, mod)
            elif not sort_last and mod.type == type:
                modifiers.insert(0, mod)

    if not modifiers:
        return

    if not static_sort:
        modifiers = sorted(modifiers, key=lambda mod: obj.modifiers[:].index(mod))

    unsorted = []
    for mod in reversed(obj.modifiers):
        if mod not in modifiers:
            unsorted.insert(0, mod)

    modifiers = modifiers + unsorted if first else unsorted + modifiers
    modifiers = [stored(mod) for mod in modifiers]

    sortable = False
    for type, mod in zip(modifiers, obj.modifiers):
        if type.name != mod.name:
            sortable = True
            break

    if not sortable:
        return

    obj.modifiers.clear()

    for mod in modifiers:
        new(obj, mod=mod)

    del modifiers


def apply(obj, mod=None, visible=False, modifiers=[], ignore=[], types={}):
    apply = []
    keep = []

    if mod:
        apply.append(mod)

    else:
        for mod in obj.modifiers:
            if (not modifiers or mod in modifiers) and mod not in ignore and (not visible or mod.show_viewport) and (not types or mod.type in types):
                apply.append(mod)

    for mod in obj.modifiers:
        if mod not in apply:
            keep.append(mod)

    keep = [stored(mod) for mod in keep]
    apply = [stored(mod) for mod in apply]

    if not apply:
        del keep

        return

    obj.modifiers.clear()

    for mod in apply:
        new(obj, mod=mod)

    if obj.data.users > 1:
        obj.data = obj.data.copy()
    remesh_voxel_size = obj.data.remesh_voxel_size

    ob = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    obj.data = bpy.data.meshes.new_from_object(ob)
    obj.data.remesh_voxel_size = remesh_voxel_size

    obj.modifiers.clear()

    for mod in keep:
        new(obj, mod=mod)

    del apply
    del keep


def bevels(obj, angle=False, weight=False, vertex_group=False, props={}):
    if not hasattr(obj, 'modifiers'):
        return []

    bevel_mods = [mod for mod in obj.modifiers if mod.type == 'BEVEL']

    if not angle and not weight and not vertex_group and not props:
        return bevel_mods

    modifiers = []

    if angle:
        for mod in bevel_mods:
            if mod.limit_method == 'ANGLE':
                modifiers.append(mod)

    if weight:
        for mod in bevel_mods:
            if mod.limit_method == 'WEIGHT':
                modifiers.append(mod)

    if vertex_group:
        for mod in bevel_mods:
            if mod.limit_method == 'VGROUP':
                modifiers.append(mod)

    if props:
        for mod in bevel_mods:
            if mod in modifiers:
                continue

            for pointer in props:
                prop = hasattr(mod, pointer) and getattr(mod, pointer) == props[pointer]
                if not prop:
                    continue

                modifiers.append(mod)

    return sorted(modifiers, key=lambda mod: bevel_mods.index(mod))


def unmodified_bounds(obj, exclude={}):
    disabled = []
    for mod in obj.modifiers:
        if exclude and mod.type not in exclude and mod.show_viewport:
            disabled.append(mod)
            mod.show_viewport = False

    if disabled:
        bpy.context.view_layer.update()

    bounds = [Vector(point[:]) for point in obj.bound_box[:]]

    for mod in disabled:
        mod.show_viewport = True

    del disabled

    return bounds


def stored(mod):
    exclude = {'__doc__', '__module__', '__slots__', '_RNA_UI', 'bl_rna', 'rna_type', 'face_count'}
    new_type = type(mod.name, (), {})

    projector = lambda p: type('projector', (), {'object': p.object})

    # TODO: 2.9 point handle write
    profile_point = lambda p: type('point', (), {
        'location': p.location[:],
        'handle_type_1': p.handle_type_1,
        'handle_type_2': p.handle_type_2})

    for pointer in dir(mod):
        if pointer not in exclude:

            type_string = str(type(getattr(mod, pointer))).split("'")[1]
            if mod.type == 'UV_PROJECT' and pointer =='projectors':
                setattr(new_type, pointer, [projector(p) for p in mod.projectors])

            elif mod.type == 'BEVEL' and pointer == 'custom_profile':
                profile = type('custom_profile', (), {
                    'use_clip': mod.custom_profile.use_clip,
                    'use_sample_even_lengths': mod.custom_profile.use_sample_even_lengths,
                    'use_sample_straight_edges': mod.custom_profile.use_sample_straight_edges,
                    'points': [profile_point(p) for p in mod.custom_profile.points]})

                setattr(new_type, pointer, profile)

            elif mod.type == 'HOOK' and pointer == 'matrix_inverse':
                setattr(new_type, pointer, getattr(mod, pointer).copy()) # XXX: use copy

            elif type_string not in {'bpy_prop_array', 'Vector'}:
                setattr(new_type, pointer, getattr(mod, pointer))

            else:
                setattr(new_type, pointer, list(getattr(mod, pointer)))

    return new_type


def new(obj, name=str(), _type='BEVEL', mod=None, props={}):
    if mod:
        new = obj.modifiers.new(name=mod.name, type=mod.type)

        for pointer in dir(mod):
            if '__' in pointer or pointer in {'bl_rna', 'rna_type', 'type', 'face_count', 'falloff_curve', 'vertex_indices', 'vertex_indices_set'}:
                continue

            elif mod.type == 'NODES':
                new.node_group = mod.node_group

            elif mod.type == 'UV_PROJECT' and pointer =='projectors':
                new.projector_count = mod.projector_count
                for new_proj, old_proj in zip(new.projectors, mod.projectors):
                    new_proj.object = old_proj.object

            elif mod.type == 'BEVEL' and pointer == 'custom_profile':
                # TODO: 2.9 point handle read
                step = 1 / len(mod.custom_profile.points)
                for index, point in enumerate(mod.custom_profile.points[1:-1]):
                    new_point = new.custom_profile.points.add(index * step, (index + 1) * step)
                    new_point.handle_type_1 = point.handle_type_1
                    new_point.handle_type_2 = point.handle_type_2

                for index, point in enumerate(mod.custom_profile.points[1:-1]):
                    new.custom_profile.points[index + 1].location = point.location

                new.custom_profile.update()

                new.custom_profile.use_clip = mod.custom_profile.use_clip
                new.custom_profile.use_sample_even_lengths = mod.custom_profile.use_sample_even_lengths
                new.custom_profile.use_sample_straight_edges = mod.custom_profile.use_sample_straight_edges

            else:
                setattr(new, pointer, getattr(mod, pointer))

        if mod.type == 'HOOK':
            new.matrix_inverse = mod.matrix_inverse # XXX: needs to be set after new.object
            new.vertex_indices_set(mod.vertex_indices)

    elif _type:
        new = obj.modifiers.new(name=name, type=_type)

        if props:
            for pointer in props:
                if hasattr(new, pointer):
                    setattr(new, pointer, props[pointer])

        return new


def exists(obj, full_match=True, types={}, **props):
    if not obj.modifiers:
        return False

    item = props.items()

    if not item:
        return bool(obj.modifiers) if not types else bool(any(mod.type in types for mod in obj.modifiers))

    checked = []
    for key, arg in item:
        checked.append(any(hasattr(mod, key) and getattr(mod, key) == arg or mod.type in types) for mod in obj.modifiers)

    return all(checked) if full_match else any(checked)


def collect(obj, full_match=False, types={}, **props):
    if not obj.modifiers:
        return []

    item = props.items()

    if not item:
        return obj.modifiers[:] if not types else [mod for mod in obj.modifiers if mod.type in types]

    check = lambda m, i: ((hasattr(m, k) and getattr(m, k) == a) for k, a in i) or m.type in types
    validated = lambda m, i: all(check(m, i)) if full_match else any(check(m, i))

    modifiers = []
    for mod in obj.modifiers:
        if not validated(mod, item):
            continue

        modifiers.append(mod)

    return modifiers


def move_to_index(mod, index=0):
    count = len(mod.id_data.modifiers)

    if index < 0:
        index = count - (abs(index) % count)

    else:
        index = index % count

    if bpy.app.version[:2] >= (2, 90):
        override = {'object' : mod.id_data, 'active_object' : mod.id_data}
        bpy.ops.object.modifier_move_to_index(override, modifier= mod.name, index=index)

    else:
        obj = mod.id_data
        modifiers = [stored(m) for m in obj.modifiers if m != mod]
        modifiers.insert(index, stored(mod))
        obj.modifiers.clear()

        for mod in modifiers:
            new(obj, mod=mod)

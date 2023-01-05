import time

import bpy

from mathutils import Matrix, Vector

from . import refresh, flip
from .. import modifier
from ..... import toolbar

from .. data import restore_overrides
from ...... utility import addon
from math import radians


def change(op, context, event, to='CUT', init=False, force=False):
    preference = addon.preference()
    bc = context.scene.bc

    if op.datablock['targets'] or init:
        value = to if init or to != op.mode or force else op.last['mode']

        offset = preference.shape.offset

        # was_flip_z = op.flip_z

        if bc.snap.operator and bc.snap.hit and hasattr(bc.snap.operator, 'grid_handler'):
            if value == 'MAKE':
                # op.flip_z = False
                offset = -offset

            elif value == 'JOIN':
                op.flip_z = True
                offset = -offset * 2

            else:
                offset = 0
                # op.flip_z = False

        elif value == 'MAKE':
            # op.flip_z = False
            offset = 0

        elif value == 'JOIN':
            # op.flip_z = True
            offset = -offset

        # else:
        #     op.flip_z = False

        # if not op.extruded and not op.modified:
        #     flip_modes = {'MAKE', 'JOIN'}

        #     if (value in flip_modes and op.mode not in flip_modes) or (value not in flip_modes and op.mode in flip_modes) or (op.mode in flip_modes and init) :
        #         matrix = Matrix.Rotation(radians(180), 4, 'X')
        #         bc.shape.matrix_world = bc.shape.matrix_world @ matrix
        #         bc.plane.matrix_world = bc.plane.matrix_world @ matrix
        #         bc.lattice.matrix_world = bc.lattice.matrix_world @ matrix

        #         bc.shape.data.transform(matrix.inverted())

        #         top = op.geo['indices']['top_edge']
        #         op.geo['indices']['top_edge'] = op.geo['indices']['bot_edge']
        #         op.geo['indices']['bot_edge'] = top

        matrix = op.start['matrix'] @ Matrix.Translation(Vector((0, 0, offset)))
        bc.shape.matrix_world.translation = matrix.translation
        bc.plane.matrix_world.translation = matrix.translation
        bc.lattice.matrix_world.translation = matrix.translation

        # if not op.flip_z and was_flip_z or op.flip_z and not was_flip_z:
        #     flip.shape(op, context, event, report=False)

        def store_last(value, to):
            if value != to:
                op.last['mode'] = value

            else:
                op.last['mode'] = 'CUT' if value != 'CUT' else value

        if not force:
            store_last(value, to)

        for obj in op.datablock['targets']:
            for mod in obj.modifiers:
                if mod == modifier.shape_bool(obj) or mod.type == 'BOOLEAN' and not mod.object and (not hasattr(mod, 'operand_type') or mod.operand_type != 'COLLECTION'):
                    obj.modifiers.remove(mod)

        if not init and (op.original_mode == 'EDIT_MESH' or op.mode == 'KNIFE'):
            restore_overrides(op, clear=True)

        for obj in op.datablock['slices'] + op.datablock['insets']:
            mesh = obj.data
            bpy.data.objects.remove(obj)
            bpy.data.meshes.remove(mesh)

            del mesh

        op.datablock['slices'] = list()
        op.datablock['insets'] = list()

        # if value == 'KNIFE':
        #     for obj in op.datablock['targets']:
        #         for mod in obj.modifiers:
        #             if mod.type == 'MIRROR':
        #                 mod.show_viewport = False

        # else:
        #     for obj in op.datablock['targets']:
        #         for mod in obj.modifiers:
        #             if mod.type == 'MIRROR':
        #                 mod.show_viewport = True

        op.mode = value
        toolbar.change_prop(context, 'mode', value)

        if not init:

            refresh.shape(op, context, event)

            wm = context.window_manager
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

            op.report({'INFO'}, '{}{}{}'.format(
                value.title()[:-1 if value in {'SLICE', 'MAKE'} else len(value)] if value != 'KNIFE' else 'Using Knife',
                't' if value in {'CUT', 'INSET'} else '',
                'ing' if value != 'KNIFE' else ''))


from mathutils import Matrix
from ...... utility import view3d, addon
# from ... import shape as _shape
from .. import mesh


def shape(op, context, event):
    bc = context.scene.bc

    amount = ((view3d.location3d_to_location2d(op.last['global_pivot']) - op.mouse['location']).length) / op.last['scale']

    if event.type in {'X', 'Y', 'Z'}:
        if event.value == 'RELEASE':
            if event.type == op.last['axis']:
                op.last['axis'] = 'XYZ'

            else:
                op.last['axis'] = event.type

    x = y = z = 1

    if op.last['axis'] == 'XYZ':
        x = y = z = amount

    elif op.last['axis'] == 'X':
        x = amount

    elif op.last['axis'] == 'Y':
        y = amount

    elif op.last['axis'] == 'Z':
        z = amount

    scale = Matrix.Diagonal((x, y, z, 1))

    matrix = op.last['shape'].matrix_world.copy()
    matrix.translation = op.last['global_pivot']

    for point, vec in zip(bc.lattice.data.points, op.last['lattice_points']):
        point.co_deform = vec

    matrix = matrix @ scale @ matrix.inverted() @ op.last['shape'].matrix_world
    scale = Matrix.Diagonal((*matrix.to_scale(), 1))
    loc = matrix.translation
    matrix.normalize()
    matrix.translation = loc

    bc.lattice.data.transform(scale)

    bc.lattice.matrix_world = bc.shape.matrix_world = matrix
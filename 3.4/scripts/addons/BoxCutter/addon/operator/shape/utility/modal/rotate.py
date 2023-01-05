from math import radians
from mathutils import Matrix
from ...... utility import view3d, addon, object
from ...... utility.math import increment_round, angle_to
# from ... import shape as _shape
from .. import mesh, lattice


def by_90(op, context, event, init=False):
    preference = addon.preference()
    bc = context.scene.bc
    prev_rot = 0

    if op.shape_type != 'NGON':
        if not init:
            prev_rot = bc.rotated_inside

            if bc.rotated_inside > 3:
                bc.rotated_inside = 0

            bc.rotated_inside += 1

        bc.shape.data.transform(Matrix.Rotation(radians(90 * (bc.rotated_inside - prev_rot) ), 4, 'Z'))

    if preference.shape.wedge and not init:
        bc.wedge_point_delta += 1

        if bc.wedge_point_delta > 3:
            bc.wedge_point_delta = 0

        lattice.wedge(op, context)

def by_90_shape(op, context):
    bc = context.scene.bc
    pivot = object.center(bc.shape)
    bc.shape.matrix_world = bc.lattice.matrix_world = bc.plane.matrix_world = matrix_by_angle(bc.shape.matrix_world, pivot=pivot, axis='Z', angle_rad=radians(90))

def matrix_by_angle(matrix, pivot=None, axis='Z', angle_rad=0):
    rotate_matrix = Matrix.Rotation(angle_rad, 4, axis)
    scaless_matrix = matrix.normalized()
    scale_matrix = Matrix.Diagonal((*matrix.to_scale(), 1))
    pivot_matrix = scaless_matrix.copy()
    if pivot: pivot_matrix.translation = pivot

    return (pivot_matrix @ rotate_matrix @ pivot_matrix.inverted() @ scaless_matrix) @ scale_matrix


def shape(op, context, event):
    preference = addon.preference()
    bc = context.scene.bc

    round_to = 1 if event.shift and op.prior_to_shift == 'NONE' else preference.snap.rotate_angle
    angle = increment_round(angle_to(op.last['mouse'], op.mouse['location'], view3d.location3d_to_location2d(op.last['global_pivot'])), round_to)

    if event.type in {'X', 'Y', 'Z'}:
        if event.value == 'RELEASE':
            preference.shape.rotate_axis = event.type

    bc.lattice.matrix_world = bc.shape.matrix_world = matrix_by_angle(op.last['shape'].matrix_world, pivot=op.last['global_pivot'], axis=preference.shape.rotate_axis, angle_rad=radians(-angle))
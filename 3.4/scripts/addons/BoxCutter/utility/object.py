import bpy
from mathutils import Vector, Matrix
from numpy import ones, reshape, array, append, delete

from . import addon, math


def duplicate(obj, name='', link=None):
    duplicate = obj.copy()
    duplicate.data = obj.data.copy()

    if name:
        duplicate.name = name
        duplicate.data.name = name

    if link:
        link.objects.link(duplicate)

    return duplicate


def center(obj, local=False, matrix=Matrix()):
    return 0.125 * math.vector_sum(bound_coordinates(obj, matrix=matrix if matrix != Matrix() else obj.matrix_world if not local else matrix
))


def bound_coordinates(obj, local=False, matrix=Matrix()):
    matrix = matrix if matrix != Matrix() or local else obj.matrix_world
    return [matrix @ Vector(coord) for coord in obj.bound_box]


def mesh_coordinates(obj, evaluated=True, local=False):
    from . mesh import indices
    from . math import transform_coordinates

    mesh = obj.data
    matrix = obj.matrix_world

    if evaluated:
        mesh = (obj.evaluated_get(bpy.context.evaluated_depsgraph_get())).to_mesh()
        obj.to_mesh_clear()

    mesh.update()
    mesh.calc_loop_triangles()

    length = len(mesh.vertices)
    coords = ones([length, 3], dtype='f')

    mesh.vertices.foreach_get('co', reshape(coords, length * 3))

    if not local:
        coords = transform_coordinates(matrix, coords)

    loop_index, edge_index = indices(mesh)
    return coords, loop_index, edge_index, mesh


def selected_bound_coordinates(local=False, matrix=Matrix(), combined=True):
    selected = bpy.context.selected_objects
    bounds = lambda o: bound_coordinates(o, local, matrix)
    return [v for o in selected for v in bounds(o)] if combined else [bounds(o) for o in selected]


def apply_transforms(obj):
    obj.data.transform(obj.matrix_world)
    clear_transforms(obj)


def clear_transforms(obj):
    obj.matrix_world = Matrix()


def parent(obj, target):
    matrix = obj.matrix_world.copy()
    obj.parent = target
    obj.matrix_parent_inverse = target.matrix_world.inverted()
    obj.matrix_world = matrix

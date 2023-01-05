from time import time
from math import radians

import bpy
import bmesh

from bpy.types import SpaceView3D
from gpu.types import GPUShader
from bgl import glEnable, glDisable, glPointSize, GL_BLEND

from mathutils import Vector, Matrix

from .. modal.ray import view_matrix, surface_matrix, planar_matrix

from ..... import shader
from ..... import toolbar
from ...... utility import method_handler, addon, screen, view3d, ray, math


class display_handler:
    exit: bool = False
    force_exit: bool = False


    @staticmethod
    def init_alpha(widget, time_in, time_out):
        widget.fade = bool(time_in) or bool(time_out)
        widget.fade_time_start = time()
        widget.fade_time = time_in * 0.001
        widget.fade_type = 'IN' if bool(time_in) else 'NONE'


    @staticmethod
    def update_alpha(widget, limit, time_out):
        alpha = 1.0

        if widget.fade_time and widget.fade_type != 'NONE':
            alpha = (time() - widget.fade_time_start) / widget.fade_time

        if widget.fade_type == 'IN':
            alpha = alpha if alpha < 1.0 else 1.0

            if alpha == 1.0:
                widget.fade_type = 'NONE'

        elif widget.fade_type == 'OUT':
            alpha = 1.0 - alpha if alpha < 1.0 else 0.0

            if alpha == 0.0:
                widget.fade_type = 'NONE'
                widget.fade = False

        elif widget.fade_type == 'NONE' and widget.exit:
            widget.fade_time_start = time()
            widget.fade_time = time_out * 0.001

            widget.fade_type = 'OUT'
            alpha = widget.alpha

        widget.alpha = alpha * limit if bpy.context.scene.bc.snap.display or (widget.exit and widget.fade) else 0.0


    @staticmethod
    def area_tag_redraw(context, type='VIEW_3D'):
        for area in context.screen.areas:
            if area.type != type:
                continue

            area.tag_redraw()


    def __init__(self, context, mouse):
        preference = addon.preference()
        bc = context.scene.bc

        self.mouse = Vector((mouse.x, mouse.y))
        self.face_index = -1

        self.fade = True

        self.grid: type = type('GridNull', tuple(), dict(display=False, update=lambda *_: None, fade=False, exit=True, remove=lambda *_, **__: None))
        # self.points: type = type('PointsNull', tuple(), dict(display=False, update=lambda *_: None, fade=False, exit=True, remove=lambda *_, **__: None))

        self.obj = None
        self.eval = False

        self._view_transform = context.region_data.view_rotation.to_matrix().to_4x4()

        hit = False
        self.normal = Vector((0, 0, -1))
        active = context.active_object
        selected = context.selected_objects

        if active:
            hit = self._ray_cast(context)

        axis = {
            'X': 'Y',
            'Y': 'X',
            'Z': 'Z'}
        angle = radians(-90 if preference.axis in {'X', 'Y'} else 90)

        if preference.surface == 'OBJECT' and hit:
            self.type = 'OBJECT'
            self._surface_matrix()

        elif preference.surface == 'VIEW' or not hit and active and selected:
            self.type = 'VIEW'

            self.location, self.normal, self.matrix = view_matrix(context, *self.mouse)

        elif preference.surface == 'CURSOR':
            self.type = 'CURSOR'

            cursor = context.scene.cursor
            matrix = cursor.rotation_euler.to_matrix().to_4x4()

            rotation = Matrix.Rotation(angle, 4, axis[preference.axis])
            matrix @= rotation

            self.location = cursor.location
            self.normal = Vector((0, 0, -1))
            self.matrix = matrix

        elif preference.surface == 'WORLD' or not selected:
            self.type = 'WORLD'

            matrix = planar_matrix(context)

            self.location = matrix.translation
            self.normal = matrix @ Vector((0, 0, -1))
            self.matrix = matrix

        types = {
            'GRID': preference.snap.grid,
            'VERT': preference.snap.verts,
            'EDGE': preference.snap.edges,
            'FACE': preference.snap.faces}

        types_enabled = [t for t in types if types[t]] if not preference.snap.grid and hit else ['GRID']

        if 'GRID' in types_enabled:
            self.grid = grid(self, context)

        self.points = points(self, context, types_enabled)

        bc.snap_type = self.type


    def update(self, context, mouse):
        preference = addon.preference()
        bc = context.scene.bc

        if not context.region_data:
            self.remove(force=True)

            return

        view = context.region_data.view_rotation.to_matrix().to_4x4()

        if self.exit:
            self.remove()

        else:
            self.mouse = Vector((mouse.x, mouse.y))

            if not bc.running:
                if self.obj and ((self.eval and bc.snap.display and not self.grid.display) or (self.type not in {'VIEW', 'CURSOR', 'WORLD'} and (not self.grid.display or (preference.snap.adaptive and bc.snap.display)))):
                    if self.eval and bc.snap.display:
                        self._eval_obj(context, self.obj)
                        self.eval = False

                    if self._ray_cast(context):
                        self._surface_matrix()

            if not bc.snap.display and not self.eval:
                self.eval = True

        if self.type == 'VIEW' and self._view_transform != view:
            self._view_transform = view
            self.location, self.normal, self.matrix = view_matrix(context, *self.mouse)

        self.grid.update(self, context)
        self.points.update(self, context)

        self.fade = self.grid.fade or self.points.fade

        bc.snap_type = self.type

        self.area_tag_redraw(context)


    def _ray_cast(self, context):
        preference = addon.preference()

        hit = False
        location = Vector()
        normal = Vector()
        face_index = -2
        obj = None

        if toolbar.option().active_only:
            hit, location, normal, face_index, obj, _ = ray.cast(*self.mouse, selected=True)

            if hit and self.obj != obj:
                self._eval_obj(context, obj)

        elif context.active_object and context.selected_objects:
            if self.obj != context.active_object:
                self._eval_obj(context, context.active_object)

            bm = bmesh.new()
            bm.from_mesh(self.mesh)

            hit, location, normal, face_index = ray.cast(*self.mouse, bmesh_data=bm)

            bm.free()

        if hit: # and face_index != self.face_index and ((self.grid.display and preference.snap.adaptive) or obj != self.obj):
            self.location = location
            self.normal = normal if round(normal.dot(self.normal), 3) != 1 else self.normal
            self.face_index = face_index

            # return True

        return hit


    def _eval_obj(self, context, obj):
        bc = context.scene.bc

        self.obj = obj

        self.mesh = obj.evaluated_get(context.evaluated_depsgraph_get()).data.copy()
        self.mesh.transform(self.obj.matrix_world)
        self.mesh.bc.removeable = True


    def _surface_matrix(self):
        preference = addon.preference()

        matrix = self.obj.matrix_world.decompose()[1].to_matrix().to_4x4()

        orient_method = 'EDIT' if self.obj.mode == 'EDIT' and preference.behavior.orient_active_edge else preference.behavior.orient_method
        self.matrix = surface_matrix(self.obj, matrix, self.location, self.normal, Vector(), orient_method if self.grid.display else 'LOCAL', self.face_index)[1]


    def remove(self, force=False):
        self.obj = None
        self.mesh = None

        self.eval = False

        self.grid.exit = True
        self.points.exit = True

        if force:
            self.grid.remove(force=True)
            self.points.remove(force=True)


class grid:
    exit: bool = False
    display: bool = True


    def __init__(self, handler, context):
        preference = addon.preference()

        handler.init_alpha(self, preference.display.grid_fade_time_in, preference.display.grid_fade_time_out)

        self._color = Vector(preference.color.grid_wire[:])

        self._count = preference.snap.grid_units
        self._increment = preference.snap.increment

        self._size = 0.0
        self._indices = ((0, 1, 3), (0, 3, 2))
        self._uv = ((-1, -1), (1, -1), (-1, 1), (1, 1))

        self.update(handler, context)

        self._time = time()
        self._shader = GPUShader(shader.load('grid.vert'), shader.load('grid.frag'))
        self._build_batch = True

        shader.handlers.append(self)

        self.handler = SpaceView3D.draw_handler_add(self._draw_handler, (), 'WINDOW', 'POST_VIEW')


    def update(self, handler, context):
        preference = addon.preference()

        if self.exit:
            self.remove()

        else:
            transform = handler.matrix if handler.type != 'VIEW' else context.region_data.view_rotation.to_matrix().to_4x4()
            intersect = view3d.intersect_plane(*handler.mouse, handler.location, transform)

            while not intersect:
                transform = transform @ Matrix.Rotation(radians(90), 4, 'X' if preference.axis == 'Z' else 'Y')
                intersect = view3d.intersect_plane(*handler.mouse, handler.location, transform)

            else:
                self.transform = transform
                self.intersect = intersect

                if handler.matrix != self.transform:
                    handler.matrix = self.transform

            self._count = preference.snap.grid_units if preference.snap.grid else 0
            self._increment = preference.snap.increment
            self._update_size()

        # self._background = Vector(preference.color.grid[:-1]) # TODO
        handler.update_alpha(self, self._color[-1], preference.display.grid_fade_time_out)

        self._thickness = 1 if not preference.display.thick_wire else 1.8
        self._thickness *= preference.display.wire_width


    def _update_size(self):
        preference = addon.preference()

        size = self._count * self._increment
        if self._size != size:
            self._size = size

            offset = self._size * 0.5
            offset_z = 0.0 # preference.shape.offset # TODO: intersect calc needs offset
            self._frame = tuple([tuple([offset * self._uv[i][j] if j < 2 else offset_z for j in range(3)]) for i in range(4)])

            self._build_batch = True


    def _draw_handler(self):
        method_handler(self._draw,
            identifier = 'Grid Draw',
            exit_method = self.remove,
            return_result = False)


    def _draw(self):
        preference = addon.preference()

        if not self.handler or not preference.snap.grid:
            return

        region_data = bpy.context.region_data

        self._shader.bind()

        self._shader.uniform_float('projection', region_data.window_matrix @ region_data.view_matrix)
        self._shader.uniform_float('transform', self.transform)
        self._shader.uniform_float('intersect', self.intersect)

        self._shader.uniform_float('count', self._count)
        self._shader.uniform_float('increment', self._increment)
        self._shader.uniform_float('size', self._size)

        self._shader.uniform_float('color', self._color[:-1])
        # self._shader.uniform_float('background', self._background) # TODO
        self._shader.uniform_float('alpha', self.alpha)

        self._shader.uniform_float('thickness', self._thickness)

        if self._build_batch:
            self._batch = shader.batch(self._shader, 'TRIS', {'frame': self._frame}, indices=self._indices)
            self._build_batch = False

        glEnable(GL_BLEND)

        self._batch.draw(self._shader)

        glDisable(GL_BLEND)


    def remove(self, force=False):
        if self.handler and (not self.fade or force):
            self.fade = False
            self.handler = SpaceView3D.draw_handler_remove(self.handler, 'WINDOW')

            shader.handlers = [handler for handler in shader.handlers if handler != self]


class points:
    active = None

    exit: bool = False


    @staticmethod
    def _grid_intersect(handler, increment):
        return Vector((*math.increment_round_2d(*handler.grid.intersect[:-1], increment), handler.grid.intersect[2]))


    @staticmethod
    def _reset_point(handler, point):
        preference = addon.preference()

        point.exit = False

        handler.init_alpha(point, preference.display.dot_fade_time_in, preference.display.dot_fade_time_out)


    def __init__(self, handler, context, types):
        preference = addon.preference()

        self._type = types
        self.handler = []

        self.fade = True
        self.face_index = handler.face_index

        if 'GRID' in self._type:
            self.handler.append(point(handler, context, 'GRID', self._grid_intersect(handler, preference.snap.increment)))
            self.active = self.handler[0]

        else:
            self._init_face_points(handler, context)

        self.update(handler, context)


    def _init_face_points(self, handler, context):
        face = handler.mesh.polygons[handler.face_index]
        locations = [point.location for point in self.handler]

        if 'VERT' in self._type:
            for index in face.vertices:
                location = handler.matrix.inverted() @ handler.mesh.vertices[index].co

                if location in locations:
                    self._reset_point(handler, self.handler[locations.index(location)])

                    continue

                self.handler.append(point(handler, context, 'VERT', location))

        if 'EDGE' in self._type:
            for index, key in enumerate(face.edge_keys):
                vert1 = handler.mesh.vertices[key[0]].co
                vert2 = handler.mesh.vertices[key[1]].co

                location = handler.matrix.inverted() @ ((vert1 + vert2) / 2)

                if location in locations:
                    self._reset_point(handler, self.handler[locations.index(location)])

                    continue

                self.handler.append(point(handler, context, 'EDGE', location))
                self.handler[-1].edge_index = index

        if 'FACE' in self._type:
            location = handler.matrix.inverted() @ face.center

            if location in locations:
                self._reset_point(handler, self.handler[locations.index(location)])

                return

            self.handler.append(point(handler, context, 'FACE', location))


    def update(self, handler, context):
        preference = addon.preference()
        bc = context.scene.bc

        self.handler = [point for point in self.handler if point.handler]
        self.fade = bool(len(self.handler))

        if self.exit:
            self.remove()

        intersect = view3d.intersect_plane(*handler.mouse, handler.location, handler.matrix)

        for point in self.handler:
            point.highlight = False
            position = view3d.location3d_to_location2d(point.transform @ point.location)
            point.distance = (position - handler.mouse).length if position else 1024

            if point.type == 'GRID' and not point.exit:
                intersect = None
                location = self._grid_intersect(handler, preference.snap.increment)

                if point.location == location:
                    continue

                point.location = location
                point.build_batch = True

            elif self.face_index != handler.face_index:
                point.exit = True

        if not self.exit and self.face_index != handler.face_index:
            self.face_index = handler.face_index
            self._init_face_points(handler, context)

        distances = [point.distance for point in self.handler]

        if distances:
            closest = self.handler[distances.index(min(distances))]
            closest.highlight = closest.distance < preference.display.snap_dot_size * screen.dpi_factor() * preference.display.snap_dot_factor * 2 if closest.type != 'GRID' else True

            if closest.highlight and not self.exit:
                self.active = closest

                bc.snap.hit = True
                bc.snap.type = closest.type
                bc.snap.location = closest.transform @ closest.location
                bc.snap.normal = handler.normal if closest.type != 'GRID' else closest.transform @ Vector((0, 0, -1))

                if hasattr(handler.obj, 'matrix_world'):
                    rot_mat = handler.obj.matrix_world.decompose()[1].to_matrix().to_4x4()
                    bc.snap.matrix = closest.transform if closest.type == 'GRID' else surface_matrix(handler.obj, rot_mat, handler.location, Vector(bc.snap.normal[:]), Vector(bc.snap.location[:]), handler.face_index)
                else:
                    bc.snap.matrix = closest.transform

            elif bc.snap.hit and self.active:
                bc.snap.hit = False
                bc.snap.type = ''
                bc.snap.location = Vector()
                bc.snap.normal = Vector()
                bc.snap.matrix = Matrix()

                self.active = None

        for point in self.handler:
            point.update(handler, context)

            if not intersect:
                continue

            max_dim = 2

            if handler.obj:
                max_dim = max(handler.obj.dimensions[:])

            region_fade = 1.0 - (point.location - intersect).length / (preference.snap.fade_distance * max_dim)

            if region_fade < 0.0:
                region_fade = 0.0

            # TODO: overlap fade difference

            point.alpha *= region_fade


    def remove(self, force=False):
        remove = []
        for index, handler in enumerate(self.handler):
            handler.exit = True

            if force:
                remove.append(index)

        for index in remove:
            if self.handler[index].handler:
                self.handler[index].remove(force=True)


class point:
    exit: bool = False

    highlight: bool = False
    distance: float = 0.0

    build_batch: bool = True


    def __init__(self, handler, context, type, location):
        preference = addon.preference()

        self.type = type

        self.location = location

        handler.init_alpha(self, preference.display.dot_fade_time_in, preference.display.dot_fade_time_out)

        self.update(handler, context)

        self._time = time()
        self._shader = GPUShader(shader.load('point.vert'), shader.load('point.frag'))
        self._build_batch = True

        shader.handlers.append(self)

        self.handler = SpaceView3D.draw_handler_add(self._draw_handler, (), 'WINDOW', 'POST_VIEW')


    def update(self, handler, context):
        preference = addon.preference()

        if self.exit:
            self.remove()

        if not self.exit:
            self.transform = handler.matrix if self.type != 'GRID' else handler.grid.transform

        self._size = preference.display.snap_dot_size * screen.dpi_factor()
        self._size *= 1 if not self.highlight or self.type == 'GRID' else 1.5

        self._color = preference.color.snap_point[:] # if not self.highlight else preference.color.snap_point_highlight[:-1]
        self._outline = (0.1, 0.1, 0.1) if not self.highlight else preference.color.snap_point_highlight[:-1]

        handler.update_alpha(self, self._color[-1], preference.display.dot_fade_time_out)


    def _draw_handler(self):
        method_handler(self._draw,
            identifier = 'Point Draw',
            exit_method = self.remove,
            return_result = False)


    def _draw(self):
        if not self.handler:
            return

        region_data = bpy.context.region_data

        self._shader.bind()

        self._shader.uniform_float('projection', region_data.window_matrix @ region_data.view_matrix)
        self._shader.uniform_float('transform', self.transform)

        self._shader.uniform_float('color', self._color[:-1])
        self._shader.uniform_float('outline', self._outline)
        self._shader.uniform_float('alpha', self.alpha)

        if self.build_batch:
            self._batch = shader.batch(self._shader, 'POINTS', {'vert': [self.location]})
            self.build_batch = False

        glEnable(GL_BLEND)
        glPointSize(self._size)

        self._batch.draw(self._shader)

        glPointSize(1)
        glDisable(GL_BLEND)


    def remove(self, force=False):
        if self.handler and (not self.fade or force):
            self.fade = False
            self.handler = SpaceView3D.draw_handler_remove(self.handler, 'WINDOW')

            shader.handlers = [handler for handler in shader.handlers if handler != self]


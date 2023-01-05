import bpy

from bpy.types import Operator
from bpy.props import BoolProperty

from ... utility import active_tool


class BC_OT_box(Operator):
    bl_idname = 'bc.box'
    bl_label = 'Box'
    bl_description = 'Set the shape to box'


    def execute(self, context):
        for tool in context.workspace.tools:
            if tool.idname == 'BoxCutter' and tool.mode == active_tool().mode:
                tool.operator_properties('bc.draw_shape').shape_type = 'BOX'

                context.workspace.tools.update()
                break

        return {'FINISHED'}


class BC_OT_circle(Operator):
    bl_idname = 'bc.circle'
    bl_label = 'Circle'
    bl_description = 'Set the shape to circle'


    def execute(self, context):
        for tool in context.workspace.tools:
            if tool.idname == 'BoxCutter' and tool.mode == active_tool().mode:
                tool.operator_properties('bc.draw_shape').shape_type = 'CIRCLE'

                context.workspace.tools.update()
                break

        return {'FINISHED'}


class BC_OT_ngon(Operator):
    bl_idname = 'bc.ngon'
    bl_label = 'Ngon'
    bl_description = 'Set the shape to ngon'


    def execute(self, context):
        for tool in context.workspace.tools:
            if tool.idname == 'BoxCutter' and tool.mode == active_tool().mode:
                tool.operator_properties('bc.draw_shape').shape_type = 'NGON'

                context.workspace.tools.update()
                break

        return {'FINISHED'}


class BC_OT_custom(Operator):
    bl_idname = 'bc.custom'
    bl_label = 'Custom'
    bl_description = 'Set the shape to custom'

    set: BoolProperty(default=False)


    def execute(self, context):
        bc = context.window_manager.bc
        set = False

        for tool in context.workspace.tools:
            if tool.idname == 'BoxCutter' and tool.mode == active_tool().mode:
                option = tool.operator_properties('bc.draw_shape')

                context.workspace.tools.update()

                if self.set and context.active_object and option.shape_type == 'CUSTOM':
                    bc.shape = context.active_object
                    self.report({'INFO'}, F'Custom Shape: {bc.shape.name}')
                    set = True

                if not self.set:
                    option.shape_type = 'CUSTOM'

                    if not bc.shape and context.active_object:
                        bc.shape = context.active_object
                        self.report({'INFO'}, F'Custom Shape: {bc.shape.name}')

                break

        if self.set and not set:
            return {'PASS_THROUGH'}


        return {'FINISHED'}

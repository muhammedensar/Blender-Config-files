import bpy

from bpy.types import Panel

from . import general, start_operation
from ... utility import addon, active_tool


class BC_PT_help(Panel):
    bl_label = 'Help'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = '.workspace'
    bl_options = {'HIDE_HEADER'}


    @classmethod
    def poll(cls, context):

        mode = {'OBJECT': 'OBJECT', 'EDIT_MESH': 'EDIT'}
        object_mode = context.active_object.mode if context.active_object else 'OBJECT'

        option = None
        for tool in context.workspace.tools:
            if tool.idname == 'BoxCutter' and mode[tool.mode] == object_mode:
                option = tool.operator_properties('bc.draw_shape')

        return bool(option)


    def draw(self, context):
        layout = self.layout


class BC_PT_help_npanel_tool(Panel):
    bl_label = 'Help'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'


    @classmethod
    def poll(cls, context):

        return BC_PT_help.poll(context)


    def draw(self, context):
        BC_PT_help.draw(self, context)


class BC_PT_help_npanel(Panel):
    bl_label = 'Help'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BoxCutter'
    bl_options = {'DEFAULT_CLOSED'}


    @classmethod
    def poll(cls, context):

        return BC_PT_help.poll(context)


    def draw(self, context):
        BC_PT_help.draw(self, context)

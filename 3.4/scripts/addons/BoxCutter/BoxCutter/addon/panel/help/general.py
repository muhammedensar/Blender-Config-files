import bpy

from bpy.types import Panel

from ... utility import active_tool, addon


# TODO: ctrl, alt, shift modifier key bahavior states
class BC_PT_help_general(Panel):
    bl_label = 'Help'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = '.workspace'
    bl_options = {'HIDE_HEADER'}
    bl_parent_id = 'BC_PT_help'


    def draw(self, context):
        layout = self.layout

        bc = context.window_manager.bc

        mode = {'OBJECT': 'OBJECT', 'EDIT_MESH': 'EDIT'}
        object_mode = context.active_object.mode if context.active_object else 'OBJECT'

        option = None
        for tool in context.workspace.tools:
            if tool.idname == 'BoxCutter' and mode[tool.mode] == object_mode:
                option = tool.operator_properties('bc.draw_shape')

        row = layout.row()
        row.alignment = 'RIGHT'
        row.operator('bc.help_link', text='', icon='QUESTION', emboss=False)

        if not bc.running:
            layout.label(text='Hold LMB + Drag to draw a shape')

            if addon.preference().behavior.snap:
                layout.label(text='Hold Ctrl - Display Snapping Points')

        else:
            if option.operation == 'NONE' or option.operation == 'EXTRUDE' and not option.modified:
                layout.label(text='LMB / Spacebar- Confirm')

                layout.separator()

                layout.label(text='Shift + Confirm - Keep Shape')

                layout.separator()

                layout.label(text='RMB / Esc - Cancel')

            elif option.operation == 'DRAW':
                layout.label(text='LMB Release - Extrude')
                layout.label(text='RMB - Lock Shape')

            elif option.operation != 'NONE':
                layout.label(text='LMB - Lock')
                layout.label(text='RMB - Cancel')

            elif option.operation == 'DRAW' and option.shape_type == 'NGON':
                layout.label(text='LMB - Place Point')
                layout.label(text='RMB / Backspace - Remove Point')

            layout.separator()
            layout.label(text='C / Alt + Scroll - Cycle Cutters')

            if option.shape_type == 'NGON':

                layout.separator()
                layout.label(text='CTRL - Angle Snapping')
                layout.label(text='C - Toggle Cyclic')


            layout.separator()
            layout.label(text='Tilde / R - Rotate 90 Fitted')
            layout.label(text='TAB - Lock Shape')
            layout.label(text='L - Live Toggle')
            layout.label(text='E - Extrude')
            layout.label(text='O - Offset')

            layout.separator()
            layout.label(text='H - Toggle Wires Only')

            layout.separator()
            layout.label(text='X - Slice')
            layout.label(text='Z - Inset')
            layout.label(text='J - Join')
            layout.label(text='K - Knife')
            layout.label(text='A - Make')
            layout.label(text='Y - Extract')

            layout.label(text=F'V - {"Array" if not option.operation == "ARRAY" else "Clear Array"}')

            if option.operation == 'ARRAY':
                layout.label(text='Scroll / - / + - Adjust Count')

            layout.label(text=F'T - {"Solidify" if not option.operation == "SOLIDIFY" else "Clear Solidify"}')

            layout.label(text=F'B - {"Bevel" if not option.operation == "BEVEL" else "Clear Bevel"}')

            if option.operation == 'BEVEL':
                layout.label(text='Scroll / - / + - Adjust Segments')

            layout.label(text='Q - Contour Bevel')

            layout.separator()
            layout.label(text='. - Change origin (period)')

            if option.operation == 'SOLIDIFY':
                layout.label(text='1, 2, 3 - Offset (-1, 0, 1)')

            else:
                layout.label(text='1, 2, 3 - Mirror (X, Y, Z)')

        if option.operation == 'NONE':
            layout.separator()
            layout.label(text='D - Pie Menu')
            layout.label(text='Ctrl + D - Behavior Helper')


class BC_PT_help_general_npanel_tool(Panel):
    bl_label = 'Interaction'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'
    bl_parent_id = 'BC_PT_help_npanel_tool'
    bl_options = {'HIDE_HEADER'}


    def draw(self, context):
        BC_PT_help_general.draw(self, context)


class BC_PT_help_general_npanel(Panel):
    bl_label = 'Interaction'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BoxCutter'
    bl_parent_id = 'BC_PT_help_npanel'
    bl_options = {'HIDE_HEADER'}


    def draw(self, context):
        BC_PT_help_general.draw(self, context)

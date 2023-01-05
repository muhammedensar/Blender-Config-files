import bpy

from bpy.types import Panel

from .. keymap import keys
from .. utility import active_tool, addon, names


class BC_PT_mode(Panel):
    bl_label = 'Mode'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BoxCutter'

    @classmethod
    def poll(cls, context):
        return active_tool().mode in {'OBJECT', 'EDIT_MESH'}


    def draw(self, context):
        preference = addon.preference()

        layout = self.layout
        bc = context.window_manager.bc

        option = None
        for tool in context.workspace.tools:
            if tool.idname == 'BoxCutter' and tool.mode == active_tool().mode:
                option = tool.operator_properties('bc.draw_shape')

                break

        if not option:
            hotkey = [kmi[1] for kmi in keys if kmi[1].idname == 'bc.topbar_activate'][0]

            shift = 'Shift' if hotkey.shift else ''
            ctrl = 'Ctrl' if hotkey.ctrl else ''
            alt = 'Alt' if hotkey.alt else ''
            cmd = 'Cmd+' if hotkey.oskey else '+'

            shift += '+' if hotkey.ctrl and hotkey.shift else ''
            ctrl += '+' if hotkey.alt and hotkey.ctrl else ''
            alt += '+' if hotkey.oskey and hotkey.alt else ''

            key = hotkey.type

            row = layout.row()
            row.alignment = 'LEFT'
            row.operator('bc.topbar_activate', emboss=False)
            layout.label(text=F'\u2022 {shift+ctrl+alt+cmd+key}')

            return

        row = layout.row(align=True)
        row.scale_x = 2
        row.scale_y = 1.5
        row.prop(option, 'mode', text='', expand=True)

import bpy

from bpy.types import Menu
from bpy.utils import register_class, unregister_class

from . import icon
from . utility import active_tool, addon, active_tool


class BC_MT_pie(Menu):
    bl_label = 'BoxCutter'


    @classmethod
    def poll(cls, context):

        return active_tool().idname == 'BoxCutter'


    def draw(self, context):
        layout = self.layout.menu_pie()

        preference = addon.preference()
        bc = context.window_manager.bc

        option = None
        for tool in context.workspace.tools:
            if tool.idname == 'BoxCutter' and tool.mode == active_tool().mode:
                option = tool.operator_properties('bc.draw_shape')

                if option.shape_type != 'CIRCLE':
                    layout.operator('bc.circle', icon='MESH_CIRCLE')
                else:
                    layout.operator('bc.custom', icon='FILE_NEW')

                layout.separator()

                if option.shape_type != 'NGON':
                    layout.operator('bc.ngon', icon='MOD_SIMPLIFY')
                else:
                    layout.operator('bc.custom', icon='FILE_NEW')

                row = layout.row(align=True)
                row.scale_x = 1.5
                row.scale_y = 1.5

                icons = {
                    'CUT': icon.id('red'),
                    'SLICE': icon.id('yellow'),
                    'INSET': icon.id('purple'),
                    'JOIN': icon.id('green'),
                    'KNIFE': icon.id('blue'),
                    'EXTRACT': icon.id('black'),
                    'MAKE': icon.id('grey')}

                # row.popover(panel='BC_PT_helper', text='', icon_value=icons[option.mode])
                row.popover(panel='BC_PT_mode', text='', icon_value=icons[option.mode])
                row.separator()

                icons = {
                    'OBJECT': 'OBJECT_DATA',
                    'CURSOR': 'PIVOT_CURSOR',
                    'CENTER': 'VIEW_PERSPECTIVE'}

                row.prop(option, 'align_to_view', text='', icon='VIEW_ORTHO' if option.align_to_view else 'VIEW_PERSPECTIVE')
                row.popover(panel='BC_PT_surface', text='', icon=icons[preference.surface])
                row.separator()

                row.prop(preference.behavior, 'snap', text='', icon=F'SNAP_O{"N" if preference.behavior.snap else "FF"}')

                row.popover('BC_PT_snap', text='', icon='SNAP_GRID')
                row.separator()

                row.popover(panel='BC_PT_settings', text='', icon='PREFERENCES')
                row.prop(option, 'live', text='', icon='PLAY' if not option.live else 'PAUSE')

                sub = row.row(align=True)
                sub.scale_x = 0.85
                sub.label(text=' ')
                sub.label(text=' ')

                layout.separator()
                row = layout.row()
                column = row.column(align=True)
                column.scale_x = 1.1
                column.scale_y = 1.5

                for i in range(6):
                    column.label(text=' ')

                column.prop(bc, 'start_operation', text='', expand=True, icon_only=True)

                icons = {
                    'NONE': 'LOCKED',
                    'DRAW': 'GREASEPENCIL',
                    'EXTRUDE': 'ORIENTATION_NORMAL',
                    'OFFSET': 'MOD_OFFSET',
                    'MOVE': 'RESTRICT_SELECT_ON',
                    #'ROTATE': 'DRIVER_ROTATIONAL_DIFFERENCE',
                    #'SCALE': 'FULLSCREEN_EXIT',
                    'ARRAY': 'MOD_ARRAY',
                    'SOLIDIFY': 'MOD_SOLIDIFY',
                    'BEVEL': 'MOD_BEVEL',
                    'MIRROR': 'MOD_MIRROR'}

                column.popover(panel='BC_PT_operation', text='', icon=icons[option.operation])
                column.separator()

                if option.shape_type != 'BOX':
                    layout.operator('bc.box', icon='MESH_PLANE')
                else:
                    layout.operator('bc.custom', icon='FILE_NEW')

                break

classes = [
    BC_MT_pie]


def register():

    for cls in classes:
        register_class(cls)


def unregister():

    for cls in classes:
        unregister_class(cls)

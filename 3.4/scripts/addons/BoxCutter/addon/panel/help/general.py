import time
import bpy

from bpy.types import Panel

from .... utility import tool, addon
from ... import toolbar
from ... operator.shape.utility import tracked_events, tracked_states


# TODO: ctrl, alt, shift modifier key bahavior states
class BC_PT_help_general(Panel):
    bl_label = F'Help{" " * 44}{toolbar.version}'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = '.workspace'
    bl_options = {'HIDE_HEADER'}
    bl_parent_id = 'BC_PT_help'


    def draw(self, context):
        preference = addon.preference()
        bc = context.scene.bc
        op = toolbar.option()

        unmodified = op.operation in {'DRAW', 'EXTRUDE'} and not tracked_states.modified
        indentation = '           '
        sep = '-   '
        nav_type = 'Rotate' if not tracked_events.shift else 'Pan'
        cut = 'Lazorcut' if tracked_states.thin else 'Cut'
        single_selected = len(context.selected_objects) == 1

        layout = self.layout

        row = layout.row()
        if not self.is_popover:
            row.label(text=F'{indentation * 3}{toolbar.version}')

        sub = row.row()
        sub.alignment = 'RIGHT'
        ot = sub.operator('bc.help_link', text='', icon='QUESTION', emboss=False)

        if self.is_popover or context.region.type == 'UI':
            ot.use_url = True

        if not bc.running:
            edit_mode = tool.active().mode == 'EDIT_MESH'
            use_make = not context.selected_objects[:] and not edit_mode

            if use_make:
                row = layout.row()
                row.alert = True if op.mode != 'MAKE' else False
                row.label(text=F'Select Mesh to {"Cut" if op.mode != "MAKE" else "Align"}', icon='INFO') # icon='ERROR')

                # row = layout.row()
                # row.alert = True if op.mode != 'MAKE' else False
                # row.label(text='  Using make & Aligning to floor')

            elif preference.surface == 'OBJECT' and not op.active_only:
                layout.label(text=F'Draw On{" the" if single_selected else ""} Mesh{"" if single_selected else "es"} to {"Cut" if op.mode != "MAKE" else "Align"}', icon='INFO')
                layout.label(text='           Off Mesh: View Align')

            elif preference.surface == 'VIEW':
                layout.label(text=F'{"Cutting" if op.mode != "MAKE" else "Aligning to"} View-Aligned Only', icon='INFO')

            elif not op.active_only:
                layout.label(text='Adjust Surface Options', icon='INFO')

            else:
                layout.label(text=F'{"Cutting" if op.mode != "MAKE" else "Aligning to"} Only Active', icon='INFO')

            layout.separator()

            make = op.mode == 'MAKE'
            layout.label(text=F'{sep}{op.mode.title() if not use_make else "Make"} {"Object" if single_selected or op.active_only else "Selected" if not make and not use_make else ""}', icon='MOUSE_LMB_DRAG')

            layout.separator()

            if addon.preference().snap.enable and not bc.snap.operator:
                layout.label(text='Enable Snapping', icon='EVENT_CTRL')
                layout.separator()

            elif bc.snap.operator and hasattr(bc.snap.operator, 'grid_handler'):
                grid_handler = bc.snap.operator.grid_handler

                row = layout.row(align=True)
                row.alignment = 'LEFT'
                row.label(text='/', icon='EVENT_TAB')
                row.label(text=F'{sep}{"Freeze" if not grid_handler.frozen else "Unfreeze"}', icon='EVENT_SPACEKEY')

                layout.label(text=F'{sep}Align', icon='EVENT_A')

                if grid_handler.snap_type == 'DOTS':
                    if grid_handler.nearest_dot:
                        row = layout.row(align=True)
                        row.label(text='', icon='EVENT_CTRL')
                        row.label(text='Cycle Dot alignment', icon='MOUSE_MMB')

                        layout.label(text='Switch to Grid', icon='EVENT_G')

                    row = layout.row(align=True)
                    row.label(text='', icon='EVENT_SHIFT')
                    row.label(text='Subdivide face', icon='MOUSE_MMB')

                else:
                    if grid_handler.mode != 'NONE' or (grid_handler.mode == 'MOVE' and not grid_handler.mode.frozen):
                        layout.label(text='Confirm operation', icon='MOUSE_LMB')
                        layout.label(text='Cancel operation', icon='MOUSE_RMB')

                    if grid_handler.mode != 'MOVE':
                        layout.label(text=F'{sep}Move', icon='EVENT_G')

                    if grid_handler.mode != 'SCALE':
                        layout.label(text=F'{sep}Scale', icon='EVENT_S')

                    if grid_handler.mode != 'ROTATE':
                        layout.label(text=F'{sep}Rotate', icon='EVENT_R')

                    else:
                        row = layout.row(align=True)

                        if grid_handler.rotation_axis != 'X':
                            row.label(text='', icon='EVENT_X')

                        if grid_handler.rotation_axis != 'Y':
                            row.label(text='', icon='EVENT_Y')

                        if grid_handler.rotation_axis != 'Z':
                            row.label(text='', icon='EVENT_Z')

                        row.label(text=F'{sep}Change Axis')

                    if grid_handler.mode != 'EXTEND':

                        row = layout.row(align=True)
                        row.alignment = 'LEFT'
                        row.label(text='', icon='EVENT_CTRL')
                        row.label(text='/', icon='MOUSE_RMB')
                        row.label(text=F'{sep}Extend', icon='EVENT_E')

                    layout.label(text='Change Unit Size', icon='MOUSE_MMB')

                    row = layout.row(align=True)
                    row.label(text='', icon='EVENT_SHIFT')
                    row.label(text='Subdivide', icon='MOUSE_MMB')

                    row = layout.row(align=True)
                    row.alignment = 'LEFT'
                    row.label(text='', icon='EVENT_SHIFT')
                    row.label(text=F'{sep}Knife Project', icon='EVENT_K')

                layout.label(text=F'{sep}Disable Snapping', icon='EVENT_ESC')
                layout.separator()

            layout.label(text=F'{sep}Box Helper' if preference.keymap.d_helper else F'{sep}Pie Menu', icon='EVENT_D')

            row = layout.row(align=True)
            row.label(text='', icon='EVENT_ALT')
            row.label(text=F'{sep}Change Shape Type', icon='MOUSE_MMB')

            row = layout.row(align=True)
            row.label(text='', icon='EVENT_CTRL')
            row.label(text=F'{sep}Pie Menu' if preference.keymap.d_helper else F'{sep}Box Helper', icon='EVENT_D')

            row = layout.row(align=True)
            row.label(text='', icon='EVENT_SHIFT')
            row.label(text=F'{sep}Surface Options', icon='EVENT_V')

            if op.shape_type == 'CUSTOM':
                layout.separator()
                layout.label(text=F'{sep}Active Object to Custom', icon='EVENT_C')

            return

        if tracked_events.mmb:
            layout.label(text=F'{sep}Confirm {nav_type}', icon='MOUSE_MMB')

            if not tracked_events.shift:
                layout.separator()

                layout.label(text=F'{sep}Axis Snap', icon='EVENT_ALT')

            return

        if op.operation != 'NONE':
            icon = 'MOUSE_LMB_DRAG' if tracked_events.lmb else 'MOUSE_MOVE'
            layout.label(text=F'{sep}Adjust {op.operation.title()}', icon=icon)

        if tracked_states.shape_type == 'NGON' and op.operation == 'DRAW':
            layout.label(text=F'{sep}Confirm Point', icon='MOUSE_LMB')

        elif tracked_events.lmb and op.operation == 'NONE' and not tracked_states.rmb_lock:
            cut_type = cut if op.operation != 'MAKE' else 'Shape'
            layout.label(text=F'{sep}Confirm {cut_type if op.operation != "JOIN" else "Join"}', icon='MOUSE_LMB')

        elif tracked_events.lmb and not tracked_states.rmb_lock:
            if unmodified and op.operation == 'EXTRUDE':
                cut_type = cut if op.operation != 'MAKE' else 'Shape'
                layout.label(text=F'{sep}Confirm {cut_type if op.operation != "JOIN" else "Join"}', icon='MOUSE_LMB')
            else:
                layout.label(text=F'{sep}Confirm {op.operation.title()}', icon='MOUSE_LMB')

        elif op.operation != 'NONE' and not tracked_states.thin:
            layout.label(text=F'{sep}Confirm {op.operation.title()}', icon='MOUSE_LMB')

        elif not tracked_states.rmb_lock:
            cut_type = cut if op.operation != 'MAKE' else 'Shape'
            layout.label(text=F'{sep}Confirm {cut_type if op.operation != "JOIN" else "Join"}', icon='MOUSE_LMB')

        layout.label(text=F'{sep}{nav_type} View', icon='MOUSE_MMB')

        if (tracked_states.shape_type == 'NGON' or bc.operator.ngon_fit) and not bc.operator.extruded and tracked_states.operation in {'NONE', 'DRAW'}:
            if len(bc.shape.data.vertices) > 2:
                layout.label(text=F'{sep}{"Lock Shape" if op.operation == "DRAW" else "Adjust Point"}', icon='MOUSE_RMB')
                layout.label(text=F'{sep}Backspace Point', icon='BACK')
            else:
                layout.label(text=F'{sep}Cancel', icon='MOUSE_RMB')

        else:
            cancel_type = '' if op.operation == 'NONE' or not tracked_states.modified else F' {op.operation.title()}'
            layout.label(text=F'{sep}Lock Shape' if tracked_events.lmb and op.operation != 'NONE' else F'{sep}Cancel{cancel_type}', icon='MOUSE_RMB')

        layout.separator()

        if op.operation in {'MOVE', 'ROTATE', 'SCALE', 'ARRAY'}:
            layout.separator()

            row = layout.row(align=True)

            if bc.axis != 'X':
                row.label(text='', icon='EVENT_X')

            if bc.axis != 'Y':
                row.label(text='', icon='EVENT_Y')

            if bc.axis != 'Z':
                row.label(text='', icon='EVENT_Z')

            row.label(text=F'{sep}Change Axis')

        if op.operation in {'ARRAY', 'SOLIDIFY', 'BEVEL', 'TAPER'}:
            row = layout.row(align=True)
            row.label(text='', icon='EVENT_SHIFT')
            row.label(text=F'{sep}Reset Adjustment', icon='EVENT_R')

        layout.separator()

        if op.operation != 'NONE':
            layout.label(text=F'{sep}Lock Shape', icon='EVENT_TAB')

        layout.label(text=F'{sep}{"Disable " if preference.display.wire_only else ""}Wire', icon='EVENT_H')

        layout.separator()

        if op.operation != 'MOVE':
            layout.label(text=F'{sep}Move', icon='EVENT_G')

        if op.operation != 'SCALE':
            layout.label(text=F'{sep}Scale', icon='EVENT_S')

        if op.operation != 'ROTATE':
            layout.label(text=F'{sep}Rotate', icon='EVENT_R')

        if op.operation == 'NONE':
            row = layout.row(align=True)
            row.label(text='', icon='EVENT_CTRL')
            row.label(text=F'{sep}Rotate by 90\u00b0', icon='EVENT_R')

        if op.shape_type == 'CUSTOM' or bc.shape.bc.applied or bc.shape.bc.applied_cycle:
            row = layout.row(align=True)
            row.label(text='', icon='EVENT_SHIFT')
            row.label(text=F'{sep}Rotate 90\u00b0 in Bounds', icon='EVENT_R')

        layout.separator()

        if op.operation != 'EXTRUDE':
            operation = 'Extrude' if op.operation != 'EXTRUDE' else 'Offset'
            layout.label(text=F'{sep}{operation}', icon='EVENT_E')

        if op.operation != 'OFFSET':
            row = layout.row(align=True)
            row.label(text=F'{sep}Offset', icon='EVENT_O')

        #if preference.shape.wedge:
        row = layout.row(align=True)
        #row.label(text='', icon='EVENT_SHIFT')
        row.label(text=F'{sep}{"Wedge"}', icon='EVENT_W')

        if op.operation != 'TAPER':
            row = layout.row(align=True)
            row.label(text='', icon='EVENT_SHIFT')

            if preference.keymap.shift_operation_enable and preference.keymap.shift_operation == 'TAPER':
                row.label(text=F'{sep}Taper')
            else:
                row.label(text=F'{sep}Taper', icon='EVENT_T')

        if op.shape_type != 'NGON' and preference.shape.taper != 1.0 or op.operation == 'TAPER':
            row = layout.row(align=True)
            row.label(text='', icon='EVENT_SHIFT')
            row.label(text=F'{sep}Reset{"/Exit" if op.operation == "TAPER" else ""} Taper', icon='EVENT_T')

        if op.shape_type == 'BOX':
            row = layout.row(align=True)
            row.label(text='', icon='EVENT_SHIFT')
            row.label(text=F'{sep}Grid Adjust', icon='EVENT_G')

        layout.separator()

        row = layout.row(align=True)
        row.label(text='', icon='EVENT_ALT')
        row.label(text=F'{sep}Switch Solver ({preference.behavior.boolean_solver.capitalize()})', icon='EVENT_E')

        row = layout.row(align=True)
        row.label(text='', icon='EVENT_ALT')
        row.label(text=F'{sep}Scroll Cutter History', icon='MOUSE_MMB')

        row = layout.row(align=True)
        row.label(text='', icon='EVENT_SHIFT')
        row.label(text=F'{sep}Flip Shape Z', icon='EVENT_F')

        row = layout.row(align=True)
        row.label(text=F'{sep}Cycle Cutters', icon='EVENT_C')

        layout.label(text=F'{sep}Live', icon='EVENT_L')

        layout.separator()

        if op.operation != 'BEVEL':
            layout.label(text=F'{sep}Bevel', icon='EVENT_B')

        else:
            layout.label(text=F'{sep}Contour Bevel', icon='EVENT_Q')
            row = layout.row(align=True)
            row.label(text='', icon='EVENT_SHIFT')
            row.label(text=F'{sep}Backface Bevel', icon='EVENT_Q')

        if op.operation != 'SOLIDIFY':
            layout.label(text=F'{sep}Solidify', icon='EVENT_T')

        if op.operation != 'ARRAY':
            layout.label(text=F'{sep}Array', icon='EVENT_V')

        elif op.operation == 'ARRAY' and not bc.shape.bc.array_circle:
            layout.label(text=F'{sep}Radial Array', icon='EVENT_V')

        layout.separator()

        if op.mode == 'CUT':
            layout.label(text=F'{sep}Slice', icon='EVENT_X')

        elif op.mode == 'SLICE':
            layout.label(text=F'{sep}Intersect', icon='EVENT_X')

        elif op.mode == 'INTERSECT':
            layout.label(text=F'{sep}Inset', icon='EVENT_X')

        else:
            layout.label(text=F'{sep}Cut', icon='EVENT_X')

        if op.mode == 'SLICE':
            row = layout.row(align=True)
            row.label(text='', icon='EVENT_ALT')
            row.label(text=F'{sep}{"Disable " if preference.behavior.recut else ""}Recut', icon='EVENT_X')

        if op.mode == 'INSET':
            row = layout.row(align=True)
            row.label(text='', icon='EVENT_ALT')
            row.label(text=F'{sep}{"Disable " if preference.behavior.inset_slice else ""}Inset Slice', icon='EVENT_X')

        if context.selected_objects or tool.active().mode == 'EDIT_MESH':
            layout.label(text=F'{sep}{"Knife" if op.mode != "KNIFE" else "Cut"}', icon='EVENT_K')
            layout.label(text=F'{sep}{"Join" if op.mode != "JOIN" else "Cut"}', icon='EVENT_J')
            layout.label(text=F'{sep}{"Inset" if op.mode != "INSET" else "Cut"}', icon='EVENT_I')
            layout.label(text=F'{sep}{"Extract" if op.mode != "EXTRACT" else "Cut"}', icon='EVENT_Y')
            layout.label(text=F'{sep}{"Make" if op.mode != "MAKE" else "Cut"}', icon='EVENT_A')

        layout.separator()

        if op.operation == 'NONE':
            layout.label(text=F'{sep}Pie Menu', icon='EVENT_D')

            row = layout.row(align=True)
            row.label(text='', icon='EVENT_CTRL')
            row.label(text=F'{sep}Behavior Helper', icon='EVENT_D')

            row = layout.row(align=True)
            row.label(text='', icon='EVENT_ALT')
            row.label(text=F'{sep}Toggle Dots', icon='EVENT_D')

            # elif op.shape_type == 'CUSTOM':
                # layout.separator()
                # layout.label(text='Active Object as Custom Cutter', icon='EVENT_C')

        if op.operation != 'NONE' and op.operation == 'SOLIDIFY':
            layout.label(text=F'1 2 3   Solidify Type')
        else:
            layout.label(text=F'1 2 3   Mirror Axis (shift - flip)')

        layout.label(text='. (PERIOD)    Change origin')


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


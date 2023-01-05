import bpy

from bpy.types import PropertyGroup
from bpy.props import *

from . utility import update
from ... panel.utility import preset
from ... operator.shape.utility import change
from ... property.utility import names


def pie_hotkey(keymap, context):
    wm = context.window_manager
    active_keyconfig = wm.keyconfigs.active
    addon_keyconfig = wm.keyconfigs.addon

    for kc in (active_keyconfig, addon_keyconfig):
        for kmi in kc.keymaps['3D View Tool: BoxCutter'].keymap_items:
            if kmi.idname == 'wm.call_menu_pie' and kmi.properties.name == 'BC_MT_pie':
                kmi.ctrl = keymap.d_helper
            if kmi.idname == 'bc.helper':
                kmi.ctrl = not keymap.d_helper


class shift_operations(PropertyGroup):
    name: StringProperty(update=update.shift_operation_preset)
    operation: StringProperty(default='TAPER')

    draw: BoolProperty(
        name = 'Draw',
        description = '\n Allow shift operation during the draw operation',
        update = update.shift_in_operation,
        default = False)

    extrude: BoolProperty(
        name = 'Extrude',
        description = '\n Allow shift operation during the extrude operation',
        update = update.shift_in_operation,
        default = True)

    offset: BoolProperty(
        name = 'Offset',
        description = '\n Allow shift operation during the offset operation',
        update = update.shift_in_operation,
        default = True)

    move: BoolProperty(
        name = 'Move',
        description = '\n Allow shift operation during the move operation',
        update = update.shift_in_operation,
        default = False)

    rotate: BoolProperty(
        name = 'Rotate',
        description = '\n Allow shift operation during the rotate operation',
        update = update.shift_in_operation,
        default = False)

    scale: BoolProperty(
        name = 'Scale',
        description = '\n Allow shift operation during the scale operation',
        update = update.shift_in_operation,
        default = False)

    array: BoolProperty(
        name = 'Array',
        description = '\n Allow shift operation during the array operation',
        update = update.shift_in_operation,
        default = False)

    solidify: BoolProperty(
        name = 'Solidify',
        description = '\n Allow shift operation during the solidify operation',
        update = update.shift_in_operation,
        default = False)

    bevel: BoolProperty(
        name = 'Bevel',
        description = '\n Allow shift operation during the bevel operation',
        update = update.shift_in_operation,
        default = False)

    displace: BoolProperty(
        name = 'Displace',
        description = '\n Allow shift operation during the displace operation',
        update = update.shift_in_operation,
        default = False)

    taper: BoolProperty(
        name = 'Taper',
        description = '\n Allow shift operation during the taper operation',
        update = update.shift_in_operation,
        default = False)


class bc(PropertyGroup):
    allow_selection: BoolProperty(
        name = names['allow_selection'],
        description = '\n Preserve mouse click for viewport selection',
        update = change.allow_selection,
        default = True)

    edit_disable_modifiers: BoolProperty(
        name = names['edit_disable_modifiers'],
        description = ('\n Disable CTRL and SHIFT key modifiers for drawing shapes in edit mode, allows path selection\n'
                       ' Note: Disables repeat shape (edit mode)'),
        default = True)

    d_helper: BoolProperty(
        name = names['d_helper'],
        description = '\n Use the D Helper instead of the default pie menu',
        update = pie_hotkey,
        default = True)

    enable_surface_toggle: BoolProperty(
        name = names['enable_surface_toggle'],
        description = '\n Toggle surface draw method from Object to Cursor with Alt-W',
        default = False)

    alt_preserve: BoolProperty(
        name = 'Preserve Alt',
        description = '\n Preserve Alt for other navigational controls during cut',
        default = False)

    rmb_preserve: BoolProperty(
        name = 'Preserve RMB',
        description = '\n Preserve RMB for other navigational controls during cut',
        default = False)

    release_lock: BoolProperty(
        name = 'Release Lock',
        description = '\n Lock the shape (Tab) after the first mouse release\n\n SHIFT or CTRL - Additional Lock Options',
        update = update.release_lock,
        default = False)

    release_lock_lazorcut: BoolProperty(
        name = 'Release Lock Lazorcut',
        description = '\n Lock the shape after performing a lazorcut',
        default = False)

    release_lock_repeat: BoolProperty(
        name = names['release_lock_repeat'],
        description = '\n Lock the shape after performing a repeat',
        default = False)

    quick_execute: BoolProperty(
        name = names['quick_execute'],
        description = '\n Quickly execute cuts on release',
        default = False)

    make_active: BoolProperty(
        name = names['make_active'],
        description = '\n Make the shape active when holding shift to keep it',
        default = True)

    rmb_cancel_ngon: BoolProperty(
        name = 'RMB Cancel Ngon',
        description = '\n Cancel ngon on rmb click rather then remove points',
        default = False)

    ctrl_multiplier: FloatProperty(
        name = 'Ctrl Factor',
        description = '\n Holding Ctrl factors mouse influence during an operation by this amount.\n'
                      '  Note: Snapping overrides\n',
        min = 0,
        soft_max = 10,
        default = 5)

    alt_draw: BoolProperty(
        name = 'Alt Center',
        description = '\n Alt centers the cutter when held while drawing',
        default = True)

    shift_draw: BoolProperty(
        name = 'Shift Uniform',
        description = '\n Shift uniformely expands the cutter when held while drawing',
        default = True)

    scroll_adjust_circle: BoolProperty(
        name = names['scroll_adjust_circle'],
        description = '\n Shift + scroll wheel adjusts circle vert count when using circle',
        default = True)

    alt_scroll_shape_type: BoolProperty(
        name = names['alt_scroll_shape_type'],
        description = '\n Alt + scroll wheel change shape on the fly',
        update = change.alt_scroll_shape_type,
        default = True)

    enable_toolsettings: BoolProperty(
        name = 'Enable Tool Settings',
        description = '\n Enable tool settings area when activating boxcutter with the hotkey',
        default = True)

    view_pie: BoolProperty(
        name = 'View Pie',
        description = '\n Allow using the view pie with accent grave / tilde key',
        default = True)

    shift_operation_enable: BoolProperty(
        name = names['shift_operation_enable'],
        description = '\n Enable shift operation behavior',
        update = update.shift_operation,
        default = False)

    shift_operation: EnumProperty(
        name = names['shift_operation'],
        description = '\n Assign an operation to jump into when shift is held during other operations',
        items = [
            # ('DRAW', 'Draw', '', 'GREASEPENCIL', 0),
            # ('EXTRUDE', 'Extrude', '', 'ORIENTATION_NORMAL', 1),
            # ('OFFSET', 'Offset', '', 'MOD_OFFSET', 2),
            ('MOVE', 'Move', '', 'RESTRICT_SELECT_ON', 3),
            ('ROTATE', 'Rotate', '', 'DRIVER_ROTATIONAL_DIFFERENCE', 4),
            ('SCALE', 'Scale', '', 'FULLSCREEN_EXIT', 5),
            ('ARRAY', 'Array', '', 'MOD_ARRAY', 6),
            ('SOLIDIFY', 'Solidify', '', 'MOD_SOLIDIFY', 7),
            ('BEVEL', 'Bevel', '', 'MOD_BEVEL', 8),
            # ('DISPLACE', 'Displace', '', 'MOD_DISPLACE', 9),
            ('TAPER', 'Taper', '', 'FULLSCREEN_ENTER', 10)],
        update = update.shift_operation_presets,
        default = 'TAPER')

    shift_operation_preset: StringProperty(
        name = names['shift_operation_preset'],
        description = 'Currently active shift operation preset',
        update = update.shift_operation,
        default = '')

    ngon_last_line_threshold: IntProperty(
        name = names['ngon_last_line_threshold'],
        description = '\n Distance your mouse needs to be from the current position to snap point, aligning with the last line',
        subtype = 'PIXEL',
        min = 0,
        default = 5)

    repeat_threshold: IntProperty(
        name = names['repeat_threshold'],
        description = '\n Distance your mouse needs to be within start of cut in order to allow repeat.\n'
                      '  Note: 0 disables',
        subtype = 'PIXEL',
        min = 0,
        default = 5)

    repeat_single_click: BoolProperty(
        name = names['repeat_single_click'],
        description = '\n Only require a single click when holding CTRL to repeat',
        default = False)

    alternate_extrude: BoolProperty(
        name = 'Alternate Extrude',
        description = '\n Perform alternative extrude adjustment before the shape is locked or view is changed',
        default = False)

    shift_operation_presets: CollectionProperty(type=shift_operations)
    shift_in_operations: PointerProperty(type=shift_operations)


def label_row(path, prop, row, label=''):
    row.label(text=label if label else names[prop])
    row.prop(path, prop, text='')


def draw(preference, context, layout):
    keymap = context.window_manager.keyconfigs.user.keymaps['3D View']
    keymap_items = keymap.keymap_items

    row = layout.row()
    row.label(text=keymap_items['bc.tool_activate'].name)

    row.prop(keymap_items['bc.tool_activate'], 'type', text='', full_event=True)
    label_row(keymap_items['bc.tool_activate'].properties, 'swap_tools', layout.row(), label='Swap Active Tools')
    preset.shift_operation_draw(layout.row(align=True), context)
    label_row(preference.keymap, 'release_lock', layout.row(), label='Release Lock')
    label_row(preference.keymap, 'release_lock_lazorcut', layout.row(), label='Lazorcut Lock')
    label_row(preference.keymap, 'quick_execute', layout.row())

    label_row(preference.keymap, 'd_helper', layout.row())

    # label_row(preference.keymap, 'enable_surface_toggle', layout.row())
    label_row(preference.keymap, 'enable_toolsettings', layout.row(), label='Enable Topbar')
    label_row(preference.keymap, 'allow_selection', layout.row(), label='Allow Selection')
    label_row(preference.keymap, 'edit_disable_modifiers', layout.row())
    label_row(preference.keymap, 'view_pie', layout.row(), label='View Pie')

    label_row(preference.keymap, 'rmb_cancel_ngon', layout.row(), label='RMB Cancel Ngon')
    label_row(preference.keymap, 'rmb_preserve', layout.row(), label='Preserve RMB')

    label_row(preference.keymap, 'ctrl_multiplier', layout.row(), label='Ctrl Factor')

    label_row(preference.keymap, 'alt_preserve', layout.row(), label='Preserve Alt')
    label_row(preference.keymap, 'alt_draw', layout.row(), label='Alt Center')
    label_row(preference.keymap, 'alt_scroll_shape_type', layout.row())

    label_row(preference.keymap, 'shift_draw', layout.row(), label='Shift Uniform')
    label_row(preference.keymap, 'scroll_adjust_circle', layout.row())

    label_row(preference.keymap, 'alternate_extrude', layout.row(), label='Alternate Extrude')


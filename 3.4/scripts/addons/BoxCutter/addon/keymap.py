import bpy

from .. utility import addon

keys = []

def register():
    global keys

    wm = bpy.context.window_manager
    active_keyconfig = wm.keyconfigs.active
    addon_keyconfig = wm.keyconfigs.addon

    kc = addon_keyconfig
    if not kc:
        print('BoxCutter: keyconfig unavailable (in batch mode?), no keybinding items registered')
        return

    # Activate tool
    km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')

    kmi = km.keymap_items.new(idname='bc.tool_activate', type='W', value='PRESS', alt=True)
    keys.append((km, kmi))

    # Active Tool
    for kc in (active_keyconfig, addon_keyconfig):
        km = kc.keymaps.new(name='3D View Tool: BoxCutter', space_type='VIEW_3D')

        # Cursor 3D
        # kmi = km.keymap_items.new(idname='view3d.cursor3d', type='RIGHTMOUSE', value='PRESS', shift=True)
        # kmi.properties.orientation = 'GEOM'

        # Pie
        kmi = km.keymap_items.new(idname='wm.call_menu_pie', type='D', value='PRESS')
        kmi.properties.name = 'BC_MT_pie'

        # Behavior Helper
        kmi = km.keymap_items.new(idname='bc.helper', type='D', value='PRESS', ctrl=True)

        # Surface
        kmi = km.keymap_items.new(idname='wm.call_panel', type='V', value='PRESS', shift=True)
        kmi.properties.name = 'BC_PT_surface'
        # kmi.properties.keep_open = False

        # Draw shape
        kmi = km.keymap_items.new(idname='bc.shape_draw', type='LEFTMOUSE', value='ANY')
        kmi.map_type = 'TWEAK'

        # Draw shape
        kmi = km.keymap_items.new(idname='bc.shape_draw', type='LEFTMOUSE', value='ANY', alt=True)
        kmi.map_type = 'TWEAK'

        # Draw shape
        kmi = km.keymap_items.new(idname='bc.shape_draw', type='LEFTMOUSE', value='ANY', shift=True)
        kmi.map_type = 'TWEAK'

        # Draw shape
        kmi = km.keymap_items.new(idname='bc.shape_draw', type='LEFTMOUSE', value='ANY', alt=True, shift=True)
        kmi.map_type = 'TWEAK'

        # Draw shape
        kmi = km.keymap_items.new(idname='bc.shape_draw', type='LEFTMOUSE', value='PRESS', ctrl=True)

        # Draw shape
        # kmi = km.keymap_items.new(idname='bc.shape_draw', type='LEFTMOUSE', value='PRESS', ctrl=True, alt=True)

        # Draw shape
        kmi = km.keymap_items.new(idname='bc.shape_draw', type='LEFTMOUSE', value='PRESS', ctrl=True, shift=True)

        # Draw shape
        # kmi = km.keymap_items.new(idname='bc.shape_draw', type='LEFTMOUSE', value='PRESS', ctrl=True, alt=True, shift=True)

        # Draw shape
        kmi = km.keymap_items.new(idname='bc.shape_draw', type='LEFTMOUSE', value='PRESS')
        kmi.active = False

        # Display snap
        kmi = km.keymap_items.new(idname='bc.shape_snap', type='LEFT_CTRL', value='PRESS')
        kmi = km.keymap_items.new(idname='bc.shape_snap', type='RIGHT_CTRL', value='PRESS')

        # Custom shape
        kmi = km.keymap_items.new(idname='BC_OT_custom', type='C', value='PRESS')
        kmi.properties.set = True

        # Cycle shape types
        kmi = km.keymap_items.new(idname='BC_OT_subtype_scroll', type='WHEELUPMOUSE', value='PRESS', alt=True)
        kmi.active = addon.preference().keymap.alt_scroll_shape_type
        kmi.properties.direction = 'UP'

        kmi = km.keymap_items.new(idname='BC_OT_subtype_scroll', type='WHEELDOWNMOUSE',value='PRESS', alt=True)
        kmi.active = addon.preference().keymap.alt_scroll_shape_type
        kmi.properties.direction = 'DOWN'

        kmi = km.keymap_items.new(idname='BC_OT_subtype_scroll', type='UP_ARROW', value='PRESS', alt=True)
        kmi.active = addon.preference().keymap.alt_scroll_shape_type
        kmi.properties.direction = 'UP'

        kmi = km.keymap_items.new(idname='BC_OT_subtype_scroll', type='DOWN_ARROW',value='PRESS', alt=True)
        kmi.active = addon.preference().keymap.alt_scroll_shape_type
        kmi.properties.direction = 'DOWN'

    del active_keyconfig
    del addon_keyconfig


def unregister():
    global keys

    for km, kmi in keys:
        km.keymap_items.remove(kmi)

    keys.clear()

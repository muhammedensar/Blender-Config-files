'''
Copyright (C) 2021 CG Cookie
http://cgcookie.com
hello@cgcookie.com

Created by Jonathan Denning, Jonathan Williamson, and Patrick Moore

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import os
import re
import time
import textwrap
import importlib
from concurrent.futures import ThreadPoolExecutor

import bpy
from bpy.types import Menu, Operator, Panel
from bpy_extras import object_utils
from bpy.app.handlers import persistent

# a hack to check if we're under git version control
# is_git = os.path.exists(os.path.join(os.path.dirname(__file__), '.git'))
bl_info = {
    "name":        "RetopoFlow",
    "description": "A suite of retopology tools for Blender through a unified retopology mode",
    "author":      "Jonathan Denning, Jonathan Lampel, Jonathan Williamson, Patrick Moore, Patrick Crawford, Christopher Gearhart",
    "location":    "View 3D > Header",
    "blender":     (2, 93, 0),
    "version":     (3, 2, 9),
    # "warning":     "Alpha",                   # used for warning icon and text in addons panel
    # "warning":     "Beta",
    # "warning":     "Release Candidate 1",
    # "warning":     "Release Candidate 2",
    "doc_url":     "https://docs.retopoflow.com",
    "tracker_url": "https://github.com/CGCookie/retopoflow/issues",
    "category":    "3D View",
}

import_succeeded = False

if bpy.app.background:
    print(f'RetopoFlow: Blender is running in background; skipping any RF initializations')
else:
    try:
        if "retopoflow" in locals():
            print('RetopoFlow: RELOADING!')
            # reloading RF modules
            importlib.reload(retopoflow)
            importlib.reload(helpsystem)
            importlib.reload(updatersystem)
            importlib.reload(keymapsystem)
            importlib.reload(configoptions)
            importlib.reload(updater)
            importlib.reload(rftool)
        else:
            print('RetopoFlow: Initial load')
            from .retopoflow import retopoflow
            from .retopoflow import helpsystem
            from .retopoflow import updatersystem
            from .retopoflow import keymapsystem
            from .config import options as configoptions
            from .retopoflow import updater
            from .addon_common.common.maths import convert_numstr_num, has_inverse
            from .addon_common.common.blender import get_active_object, BlenderIcon
            from .retopoflow import rftool
        options = configoptions.options
        retopoflow_version = configoptions.retopoflow_version
        import_succeeded = True
        RFTool = rftool.RFTool
    except ModuleNotFoundError as e:
        print('RetopoFlow: ModuleNotFoundError caught when trying to enable add-on!')
        print(e)
    except Exception as e:
        print('RetopoFlow: Unexpected Exception caught when trying to enable add-on!')
        print(e)
        from .addon_common.common.debug import Debugger
        message,h = Debugger.get_exception_info_and_hash()
        message = '\n'.join('- %s'%l for l in message.splitlines())
        print(message)


# the classes to register/unregister
RF_classes = []


# point BlenderIcon to correct icon path
if import_succeeded:
    BlenderIcon.path_icons = os.path.join(os.path.dirname(__file__), 'icons')


if import_succeeded:
    '''
    create operators for viewing RetopoFlow help documents
    '''

    def VIEW3D_OT_RetopoFlow_Help_Factory(label, filename):
        idname = label.replace(' ', '')
        class VIEW3D_OT_RetopoFlow_Help(helpsystem.RetopoFlow_OpenHelpSystem):
            """Open RetopoFlow Help System"""
            bl_idname = f'cgcookie.retopoflow_help_{idname.lower()}'
            bl_label = f'RF Help: {label}'
            bl_description = f'Open RetopoFlow Help System: {label}'
            bl_space_type = "VIEW_3D"
            bl_region_type = "TOOLS"
            bl_options = set()
            rf_startdoc = f'{filename}.md'
        VIEW3D_OT_RetopoFlow_Help.__name__ = f'VIEW3D_OT_RetopoFlow_Help_{idname}'
        return VIEW3D_OT_RetopoFlow_Help

    def VIEW3D_OT_RetopoFlow_Online_Factory(label, filename):
        idname = label.replace(' ', '')
        class VIEW3D_OT_RetopoFlow_Online(Operator):
            """Open RetopoFlow Help Online"""
            bl_idname = f'cgcookie.retopoflow_online_{idname.lower()}'
            bl_label = f'RF Online: {label}'
            bl_description = f'Open RetopoFlow Help Online: {label}'
            bl_space_type = "VIEW_3D"
            bl_region_type = "TOOLS"
            bl_options = set()
            def invoke(self, context, event):
                bpy.ops.wm.url_open(url=f'https://docs.retopoflow.com/{filename}.html')
                return {'FINISHED'}
        VIEW3D_OT_RetopoFlow_Online.__name__ = f'VIEW3D_OT_RetopoFlow_Online_{idname}'
        return VIEW3D_OT_RetopoFlow_Online

    RF_help_classes = [
        cls
        for args in [
            ('Quick Start Guide', 'quick_start'),
            ('Welcome Message',   'welcome'),
            ('Table of Contents', 'table_of_contents'),
            ('FAQ',               'faq'),
            ('Keymap Editor',     'keymap_editor'),
            ('Updater System',    'addon_updater'),
        ]
        for cls in [
            VIEW3D_OT_RetopoFlow_Help_Factory(*args),
            VIEW3D_OT_RetopoFlow_Online_Factory(*args),
        ]
    ]
    RF_classes += RF_help_classes


    class VIEW3D_OT_RetopoFlow_Help_Warnings(helpsystem.RetopoFlow_OpenHelpSystem):
        """Open RetopoFlow Warnings Document"""
        bl_idname = "cgcookie.retopoflow_help_warnings"
        bl_label = "See details on these warnings"
        bl_description = "See details on the RetopoFlow warnings"
        bl_space_type = "VIEW_3D"
        bl_region_type = "TOOLS"
        bl_options = set()
        rf_startdoc = 'warnings.md'
    RF_classes += [VIEW3D_OT_RetopoFlow_Help_Warnings]

    class VIEW3D_OT_RetopoFlow_UpdaterSystem(updatersystem.RetopoFlow_OpenUpdaterSystem):
        """Open RetopoFlow Updater System"""
        bl_idname = "cgcookie.retopoflow_updater"
        bl_label = "Updater"
        bl_description = "Open RetopoFlow Updater"
        bl_space_type = "VIEW_3D"
        bl_region_type = "TOOLS"
        bl_options = set()
    RF_classes += [VIEW3D_OT_RetopoFlow_UpdaterSystem]

    class VIEW3D_OT_RetopoFlow_KeymapEditor(keymapsystem.RetopoFlow_OpenKeymapSystem):
        """Open RetopoFlow Keymap Editor"""
        bl_idname = "cgcookie.retopoflow_keymapeditor"
        bl_label = "Keymap Editor"
        bl_description = "Open RetopoFlow Keymap Editor"
        bl_space_type = "VIEW_3D"
        bl_region_type = "TOOLS"
        bl_options = set()
    RF_classes += [VIEW3D_OT_RetopoFlow_KeymapEditor]

    if options['preload help images']: retopoflow.preload_help_images()



class VIEW3D_OT_RetopoFlow_BlenderMarket(Operator):
    bl_idname = 'cgcookie.retopoflow_blendermarket'
    bl_label = 'Visit Blender Market'
    bl_description = 'Open the Blender Market RetopoFlow page'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_options = set()

    def invoke(self, context, event):
        bpy.ops.wm.url_open(url='https://blendermarket.com/products/retopoflow')
        return {'FINISHED'}
RF_classes += [VIEW3D_OT_RetopoFlow_BlenderMarket]

class VIEW3D_OT_RetopoFlow_Online_Main(Operator):
    bl_idname = 'cgcookie.retopoflow_online_main'
    bl_label = 'Online Documentation'
    bl_description = 'Open RetopoFlow Online Documentation'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_options = set()

    def invoke(self, context, event):
        bpy.ops.wm.url_open(url='https://docs.retopoflow.com')
        return {'FINISHED'}
RF_classes += [VIEW3D_OT_RetopoFlow_Online_Main]



if import_succeeded:
    '''
    create operators to start RetopoFlow
    '''

    class VIEW3D_OT_RetopoFlow_NewTarget_Cursor(Operator):
        """Create new target object+mesh at the 3D Cursor and start RetopoFlow"""
        bl_idname = "cgcookie.retopoflow_newtarget_cursor"
        bl_label = "RF: New target at Cursor"
        bl_description = "A suite of retopology tools for Blender through a unified retopology mode.\nCreate new target mesh based on the cursor and start RetopoFlow"
        bl_space_type = "VIEW_3D"
        bl_region_type = "TOOLS"
        bl_options = {'REGISTER', 'UNDO', 'BLOCKING'}

        @classmethod
        def poll(cls, context):
            if not context.region or context.region.type != 'WINDOW': return False
            if not context.space_data or context.space_data.type != 'VIEW_3D': return False
            # check we are not in mesh editmode
            if context.mode == 'EDIT_MESH': return False
            # make sure we have source meshes
            if not retopoflow.RetopoFlow.get_sources(): return False
            # all seems good!
            return True

        def invoke(self, context, event):
            retopoflow.RetopoFlow.create_new_target(context)
            return bpy.ops.cgcookie.retopoflow('INVOKE_DEFAULT')
    RF_classes += [VIEW3D_OT_RetopoFlow_NewTarget_Cursor]

    class VIEW3D_OT_RetopoFlow_NewTarget_Active(Operator):
        """Create new target object+mesh at the active source and start RetopoFlow"""
        bl_idname = "cgcookie.retopoflow_newtarget_active"
        bl_label = "RF: New target at Active"
        bl_description = "A suite of retopology tools for Blender through a unified retopology mode.\nCreate new target mesh based on the active source and start RetopoFlow"
        bl_space_type = "VIEW_3D"
        bl_region_type = "TOOLS"
        bl_options = {'REGISTER', 'UNDO', 'BLOCKING'}

        @classmethod
        def poll(cls, context):
            if not context.region or context.region.type != 'WINDOW': return False
            if not context.space_data or context.space_data.type != 'VIEW_3D': return False
            # check we are not in mesh editmode
            if context.mode == 'EDIT_MESH': return False
            # make sure we have source meshes
            if not retopoflow.RetopoFlow.get_sources(): return False
            o = get_active_object()
            if not o: return False
            if not retopoflow.RetopoFlow.is_valid_source(o, test_poly_count=False): return False
            # all seems good!
            return True

        def invoke(self, context, event):
            retopoflow.RetopoFlow.create_new_target(context)
            return bpy.ops.cgcookie.retopoflow('INVOKE_DEFAULT')
    RF_classes += [VIEW3D_OT_RetopoFlow_NewTarget_Active]

    class VIEW3D_OT_RetopoFlow_LastTool(retopoflow.RetopoFlow):
        """Start RetopoFlow"""
        bl_idname = "cgcookie.retopoflow"
        bl_label = "Start RetopoFlow"
        bl_description = "A suite of retopology tools for Blender through a unified retopology mode.\nStart with last used tool"
        bl_space_type = "VIEW_3D"
        bl_region_type = "TOOLS"
        bl_options = {'REGISTER', 'UNDO', 'BLOCKING'}
    RF_classes += [VIEW3D_OT_RetopoFlow_LastTool]

    def VIEW3D_OT_RetopoFlow_Tool_Factory(rftool):
        name = rftool.name
        description = rftool.description
        class VIEW3D_OT_RetopoFlow_Tool(retopoflow.RetopoFlow):
            """Start RetopoFlow with a specific tool"""
            bl_idname = f'cgcookie.retopoflow_{name.lower()}'
            bl_label = f'RF: {name}'
            bl_description = f'A suite of retopology tools for Blender through a unified retopology mode.\nStart with {name}: {description}'
            bl_space_type = "VIEW_3D"
            bl_region_type = "TOOLS"
            bl_options = {'REGISTER', 'UNDO', 'BLOCKING'}
            rf_starting_tool = name
            icon_id = rftool.icon_id
        # just in case: remove spaces, so that class name is proper
        VIEW3D_OT_RetopoFlow_Tool.__name__ = f'VIEW3D_OT_RetopoFlow_{name.replace(" ", "")}'
        return VIEW3D_OT_RetopoFlow_Tool
    RF_tool_classes = [
        VIEW3D_OT_RetopoFlow_Tool_Factory(rftool)
        for rftool in RFTool.registry
    ]
    RF_classes += RF_tool_classes


if import_succeeded:
    '''
    create operator for recovering auto save
    '''

    class VIEW3D_OT_RetopoFlow_RecoverOpen(Operator):
        bl_idname = 'cgcookie.retopoflow_recover_open'
        bl_label = 'Recover: Open Last Auto Save'
        bl_description = 'Recover by opening last file automatically saved by RetopoFlow'
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'TOOLS'
        bl_options = set()
        rf_icon = 'rf_recover_icon'

        @classmethod
        def poll(cls, context):
            return retopoflow.RetopoFlow.has_auto_save()

        def invoke(self, context, event):
            retopoflow.RetopoFlow.recover_auto_save()
            return {'FINISHED'}
    RF_classes += [VIEW3D_OT_RetopoFlow_RecoverOpen]

    class VIEW3D_OT_RetopoFlow_RecoverRevert(Operator):
        bl_idname = 'cgcookie.retopoflow_recover_finish'
        bl_label = 'Recover: Finish Auto Save Recovery'
        bl_description = 'Finish recovering open file'
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'TOOLS'
        bl_options = set()
        rf_icon = 'rf_recover_icon'

        @classmethod
        def poll(cls, context):
            return retopoflow.RetopoFlow.can_recover()

        def invoke(self, context, event):
            retopoflow.RetopoFlow.recovery_revert()
            return {'FINISHED'}
    RF_classes += [VIEW3D_OT_RetopoFlow_RecoverRevert]


if import_succeeded:
    '''
    create panel for showing tools in Blender
    '''

    # some common checker fns
    def has_sources(context):
        return retopoflow.RetopoFlow.has_valid_source()
    def is_editing_target(context):
        obj = context.active_object
        mode_string = context.mode
        edit_object = context.edit_object
        gp_edit = obj and obj.mode in {'EDIT_GPENCIL', 'PAINT_GPENCIL', 'SCULPT_GPENCIL', 'WEIGHT_GPENCIL'}
        return not gp_edit and edit_object and mode_string == 'EDIT_MESH'
    def are_sources_too_big(context):
        # take a look at https://github.com/CoDEmanX/blend_stats/blob/master/blend_stats.py#L98
        total = 0
        for src in retopoflow.RetopoFlow.get_sources():
            total += len(src.data.polygons)
        m = convert_numstr_num(options['warning max sources'])
        return total > m
    def is_target_too_big(context):
        # take a look at https://github.com/CoDEmanX/blend_stats/blob/master/blend_stats.py#L98
        tar = retopoflow.RetopoFlow.get_target()
        if not tar: return False
        m = convert_numstr_num(options['warning max target'])
        return len(tar.data.polygons) > m
    def multiple_3dviews(context):
        views = [area for area in context.window.screen.areas if area.type == 'VIEW_3D']
        return len(views) > 1
    def in_quadview(context):
        for area in context.window.screen.areas:
            if area.type != 'VIEW_3D': continue
            for space in area.spaces:
                if space.type != 'VIEW_3D': continue
                if len(space.region_quadviews) > 0: return True
        return False
    def is_addon_folder_valid(context):
        bad_chars = set(re.sub(r'[a-zA-Z0-9_]', '', __package__))
        if not bad_chars: return True
        # print(f'Bad characters found in add-on: {bad_chars}')
        return False


    rf_label_extra = " (?)"
    if       configoptions.retopoflow_version_git:    rf_label_extra = " (git)"
    elif not configoptions.retopoflow_cgcookie_built: rf_label_extra = " (self)"
    elif     configoptions.retopoflow_github:         rf_label_extra = " (github)"
    elif     configoptions.retopoflow_blendermarket:  rf_label_extra = ""

    class VIEW3D_PT_RetopoFlow(Panel):
        """RetopoFlow Blender Menu"""
        bl_label = 'RetopoFlow'
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'HEADER'
        # bl_ui_units_x = 100

        @staticmethod
        def draw_popover(self, context):
            if context.mode == 'EDIT_MESH' or context.mode == 'OBJECT':
                self.layout.separator()
                if is_editing_target(context):
                    self.layout.operator('cgcookie.retopoflow', text="", icon='MOD_DATA_TRANSFER')
                self.layout.popover('VIEW3D_PT_RetopoFlow')

        def draw(self, context):
            layout = self.layout
            layout.label(text=f'RetopoFlow {retopoflow_version}{rf_label_extra}')

    class VIEW3D_PT_RetopoFlow_Warnings(Panel):
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'HEADER'
        bl_parent_id = 'VIEW3D_PT_RetopoFlow'
        bl_label = 'WARNINGS!'

        @classmethod
        def get_warnings(cls, context):
            warnings = set()

            # source setup checks
            if not retopoflow.RetopoFlow.get_sources():
                warnings.add('setup: no sources')
            elif not all(has_inverse(source.matrix_local) for source in retopoflow.RetopoFlow.get_sources()):
                warnings.add('setup: source has non-invertible matrix')

            # target setup checks
            if is_editing_target(context) and not retopoflow.RetopoFlow.get_target():
                warnings.add('setup: no target')
            elif retopoflow.RetopoFlow.get_target() and not has_inverse(retopoflow.RetopoFlow.get_target().matrix_local):
                warnings.add('setup: target has non-invertible matrix')

            # performance checks
            if is_target_too_big(context):
                warnings.add('performance: target too big')
            if are_sources_too_big(context):
                warnings.add('performance: source too big')

            # layout checks
            if multiple_3dviews(context):
                warnings.add('layout: multiple 3d views')
            if in_quadview(context):
                warnings.add('layout: in quad view')
            if any(space.lock_cursor for space in context.area.spaces if space.type == 'VIEW_3D'):
                warnings.add('layout: view is locked to cursor')
            if any(space.lock_object for space in context.area.spaces if space.type == 'VIEW_3D'):
                warnings.add('layout: view is locked to object')

            # auto save / unsaved checks
            if not retopoflow.RetopoFlow.get_auto_save_settings(context)['auto save']:
                warnings.add('save: auto save is disabled')
            if not retopoflow.RetopoFlow.get_auto_save_settings(context)['saved']:
                warnings.add('save: unsaved blender file')
            if retopoflow.RetopoFlow.can_recover():
                # user directly opened an auto save file
                warnings.add('save: can recover auto save')

            # install checks
            if not is_addon_folder_valid(context):
                warnings.add('install: invalid add-on folder')

            return warnings

        @classmethod
        def poll(cls, context):
            return bool(cls.get_warnings(context))

        def draw(self, context):
            layout = self.layout

            warningbox = None
            warningsubboxes = {}
            def add_warning():
                nonlocal warningbox, layout
                if not warningbox:
                    warningbox = layout.box()
                    warningbox.label(text='Warnings', icon='ERROR')
                return warningbox.box()
            def get_warning_subbox(label):
                nonlocal warningsubboxes
                if label not in warningsubboxes:
                    box = layout.box().column(align=True) # add_warning().column()
                    box.label(text=label, icon='ERROR')
                    warningsubboxes[label] = box
                return warningsubboxes[label]

            warnings = self.get_warnings(context)

            # SETUP CHECKS
            if 'setup: no sources' in warnings:
                box = get_warning_subbox('Setup Issue')
                box.label(text=f'No sources detected', icon='DOT')
            if 'setup: source has non-invertible matrix' in warnings:
                box = get_warning_subbox('Setup Issue')
                box.label(text=f'A source has non-invertible matrix', icon='DOT')
            if 'setup: no target' in warnings:
                box = get_warning_subbox('Setup Issue')
                box.label(text=f'No target detected', icon='DOT')
            if 'setup: target has non-invertible matrix' in warnings:
                box = get_warning_subbox('Setup Issue')
                box.label(text=f'Target has non-invertible matrix', icon='DOT')

            # PERFORMANCE CHECKS
            if 'performance: target too big' in warnings:
                box = get_warning_subbox('Performance Issue')
                box.label(text=f'Target is too large (>{options["warning max target"]})', icon='DOT')
            if 'performance: source too big' in warnings:
                box = get_warning_subbox('Performance Issue')
                box.label(text=f'Sources are too large (>{options["warning max sources"]})', icon='DOT')

            # LAYOUT
            if 'layout: multiple 3d views' in warnings:
                box = get_warning_subbox('Layout Issue')
                box.label(text='Multiple 3D Views', icon='DOT')
            if 'layout: in quad view' in warnings:
                box = get_warning_subbox('Layout Issue')
                box.label(text='Quad View will be disabled', icon='DOT')
            if 'layout: view is locked to cursor' in warnings:
                box = get_warning_subbox('Layout Issue')
                box.label(text='View is locked to cursor', icon='DOT')
            if 'layout: view is locked to object' in warnings:
                box = get_warning_subbox('Layout Issue')
                box.label(text='View is locked to object', icon='DOT')

            # AUTO SAVE / UNSAVED
            if 'save: auto save is disabled' in warnings:
                box = get_warning_subbox('Auto Save / Save')
                box.label(text='Auto Save is disabled', icon='DOT')
            if 'save: unsaved blender file' in warnings:
                box = get_warning_subbox('Auto Save / Save')
                box.label(text='Unsaved Blender file', icon='DOT')
            if 'save: can recover auto save' in warnings:
                box = get_warning_subbox('Auto Save / Save')
                box.label(text=f'Auto Save file opened', icon='DOT')
                box.operator(
                    'cgcookie.retopoflow_recover_finish',
                    text='Finish Auto Save Recovery',
                    icon='RECOVER_LAST',
                )

            # INSTALL
            if 'install: invalid add-on folder' in warnings:
                box = get_warning_subbox('Installation')
                box.label(text=f'Invalid add-on folder name', icon='DOT')

            # show button for more warning details
            layout.operator('cgcookie.retopoflow_help_warnings', icon='HELP')


    class VIEW3D_PT_RetopoFlow_EditMesh(Panel):
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'HEADER'
        bl_parent_id = 'VIEW3D_PT_RetopoFlow'
        bl_label = 'Continue Editing Target'

        @classmethod
        def poll(cls, context):
            return is_editing_target(context)

        def draw(self, context):
            layout = self.layout

            if False:
                # currently editing target, so show RF tools
                for c in RF_tool_classes:
                    layout.operator(c.bl_idname, text=c.rf_starting_tool, icon_value=c.icon_id)
            else:
                col = layout.column(align=True)
                col.operator('cgcookie.retopoflow')

                buttons = col.grid_flow(
                    columns=len(RF_tool_classes),
                    even_columns=True,
                    align=True,
                )
                for c in RF_tool_classes:
                    buttons.operator(c.bl_idname, text='', icon_value=c.icon_id)

    class VIEW3D_PT_RetopoFlow_CreateNew(Panel):
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'HEADER'
        bl_parent_id = 'VIEW3D_PT_RetopoFlow'
        bl_label = 'Create New Target'

        @classmethod
        def poll(cls, context):
            return not is_editing_target(context)

        def draw(self, context):
            layout = self.layout
            row = layout.row()
            row.operator('cgcookie.retopoflow_newtarget_cursor', text='at Cursor', icon='ADD') #'ORIENTATION_CURSOR')
            row.operator('cgcookie.retopoflow_newtarget_active', text='at Active', icon='ADD') #'OBJECT_ORIGIN')

    class VIEW3D_PT_RetopoFlow_HelpAndSupport(Panel):
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'HEADER'
        bl_parent_id = 'VIEW3D_PT_RetopoFlow'
        bl_label = 'Help and Support'

        def draw(self, context):
            layout = self.layout

            col = layout.column(align=True)

            row = col.row(align=True)
            row.label(text='Quick Start Guide')
            row.operator('cgcookie.retopoflow_help_quickstartguide', text='', icon='HELP')
            row.operator('cgcookie.retopoflow_online_quickstartguide', text='', icon='URL')

            row = col.row(align=True)
            row.label(text='Welcome Message')
            row.operator('cgcookie.retopoflow_help_welcomemessage', text='', icon='HELP')
            row.operator('cgcookie.retopoflow_online_welcomemessage', text='', icon='URL')

            row = col.row(align=True)
            row.label(text='Table of Contents')
            row.operator('cgcookie.retopoflow_help_tableofcontents', text='', icon='HELP')
            row.operator('cgcookie.retopoflow_online_tableofcontents', text='', icon='URL')

            row = col.row(align=True)
            row.label(text='FAQ')
            row.operator('cgcookie.retopoflow_help_faq', text='', icon='HELP')
            row.operator('cgcookie.retopoflow_online_faq', text='', icon='URL')

            # col.separator()
            # col.operator('cgcookie.retopoflow_online_main', icon='HELP')

            col.separator()
            col.operator('cgcookie.retopoflow_blendermarket', icon_value=BlenderIcon.icon_id('blendermarket.png')) # icon='URL'

    class VIEW3D_PT_RetopoFlow_Config(Panel):
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'HEADER'
        bl_parent_id = 'VIEW3D_PT_RetopoFlow'
        bl_label = 'Configuration'

        def draw(self, context):
            layout = self.layout

            row = layout.row(align=True)
            row.operator('cgcookie.retopoflow_keymapeditor', icon='PREFERENCES')
            row.operator('cgcookie.retopoflow_help_keymapeditor', text='', icon='HELP')
            row.operator('cgcookie.retopoflow_online_keymapeditor', text='', icon='URL')


    class VIEW3D_PT_RetopoFlow_AutoSave(Panel):
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'HEADER'
        bl_parent_id = 'VIEW3D_PT_RetopoFlow'
        bl_label = 'Auto Save'

        def draw(self, context):
            layout = self.layout
            layout.operator(
                'cgcookie.retopoflow_recover_open',
                text='Open Last Auto Save',
                icon='RECOVER_LAST',
            )
            # if retopoflow.RetopoFlow.has_backup():
            #     box.label(text=options['last auto save path'])


    class VIEW3D_PT_RetopoFlow_Updater(Panel):
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'HEADER'
        bl_parent_id = 'VIEW3D_PT_RetopoFlow'
        bl_label = 'Updater'

        def draw(self, context):
            layout = self.layout
            if configoptions.retopoflow_version_git:
                box = layout.box().column(align=True)
                box.label(text='RetopoFlow under Git control') #, icon='DOT')
                box.label(text='Use Git to Pull latest updates') #, icon='DOT')
                # col.operator('cgcookie.retopoflow_updater', text='Updater System', icon='SETTINGS')
            else:
                col = layout.column(align=True)
                col.operator('cgcookie.retopoflow_updater_check_now', text='Check for updates', icon='FILE_REFRESH')
                col.operator('cgcookie.retopoflow_updater_update_now', text='Update now', icon="IMPORT")

                col.separator()
                row = col.row(align=True)
                row.operator('cgcookie.retopoflow_updater', text='Updater System', icon='SETTINGS')
                row.operator('cgcookie.retopoflow_help_updatersystem', text='', icon='HELP')
                row.operator('cgcookie.retopoflow_online_updatersystem', text='', icon='URL')

    RF_classes += [
        VIEW3D_PT_RetopoFlow,
        VIEW3D_PT_RetopoFlow_Warnings,
        VIEW3D_PT_RetopoFlow_CreateNew,
        VIEW3D_PT_RetopoFlow_EditMesh,
        VIEW3D_PT_RetopoFlow_HelpAndSupport,
        VIEW3D_PT_RetopoFlow_Config,
        VIEW3D_PT_RetopoFlow_AutoSave,
        VIEW3D_PT_RetopoFlow_Updater,
    ]


if not import_succeeded:
    '''
    importing failed.  show this to the user!
    '''

    class VIEW3D_PT_RetopoFlow(Panel):
        """RetopoFlow Blender Menu"""
        bl_label = "RetopoFlow (broken)"
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'HEADER'

        @staticmethod
        def draw_popover(self, context):
            self.layout.popover('VIEW3D_PT_RetopoFlow')

        def draw(self, context):
            layout = self.layout

            box = layout.box()
            box.label(text='RetopoFlow cannot start.', icon='ERROR')

            box = layout.box()
            tw = textwrap.TextWrapper(width=35)
            report_lines = [
                'This is likely due to an incorrect installation of the add-on.',
                'Please try restarting Blender.'
                'If that does not work, please download the latest version from the Blender Market.',
                'If you continue to see this error, contact us through the Blender Market Indox, and we will work to get it fixed!',
            ]
            for report_line in report_lines:
                col = box.column()
                for l in tw.wrap(text=report_line):
                    col.label(text=l)

            box = layout.box()
            box.operator('cgcookie.retopoflow_blendermarket', icon='URL')

    RF_classes += [VIEW3D_PT_RetopoFlow]



def register():
    for cls in RF_classes: bpy.utils.register_class(cls)
    if import_succeeded: updater.register(bl_info)
    bpy.types.VIEW3D_MT_editor_menus.append(VIEW3D_PT_RetopoFlow.draw_popover)

def unregister():
    if import_succeeded: retopoflow.preload_help_images.quit = True
    bpy.types.VIEW3D_MT_editor_menus.remove(VIEW3D_PT_RetopoFlow.draw_popover)
    if import_succeeded: updater.unregister()
    for cls in reversed(RF_classes): bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()

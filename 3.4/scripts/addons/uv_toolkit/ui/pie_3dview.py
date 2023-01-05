from bpy.types import Menu

from ..utils.ui_utils import get_operator_name, get_icons_set


class Pie3dView(Menu):
    bl_idname = "UVTOOLKIT_MT_pie_3dview"
    bl_label = "3D View Pie"

    def pie_item(self, context, pie_property, custom_op, custom_op_name):
        icons_coll = get_icons_set(context, pie_menu=True)
        layout = self.layout
        pie = layout.menu_pie()
        if pie_property == "UV_MENU":
            self.uv_menu(context, pie)
        elif pie_property == "MARK_SEAM":
            pie.operator("mesh.mark_seam", text="Mark Seam",
                         icon_value=icons_coll["mark_seam"].icon_id).clear = False
        elif pie_property == "CLEAR_SEAM":
            pie.operator("mesh.mark_seam", text="Clear Seam",
                         icon_value=icons_coll["clear_seam"].icon_id).clear = True
        elif pie_property == "CUSTOM_OP":
            if custom_op_name:
                op_name = custom_op_name
            else:
                op_name = get_operator_name(context, custom_op)
            pie.operator("uv.toolkit_execute_custom_op", text=op_name).exec_op = custom_op
        elif pie_property == "DISABLE":
            pie.separator()
        else:
            if pie_property == "uv.unwrap":
                icon_name = "unwrap"
            else:
                icon_name = pie_property[11:]
            pie.operator(pie_property, icon_value=icons_coll[icon_name].icon_id)

    def uv_menu(self, context, pie):
        tool_settings = context.tool_settings
        split = pie.split()
        box = split.box().column()
        box.operator("uv.unwrap")
        box.prop(tool_settings, "use_edge_path_live_unwrap")
        box.operator("uv.smart_project")
        box.operator("uv.project_from_view")
        box.operator("uv.lightmap_pack")
        box.operator("uv.follow_active_quads")
        box.operator("uv.cube_project")
        box.operator("uv.cylinder_project")
        box.operator("uv.sphere_project")
        box.operator("uv.project_from_view")
        box.operator("uv.project_from_view", text="Project from View (Bounds)")
        box.operator("uv.reset")

    def draw(self, context):
        prefs = context.preferences
        addon_prefs = prefs.addons["uv_toolkit"].preferences
        self.pie_item(context,
                      addon_prefs.pie_3dview_left,
                      addon_prefs.pie_3dview_custom_op_left,
                      addon_prefs.pie_3dview_custom_op_name_left)  # 4
        self.pie_item(context,
                      addon_prefs.pie_3dview_right,
                      addon_prefs.pie_3dview_custom_op_right,
                      addon_prefs.pie_3dview_custom_op_name_right)  # 6
        self.pie_item(context,
                      addon_prefs.pie_3dview_bottom,
                      addon_prefs.pie_3dview_custom_op_bottom,
                      addon_prefs.pie_3dview_custom_op_name_bottom)  # 2
        self.pie_item(context,
                      addon_prefs.pie_3dview_top,
                      addon_prefs.pie_3dview_custom_op_top,
                      addon_prefs.pie_3dview_custom_op_name_top)  # 8
        self.pie_item(context,
                      addon_prefs.pie_3dview_top_left,
                      addon_prefs.pie_3dview_custom_op_top_left,
                      addon_prefs.pie_3dview_custom_op_name_top_left)  # 7
        self.pie_item(context,
                      addon_prefs.pie_3dview_top_right,
                      addon_prefs.pie_3dview_custom_op_top_right,
                      addon_prefs.pie_3dview_custom_op_name_top_right)  # 9
        self.pie_item(context,
                      addon_prefs.pie_3dview_bottom_left,
                      addon_prefs.pie_3dview_custom_op_bottom_left,
                      addon_prefs.pie_3dview_custom_op_name_bottom_left)  # 1
        self.pie_item(context,
                      addon_prefs.pie_3dview_bottom_right,
                      addon_prefs.pie_3dview_custom_op_bottom_right,
                      addon_prefs.pie_3dview_custom_op_name_bottom_right)  # 3

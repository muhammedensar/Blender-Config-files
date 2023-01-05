import bpy
from bpy.app.handlers import persistent

from .. addon import shader


vertice = [3, 6, 8, 32, 64]
array = [2, 4, 6, 8, 10]
width = [0.02, 0.05, 0.1]
segment = [1, 2, 3, 4, 6]
angle = [5, 15, 30, 45, 90]
line_angle = [1, 5, 10, 15]


@persistent
def cleanup_operators(_):
    context = bpy.context
    bc = context.scene.bc

    # if bc.operator:
    #     bc.operator.cancel(context)

    if bc.snap.operator:
        bc.snap.operator.exit(context)

    bc.snap.hit = False

    for handler in shader.handlers:
        handler.remove(force=True)

    shader.handlers = []

    if bpy.context.screen:
        for area in bpy.context.screen.areas:
            area.tag_redraw()


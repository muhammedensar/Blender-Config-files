from .. import lattice, mesh


def shape(ot, context, event, extrude_only=False):
    if ot.shape_type == 'NGON':
        mesh.extrude(ot, context, event, extrude_only=extrude_only)

    lattice.extrude(ot, context, event)

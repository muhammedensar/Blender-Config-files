from gpu.types import GPUBatch, GPUIndexBuf, GPUVertBuf


handlers = []


def load(shader):
    import os
    from ... utility.addon import path

    file = open(os.path.join(path(), 'addon', 'shader', shader), 'r')
    data = file.read()
    file.close()

    return data


def batch(shader, type, attributes={}, indices=[], vbo_length=0, vbo_length_prop_index=0):
    values = list(attributes.values())
    vbo_length = len(values[vbo_length_prop_index]) if not vbo_length and len(values) else vbo_length

    vbo = GPUVertBuf(shader.format_calc(), vbo_length)

    for prop, data in attributes.items():
        if len(data) != vbo_length:
            space = " " * 70
            raise ValueError(F'Batch shader failed; buffer/attribute length mismatch\n{space}Needed: {vbo_length}\n{space}Found: {len(data)}')

        vbo.attr_fill(prop, data)

    if len(indices):
        ibo = GPUIndexBuf(type=type, seq=indices)
        return GPUBatch(type=type, buf=vbo, elem=ibo)

    return GPUBatch(type=type, buf=vbo)



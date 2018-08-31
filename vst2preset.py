# fxp/fxb file format. (VST/Cubase's preset or "bank" files from before VST3
# era)
# based on VST SDK's vst2.x/vstfxstore.h
# names as in the source

import construct
from construct import Array, Float32b, Bytes, Const, Container, Enum, \
    LazyBound, Struct, Switch, Int32ub, Int32ul

def getString():
    try:
        # construct 2.8.11
        stringCtor = getattr(construct, 'String')
        return stringCtor(28, padchar='\0')
    except:
        # construct2.9.45
        stringCtor = getattr(construct, 'PaddedString')
        return stringCtor(28, 'ascii')

vst2preset = Struct(
    "chunkMagic" / Const(b"CcnK"),
    "byteSize" / Int32ub,
    "fxMagic" / Enum(Bytes(4),
       FXP_PARAMS = b'FxCk', FXP_OPAQUE_CHUNK = b'FPCh',
       FXB_REGULAR = b'FxBk', FXB_OPAQUE_CHUNK = b'FBCh',
    ),
    "version" / Int32ub,
    "fxID" / Int32ub,
    "fxVersion" / Int32ub,
    "count" / Int32ub,
    "data" / Switch(lambda ctx: ctx.fxMagic, {
        'FXP_PARAMS': "data" / Struct(
            "prgName" / getString(),
            Array(lambda ctx: ctx['_']['count'], "params" / Float32b),
            ),
        'FXP_OPAQUE_CHUNK': "data" / Struct(
            "prgName" / getString(),
            "size" / Int32ub,
            "chunk" / Bytes(lambda ctx: ctx['size']),
            ),
        'FXB_REGULAR': "data" / Struct(
            "future" / Bytes(128), # zeros
            # Array of FXP_PARAMS vst2preset
            Array(lambda ctx: ctx['_']['count'], "presets" / LazyBound(lambda: vst2preset)),
            ),
        'FXB_OPAQUE_CHUNK': "data" / Struct(
            "future" / Bytes(128), # zeros
            "size" / Int32ub,
            # Unknown format of internal chunk
            "chunk" / Bytes(lambda ctx: ctx['size']),
            ),
    }),
    )

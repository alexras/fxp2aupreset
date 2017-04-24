# fxp/fxb file format. (VST/Cubase's preset or "bank" files from before VST3
# era)
# based on VST SDK's vst2.x/vstfxstore.h
# names as in the source

from construct import Array, Float32b, Bytes, Const, Container, Enum, \
    LazyBound, String, Struct, Switch, Int32ub, Int32ul

vst2preset = Struct(
    'chunkMagic' / Const(b"CcnK"),
    "byteSize" / Int32ub,
    "fxMagic" / Enum(Bytes(4),
       FXP_PARAMS = b'FxCk', FXP_OPAQUE_CHUNK = b'FPCh',
       FXB_REGULAR = b'FxBk', FXB_OPAQUE_CHUNK = b'FBCh',
    ),
    "version" / Int32ub,
    "fxID" / Int32ub,
    "fxVersion" / Int32ub,
    "count" / Int32ub,
    # Switch('data', lambda ctx: ctx['fxMagic'], {
    #     'FXP_PARAMS': Struct('data',
    #         String('prgName', 28, padchar = '\0'),
    #         Array(lambda ctx: ctx['_']['count'], Float32b('params')),
    #         ),
    #     'FXP_OPAQUE_CHUNK': Struct('data',
    #         String('prgName', 28, padchar = '\0'),
    #         Int32ub('size'),
    #         Bytes('chunk', lambda ctx: ctx['size']),
    #         ),
    #     'FXB_REGULAR': Struct('data',
    #         Bytes('future', 128), # zeros
    #         # Array of FXP_PARAMS vst2preset
    #         Array(lambda ctx: ctx['_']['count'], LazyBound('presets', lambda: vst2preset)),
    #         ),
    #     'FXB_OPAQUE_CHUNK': Struct('data',
    #         Bytes('future', 128), # zeros
    #         Int32ub('size'),
    #         # Unknown format of internal chunk
    #         Bytes('chunk', lambda ctx: ctx['size']),
    #         ),
    #     }),
    )

# fxp/fxb file format. (VST/Cubase's preset or "bank" files from before VST3
# era)
# based on VST SDK's vst2.x/vstfxstore.h
# names as in the source

from construct import Array, BFloat32, Bytes, Const, Container, Enum, \
    LazyBound, String, Struct, Switch, UBInt32, ULInt32

vst2preset = Struct('vst2preset',
    Const(Bytes('chunkMagic', 4), 'CcnK'),
    UBInt32('byteSize'),
    Enum(Bytes('fxMagic', 4),
        FXP_PARAMS = 'FxCk', FXP_OPAQUE_CHUNK = 'FPCh',
        FXB_REGULAR = 'FxBk', FXB_OPAQUE_CHUNK = 'FBCh',
        ),
    UBInt32('version'),
    UBInt32('fxID'),
    UBInt32('fxVersion'),
    UBInt32('count'),
    Switch('data', lambda ctx: ctx['fxMagic'], {
        'FXP_PARAMS': Struct('data',
            String('prgName', 28, padchar = '\0'),
            Array(lambda ctx: ctx['_']['count'], BFloat32('params')),
            ),
        'FXP_OPAQUE_CHUNK': Struct('data',
            String('prgName', 28, padchar = '\0'),
            UBInt32('size'),
            Bytes('chunk', lambda ctx: ctx['size']),
            ),
        'FXB_REGULAR': Struct('data',
            Bytes('future', 128), # zeros
            # Array of FXP_PARAMS vst2preset
            Array(lambda ctx: ctx['_']['count'], LazyBound('presets', lambda: vst2preset)),
            ),
        'FXB_OPAQUE_CHUNK': Struct('data',
            Bytes('future', 128), # zeros
            UBInt32('size'),
            # Unknown format of internal chunk
            Bytes('chunk', lambda ctx: ctx['size']),
            ),
        }),
    )

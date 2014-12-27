#!/usr/bin/env python

# vst to au preset convert
# Colin Barry / colin@loomer.co.uk / www.loomer.co.uk
#
# Based on the aupreset to fxp converter found here http://www.rawmaterialsoftware.com/viewtopic.php?f=8&t=8337




from construct import Array, BFloat32, Bytes, Const, Container, Enum, LazyBound, String, Struct, Switch, UBInt32, ULInt32
import os
from os import path, listdir, getcwd, chdir
import sys
from xml.dom import minidom
from glob import glob
from base64 import b64encode

# fxp/fxb file format. (VST/Cubase's preset or "bank" files from before VST3 era)
# based on VST SDK's vst2.x/vstfxstore.h
# names as in the source
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

# converts a four character identifier to an integer
def id_to_integer(id):
    if (len(id) != 4):
        print id, "should be exactly 4 characters length."
        sys.exit(1)

    return str((ord(id[0]) << 24) + (ord(id[1]) << 16) + (ord(id[2]) << 8) + ord(id[3]))

# adds an element to an xml dom tree
def add_key_and_value(doc, keyname, value, value_type, parent_element):
    key_element = doc.createElement("key")
    key_element_text = doc.createTextNode(keyname);
    key_element.appendChild(key_element_text)
    parent_element.appendChild(key_element)

    data_element = doc.createElement(value_type)
    data_element_text = doc.createTextNode(value);
    data_element.appendChild(data_element_text)
    parent_element.appendChild(data_element)


# converts the passed fxp file, creating the equivalent aupreset.
def convert(filename, manufacturer, subtype, type, state_key):
    print "Opening fxp preset file", filename

    # extract fxp structure
    f = open(filename, 'rb')
    fxp = vst2preset.parse(f.read())
    f.close()

    if (fxp['fxMagic'] != 'FXP_OPAQUE_CHUNK'):
        print ".fxp preset is not in opaque chunk format, and so can not be converted."
        return

    preset_name = path.splitext(filename)[0]

    # convert data chunk to base64
    base64data = b64encode(fxp['data']['chunk'])

    # create the aupreset dom
    # set the DOCTYPE
    imp = minidom.DOMImplementation()
    doctype = imp.createDocumentType(
        qualifiedName='plist',
        publicId="-//Apple//DTD PLIST 1.0//EN",
        systemId="http://www.apple.com/DTDs/PropertyList-1.0.dtd",
    )

    doc = imp.createDocument(None, 'plist', doctype)

    # create the plist element
    nodeList = doc.getElementsByTagName("plist")
    plist = nodeList.item(0)
    plist.setAttribute("version", "1.0");

    dict = doc.createElement("dict")
    plist.appendChild(dict)

    # create document nodes
    add_key_and_value(doc, state_key, base64data, "data", dict);
    add_key_and_value(doc, "manufacturer", manufacturer, "integer", dict);
    add_key_and_value(doc, "name", preset_name, "string", dict);
    add_key_and_value(doc, "subtype", subtype, "integer", dict);
    add_key_and_value(doc, "type", type, "integer", dict);
    add_key_and_value(doc, "version", "0", "integer", dict);

    f = open(preset_name + ".aupreset", "wb")
    f.write(doc.toxml("utf-8"))
    f.close()
    print "Created", preset_name + ".aupreset"
    print

DESCRIPTION="""
.fxp to .aupreset converter"
Original By: Colin Barry / colin@loomer.co.uk
Modifications By: Alex Rasmussen / alexras@acm.org
"""

def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)

    parser.add_argument('path', help='path to the directory of .fxp '
                        'and .fxb files to convert')
    parser.add_argument('type', help="the four-character type code for "
                        "the preset's audio unit")
    parser.add_argument('subtype', help="the four character subtype code "
                        "for the preset's audio unit file")
    parser.add_argument('manufacturer', help="the four character "
                        "manufacturer code for the preset's audio unit file")
    parser.add_argument("state_key", help="the key in the aupreset that "
                        "stores the preset's state")

    args = parser.parse_args()

    preset_type = id_to_integer(args.type)
    subtype = id_to_integer(args.subtype)
    manufacturer = id_to_integer(args.manufacturer)

    # enumerate all the .fxp files in the current directory
    os.chdir(args.path)

    fxpFileList = glob("*.fxp")

    if (len(fxpFileList) == 0):
        print "No .fxp files found in current directory", os.getcwd()

    for fname in fxpFileList:
        convert(fname, manufacturer, subtype, preset_type, args.state_key)

if __name__ == "__main__":
    sys.exit(main())

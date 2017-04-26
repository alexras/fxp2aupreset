#!/usr/bin/env python

# vst to au preset convert
# Colin Barry / colin@loomer.co.uk / www.loomer.co.uk
#
# Based on the aupreset to fxp converter found here
# http://www.rawmaterialsoftware.com/viewtopic.php?f=8&t=8337

import argparse
import re
from os import path, listdir, getcwd, chdir
import sys
import fnmatch
from xml.dom import minidom
from base64 import b64encode
from vst2preset import vst2preset

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

def au_param_from_preset_dict(param, d):
    return d[param].childNodes[0].data

def au_parameters_from_example(example_file):
    with open(example_file, 'r') as fp:
        parsed_example = minidom.parse(fp)

    # Convert list of XML keys and values into proper dict for easier handling
    aupreset_keys = filter(
        lambda x: x.nodeType == minidom.Node.ELEMENT_NODE,
        parsed_example.documentElement.getElementsByTagName('dict')[0]
        .getElementsByTagName('key'))

    # nextSibling twice to skip over newline text nodes
    aupreset_dict = dict({ (k.childNodes[0].data, k.nextSibling.nextSibling)
                           for k in aupreset_keys })

    au_type = au_param_from_preset_dict('type', aupreset_dict)
    au_subtype = au_param_from_preset_dict('subtype', aupreset_dict)
    au_manufacturer = au_param_from_preset_dict('manufacturer', aupreset_dict)

    data_elements = (parsed_example.documentElement
                     .getElementsByTagName('dict')[0]
                     .getElementsByTagName('data'))

    state_key = None

    if len(data_elements) > 1:
        # previousSibling twice to skip over newline text nodes
        state_key = (data_elements[1].previousSibling.previousSibling
                     .childNodes[0].data)
        print ("Guessing '%s' for state key, use --state_key to override" %
               (state_key))
    else:
        print "Couldn't infer state key from example"

    return (au_type, au_subtype, au_manufacturer, state_key)

DESCRIPTION="""
.fxp to .aupreset converter"
Original By: Colin Barry / colin@loomer.co.uk
Modifications By: Alex Rasmussen / alexras@acm.org
"""

def get_arguments(parser):
    args = parser.parse_args()

    if (args.example is not None):
        args.type, args.subtype, args.manufacturer, args.state_key = (
            au_parameters_from_example(args.example))
    else:
        for attr in ['type', 'subtype', 'manufacturer']:
            if getattr(args, attr) is None:
                sys.exit("ERROR: Must provide a %s or an example aupreset for "
                         "the instrument" % (attr))

        args.type = id_to_integer(args.type)
        args.subtype = id_to_integer(args.subtype)
        args.manufacturer = id_to_integer(args.manufacturer)

    if args.state_key is None:
        sys.exit("ERROR: Must provide a state key or an example aupreset for "
                 "the instrument from which we can infer one")

    return args

def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('path', help='path to the directory of .fxp '
                        'and .fxb files to convert')

    parser.add_argument('--type', '-t', help="the four-character type code for "
                        "the preset's audio unit")
    parser.add_argument('--subtype', '-s', help="the four character subtype "
                        "code for the preset's audio unit file")
    parser.add_argument('--manufacturer', '-m', help="the four character "
                        "manufacturer code for the preset's audio unit file")
    parser.add_argument("--state_key", '-k', help="the key in the aupreset that "
                        "stores the preset's state")
    parser.add_argument('--example', '-x', help='an example .aupreset file '
                        'from which to infer type, subtype, manufacturer and '
                        'state key')

    args = get_arguments(parser)

    # enumerate all the .fxp files in the current directory
    chdir(args.path)

    fxpFileList = fnmatch.filter(listdir(args.path), '*.[Ff][Xx][BbPp]')

    if (len(fxpFileList) == 0):
        print "No .fxp or .fxb files found in '%s'" % (getcwd())

    for fname in fxpFileList:
        convert(fname, args.manufacturer, args.subtype, args.type,
                args.state_key)

if __name__ == "__main__":
    sys.exit(main())

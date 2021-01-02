# -*- coding: utf-8 -*-
"""
Copyright (c) 2021 beyond-blockchain.org.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import argparse
import binascii
import hashlib
import json
import sys
import urllib.parse
import xml.etree.ElementTree as ET

from api.body import dict2xml
from bbc1.core import bbclib
from bbc1.lib import registry_lib


def argument_parser():
    argparser = argparse.ArgumentParser()
    subparsers = argparser.add_subparsers(dest="command_type", help='commands')

    # options
#    argparser.add_argument('-u', '--url_encode', action='store_true',
#            help='print URL-encoded string')

    # query command
    parser = subparsers.add_parser('query',
            help='Get query string')
    parser.add_argument('json_file', action='store', default=None,
            help='Certificate JSON file')

    return argparser.parse_args()


def print_query_string(json_file):
    with open(json_file) as f:
        dic = json.load(f)

    root = dict2xml(dic)

    proof = dic['proof']

    if proof is None:
        print('Not a certificate.')
        return

    spec = proof['spec']
    subtree = proof['subtree']

    s = ''
    for directive in subtree:
        s += 'r-' if directive['position'] == 'right' else 'l-'
        s += directive['digest'] + ':'
    s = s[:-1]

    qdic = {}
    qdic['certificate'] = ET.tostring(root, encoding='utf-8').decode('utf-8')
    qdic['subtree'] = s

    print(urllib.parse.urlencode(qdic))


def sys_check(args):
    return


if __name__ == '__main__':

    parsed_args = argument_parser()

    try:
        sys_check(parsed_args)

    except Exception as e:
        print(str(e))
        sys.exit(0)

    if parsed_args.command_type == 'query':
        print_query_string(parsed_args.json_file)

    sys.exit(0)


# end of certify_tool.py

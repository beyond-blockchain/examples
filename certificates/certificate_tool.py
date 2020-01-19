# -*- coding: utf-8 -*-
"""
Copyright (c) 2020 beyond-blockchain.org.

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
import sys
import urllib.parse
import xml.etree.ElementTree as ET

from bbc1.core import bbclib
from bbc1.lib import registry_lib


def argument_parser():
    argparser = argparse.ArgumentParser()
    subparsers = argparser.add_subparsers(dest="command_type", help='commands')

    # options
    argparser.add_argument('-p', '--private_key', type=str, default=None,
            help='private key in hexadecimal')
    argparser.add_argument('-u', '--url_encode', action='store_true',
            help='print URL-encoded string')

    # digest command
    parser = subparsers.add_parser('digest',
            help='Get <digest/> element')
    parser.add_argument('xml_string', action='store', default=None,
            help='XML string to get SHA-256 digest of')

    # keypair command
    parser = subparsers.add_parser('keypair',
            help='Generate a keypair')

    # sign command
    parser = subparsers.add_parser('sign',
            help='Sign a document')
    parser.add_argument('xml_string', action='store', default=None,
            help='Document XML string')

    return argparser.parse_args()


def generate_keypair():
    keypair = bbclib.KeyPair()
    keypair.generate()
    print('private key : {0}'.format(
            binascii.b2a_hex(keypair.private_key).decode()))
    print('public key : {0}'.format(
            binascii.b2a_hex(keypair.public_key).decode()))
    return


def print_digest(xml_string, url_encode):
    s = xml_string.encode('utf-8')
    e = ET.fromstring(s)
    if 'container' in e.attrib and e.attrib['container'] == 'true' \
            and len(e) > 0:
        digest = hashlib.sha256(registry_lib.file(e)).digest()
    else:
        digest = hashlib.sha256(s).digest()
    sD = '<digest>{0}</digest>'.format(binascii.b2a_hex(digest).decode())
    print(urllib.parse.quote(sD, safe='') if url_encode else sD)


def sign_document(xml_string, private_key):
    if private_key is None:
        keypair = bbclib.KeyPair()
        keypair.generate()

    else:
        keypair = bbclib.KeyPair(privkey=binascii.a2b_hex(private_key))

    s = xml_string.encode('utf-8')
    e = ET.fromstring(s)
    digest = hashlib.sha256(registry_lib.file(e)).digest()

    sig = keypair.sign(digest)

    print('algo="{0}"'.format('ecdsa-p256v1'))
    print('sig="{0}"'.format(binascii.b2a_hex(sig).decode()))
    print('pubkey="{0}"'.format(binascii.b2a_hex(keypair.public_key).decode()))


def sys_check(args):
    return


if __name__ == '__main__':

    parsed_args = argument_parser()

    try:
        sys_check(parsed_args)

    except Exception as e:
        print(str(e))
        sys.exit(0)

    if parsed_args.command_type == 'digest':
        print_digest(parsed_args.xml_string, parsed_args.url_encode)

    elif parsed_args.command_type == 'keypair':
        generate_keypair()

    elif parsed_args.command_type == 'sign':
        sign_document(parsed_args.xml_string, parsed_args.private_key)

    sys.exit(0)


# end of certificate_tool.py

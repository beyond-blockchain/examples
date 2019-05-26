# -*- coding: utf-8 -*-
"""
Copyright (c) 2019 beyond-blockchain.org.

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
import json
import os
import sys
import time
import xml.etree.ElementTree as ET

from bbc1.lib import app_support_lib, id_lib, registry_lib
from bbc1.core import bbclib, bbc_app, bbc_config
from bbc1.core.bbc_error import *
from bbc1.core.ethereum import bbc_ethereum
from bbc1.core.message_key_types import KeyType
from bbc1.core.subsystem_tool_lib import wait_check_result_msg_type
import bbc1


F_JSON_REG_INFO = 'certificate_registry_info.json'

KEY_REGISTRY = 'registry'
KEY_USER     = 'user'


class Certificate:

    def __init__(self, root):

        self.id = root.findtext('id', default='N/A')
        self.document = registry_lib.Document(
            document_id=bbclib.get_new_id(self.id, include_timestamp=False),
            root=root
        )


class Certifier:

    def __init__(self, is_test=False, is_verbose=False,
            domain_id_string=None,
            workingdir=bbc_config.DEFAULT_WORKING_DIR):

        self.is_test = is_test
        self.is_verbose = is_verbose

        if domain_id_string is None:
            self.domain_id = None

        else:
            self.domain_id = bytes(binascii.a2b_hex(domain_id_string))

        self.workingdir = workingdir
        self.run_client()

        self.dic = read_dic(self.domain_id)
        self.idPubkeyMap = id_lib.BBcIdPublickeyMap(self.domain_id)
        self.registry = self.get_registry()


    def check_domain_id(self):
        if self.domain_id is None:
            print("Error: please specify domain_id with '-d DOMAIN_ID'.")
            sys.exit(1)


    def get_registry(self):
        registry_id = self.dic[KEY_REGISTRY].user_id
        return registry_lib.BBcRegistry(self.domain_id, registry_id,
                registry_id, self.idPubkeyMap)


    def get_verification_dict(self, certificate):

        digest = self.registry.get_document_digest(
            certificate.document.document_id
        )

        if digest is None:
            return None

        self.client.verify_in_ledger_subsystem(None, digest)
        dat = wait_check_result_msg_type(self.client.callback,
                bbclib.MsgType.RESPONSE_VERIFY_HASH_IN_SUBSYS)

        return dat[KeyType.merkle_tree]


    def print_query_string(self, certificate):

        print("certificate id: {0}".format(certificate.id))

        if self.is_verbose:
            print("xml: {0}".format(ET.tostring(certificate.document.root,
                    encoding="utf-8").decode("utf-8")))

        dic = self.get_verification_dict(certificate)

        if dic is None:
            print("Failed: not registered.")
            return

        if dic == {}:
            print("Failed: ledger subsystem is not enabled.")
            return

        if dic[b'result'] == False:
            print("Failed: document digest is not found.")
            return

        spec = dic[b'spec']
        if spec[b'subsystem'] != b'ethereum':
            print("Failed: not stored in an Ethereum subsystem.")
            return

        subtree = dic[b'subtree']
        print(spec[b'contract_address'].decode('utf-8'))
        print(subtree)


    def register(self, certificate):

        print("certificate id: {0}".format(certificate.id))

        document = certificate.document

        if self.is_verbose:
            print("xml: {0}".format(ET.tostring(document.root,
                    encoding="utf-8").decode("utf-8")))
            print("registration to registry_lib.")

        if not self.is_test:
            self.registry.register_document(self.dic[KEY_USER].user_id,
                    document,
                    registry_lib.DocumentSpec(description="certificate"),
                    keypair=self.dic[KEY_REGISTRY].keypair)

        if self.is_verbose:
            print("registration to ledger subsystem.")

        if not self.is_test:
            self.client.register_in_ledger_subsystem(None,
                    self.registry.get_document_digest(document.document_id))
            dat = wait_check_result_msg_type(self.client.callback,
                    bbclib.MsgType.RESPONSE_REGISTER_HASH_IN_SUBSYS)


    def run_client(self):
        self.check_domain_id()
        self.client = bbc_app.BBcAppClient(port=bbc_config.DEFAULT_CORE_PORT,
                multiq=False, loglevel='all')
        self.client.set_user_id(bbclib.get_new_id('examples.certificates',
                include_timestamp=False))
        self.client.set_domain_id(self.domain_id)
        self.client.set_callback(bbc_app.Callback())
        ret = self.client.register_to_core()
        assert ret


    def verify(self, certificate):

        print("certificate id: {0}".format(certificate.id))

        if self.is_verbose:
            print("xml: {0}".format(ET.tostring(certificate.document.root,
                    encoding="utf-8").decode("utf-8")))

        dic = self.get_verification_dict(certificate)

        if dic is None:
            print("Failed: not registered.")
            return

        if dic == {}:
            print("Failed: ledger subsystem is not enabled.")
            return

        if dic[b'result'] == False:
            print("Failed: document digest is not found.")
            return

        spec = dic[b'spec']
        if spec[b'subsystem'] != b'ethereum':
            print("Failed: not stored in an Ethereum subsystem.")
            return

        if self.is_test:
            return

        subtree = dic[b'subtree']

        bbcConfig = bbc_config.BBcConfig(self.workingdir,
                os.path.join(self.workingdir, bbc_config.DEFAULT_CONFIG_FILE))
        config = bbcConfig.get_config()

        prevdir = os.getcwd()
        os.chdir(bbc1.__path__[0] + '/core/ethereum')

        eth = bbc_ethereum.BBcEthereum(
            config['ethereum']['network'],
            config['ethereum']['private_key'],
            contract_address=spec[b'contract_address'].decode('utf-8')
        )

        os.chdir(prevdir)

        digest = self.registry.get_document_digest(
            certificate.document.document_id
        )

        block_no = eth.verify(digest, subtree)

        if block_no <= 0:
            print("Failed: document digest is not found.")
        else:
            print("Verified: Merkle root is stored at block %d." % (block_no))


class User:

    def __init__(self, user_id, keypair):
        self.user_id = user_id
        self.keypair = keypair


    @staticmethod
    def from_dict(dic):
        user_id = bytes(binascii.a2b_hex(dic['user_id']))
        public_key = bytes(binascii.a2b_hex(dic['public_key']))
        private_key = bytes(binascii.a2b_hex(dic['private_key']))

        return User(user_id,
                bbclib.KeyPair(privkey=private_key, pubkey=public_key))


    def to_dict(self):
        return ({
            'user_id': binascii.b2a_hex(self.user_id).decode(),
            'public_key': binascii.b2a_hex(self.keypair.public_key).decode(),
            'private_key': binascii.b2a_hex(self.keypair.private_key).decode(),
        })


def argument_parser():
    argparser = argparse.ArgumentParser()
    subparsers = argparser.add_subparsers(dest="command_type", help='commands')

    # options
    argparser.add_argument('-d', '--domain_id', type=str, default=None,
            help='domain_id in hexadecimal')
    argparser.add_argument('-m', '--multiple', action='store_true',
            help='process multiple certificates in a file')
    argparser.add_argument('-t', '--test', action='store_true',
            help='does not register or verify')
    argparser.add_argument('-v', '--verbose', action='store_true',
            help='verbose output')
    argparser.add_argument('-w', '--workingdir', type=str,
            default=bbc_config.DEFAULT_WORKING_DIR,
            help='working directory name')

    # new_domain command
    parser = subparsers.add_parser('new_domain',
            help='Create a new bbc-1 domain')

    # query command
    parser = subparsers.add_parser('query',
            help='Generate verification query string(s)')
    parser.add_argument('file_name', action='store', default=None,
            help='Certificate file name')

    # register command
    parser = subparsers.add_parser('register',
            help='Register certificate(s)')
    parser.add_argument('file_name', action='store', default=None,
            help='Certificate file name')

    # verify command
    parser = subparsers.add_parser('verify',
            help='Verify certificate(s)')
    parser.add_argument('file_name', action='store', default=None,
            help='Certificate file name')

    return argparser.parse_args()


def create_certificates(file_name, process_multiple=False):

    tree = ET.parse(file_name)
    root = tree.getroot()

    certs = []

    if process_multiple:
        for e in root:
            certs.append(Certificate(e))

    else:
        certs.append(Certificate(root))

    return certs


def create_new_domain():

    domain_id = bbclib.get_new_id("certificate domain")
    tmpclient = bbc_app.BBcAppClient(port=bbc_config.DEFAULT_CORE_PORT,
            multiq=False, loglevel="all")
    tmpclient.domain_setup(domain_id)
    tmpclient.callback.synchronize()
    tmpclient.unregister_from_core()

    print("domain_id:")
    print(bbclib.convert_id_to_string(domain_id))

    idPubkeyMap = id_lib.BBcIdPublickeyMap(domain_id)
    dic = {}

    id, keypairs = idPubkeyMap.create_user_id(num_pubkeys=1)
    dic[KEY_REGISTRY] = User(id, keypairs[0])

    id, keypairs = idPubkeyMap.create_user_id(num_pubkeys=1)
    dic[KEY_USER] = User(id, keypairs[0])

    write_dic(domain_id, dic)


def read_dic(domain_id):
    dic = dict()

    try:
        path = app_support_lib.get_support_dir(domain_id) + F_JSON_REG_INFO
        f = open(path, 'r')
        j_dic = json.load(f)
        f.close()

    except FileNotFoundError:
        return dic

    for name, j_user in j_dic.items():
        dic[name] = User.from_dict(j_user)

    return dic


def sys_check(args):
    return
    




def write_dic(domain_id, dic):

    j_dic = dict()

    for name, user in dic.items():
        j_dic[name] = user.to_dict()

    path = app_support_lib.get_support_dir(domain_id) + F_JSON_REG_INFO
    f = open(path, 'w')
    json.dump(j_dic, f, indent=2)
    f.close()


if __name__ == '__main__':

    parsed_args = argument_parser()

    try:
        sys_check(parsed_args)

    except Exception as e:
        print(str(e))
        sys.exit(0)

    if parsed_args.command_type == 'new_domain':
        create_new_domain()

    else:
        certifier = Certifier(
            is_test=parsed_args.test,
            is_verbose=parsed_args.verbose,
            domain_id_string=parsed_args.domain_id,
            workingdir=parsed_args.workingdir
        )

        certs = create_certificates(parsed_args.file_name,
                process_multiple=parsed_args.multiple)

        if certifier.is_verbose:
            print("Processing {0} certificates.".format(len(certs)))

        if parsed_args.command_type == "query":
            for certificate in certs:
                certifier.print_query_string(certificate)

        elif parsed_args.command_type == "register":
            for certificate in certs:
                certifier.register(certificate)

        elif parsed_args.command_type == "verify":
            for certificate in certs:
                certifier.verify(certificate)

    sys.exit(0)


# end of certificates.py

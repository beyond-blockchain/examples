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
import bbc1
import binascii
import datetime
import hashlib
import io
import os
import string
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET

from bbc1.core.ethereum import bbc_ethereum
from bbc1.lib import registry_lib
from brownie import *
from flask import Blueprint, render_template, request, redirect, url_for, flash


S_CONTRACT_ADDRESS = '0xd123Ec03ACdbC36e4fA818c983C259049EE705e0'
S_NETWORK = 'ropsten'


def certify(cert_xml, subtree_string):

    if cert_xml is None or subtree_string is None:
        return failure_template('no-query')

    try:
        root = ET.fromstring(cert_xml)

    except ET.ParseError:
        return failure_template('xml-syntax')

    try:
        data = registry_lib.file(root)

    except ValueError as error:
        s = str(error)
        if s.startswith('pubkey'):
            return failure_template('no-pubkey', root=root)
        elif s.startswith('sig'):
            return failure_template('bad-sig', root=root)

    except KeyError as error:
        return failure_template('sig-algo', root=root)

    digest = hashlib.sha256(data).digest()

    subtree = []
    nodes = subtree_string.split(':')

    for node in nodes:
        s = node.split('-')
        if len(s) != 2 or not all(c in string.hexdigits for c in s[1]):
            return failure_template('subtree-syntax', root=root)
        dic = {}
        dic['position'] = 'right' if s[0] == 'r' else 'left'
        dic['digest'] = s[1]
        subtree.append(dic)

    eth = bbc_ethereum.BBcEthereum(
        S_NETWORK,
        private_key=None,
        contract_address=S_CONTRACT_ADDRESS,
        project_dir=bbc1.__path__[0] + '/core/ethereum'
    )

    block_no, digest0 = eth.verify_and_get_root(digest, subtree)

    if block_no <= 0:
        return failure_template('digest-mismatch', root=root)

    block = network.web3.eth.getBlock(block_no)

    realtime = datetime.datetime.fromtimestamp(block['timestamp'])

    return render_template('cert/success.html',
            title='Certificate Vefirication - Success',
            root=root, network=S_NETWORK, contract=S_CONTRACT_ADDRESS,
            block_no=block_no, realtime=realtime,
            get_date_string=get_date_string,
            merkle_root=binascii.b2a_hex(digest0).decode())


def failure_template(reason, root=''):

    return render_template('cert/failure.html',
            title='Certificate Verification - Failure',
            network=S_NETWORK, contract=S_CONTRACT_ADDRESS,
            reason=reason, root=root,
            get_date_string=get_date_string)


def get_date_string(timestamp):

    try:
        s = str(datetime.datetime.fromtimestamp(int(timestamp))).split()

    except ValueError:
        return 'N/A'

    return s[0]


cert = Blueprint('cert', __name__, template_folder='templates',
        static_folder='./static')


@cert.route('/')
def index():

    cert_xml = request.args.get('certificate')
    subtree_string = request.args.get('subtree')

    return certify(cert_xml, subtree_string)


@cert.route('/upload', methods=['GET', 'POST'])
def upload():

    if request.method == 'POST':
        filebuf = request.files.get('file')
        if filebuf is None:
            flash('no file')
            return redirect(request.url)

        s = filebuf.stream.read()

        dic = urllib.parse.parse_qs(s.decode('utf-8'))

        l_cert_xml = dic['certificate'] if 'certificate' in dic else None
        l_subtree_string = dic['subtree'] if 'subtree' in dic else None

        return certify(l_cert_xml[0], l_subtree_string[0])

    return '''
<!doctype html>
<html>
<head>
<meta charset="UTF-8"/>
<title>Upload Certificate</title>
</head>
<body>
<h2>Upload a Certificate File</h2>
<form method="post" enctype="multipart/form-data">
<p>
<input type="file" name="file"/>
<input type="submit" value="Upload"/>
</p>
</form>
</body>
'''


# end of cert_flask.py

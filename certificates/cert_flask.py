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
import os
import sys
import time
import xml.etree.ElementTree as ET

from bbc1.core.ethereum import bbc_ethereum
from brownie import *
from flask import Flask, render_template, request, redirect, url_for


S_CONTRACT_ADDRESS = '0xd123Ec03ACdbC36e4fA818c983C259049EE705e0'
S_NETWORK = 'ropsten'


app = Flask(__name__)


@app.route('/')
def index():

    cert_xml = request.args.get('certificate')
    subtree_string = request.args.get('subtree')

    root = ET.fromstring(cert_xml)
    date_string, time_string = str(datetime.datetime.fromtimestamp(
            int(root.findtext('date', default='0')))).split()

    dat = bytearray()
    for e in root:
        s = ET.tostring(e, encoding='utf-8')
        dat.extend(hashlib.sha256(s).digest())

    digest = hashlib.sha256(bytes(dat)).digest()

    subtree = []
    nodes = subtree_string.split(':')

    for node in nodes:
        s = node.split('-')
        dic = {}
        dic['position'] = 'right' if s[0] == 'r' else 'left'
        dic['digest'] = s[1]
        subtree.append(dic)

    prevdir = os.getcwd()
    os.chdir(bbc1.__path__[0] + '/core/ethereum')

    eth = bbc_ethereum.BBcEthereum(
        S_NETWORK,
        private_key=None,
        contract_address=S_CONTRACT_ADDRESS
    )

    os.chdir(prevdir)

    block_no = eth.verify(digest, subtree)

    if block_no <= 0:
        return render_template('failure.html', title='Certification - Failure',
            network=S_NETWORK, contract=S_CONTRACT_ADDRESS)

    block = network.web3.eth.getBlock(block_no)

    realtime = datetime.datetime.fromtimestamp(block['timestamp'])

    return render_template('success.html', title='Certification - Success',
            root=root, network=S_NETWORK, contract=S_CONTRACT_ADDRESS,
            block_no=block_no, realtime=realtime, date_string=date_string)


if __name__ == '__main__':
    app.run()


# end of cert_flask.py

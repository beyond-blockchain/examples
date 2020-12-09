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
import base64
import bbc1
import binascii
import hashlib
import json
import os
import requests
import string
import sys
import time

from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, request, session, abort, jsonify


# Put API host name here.
PREFIX_API = 'http://localhost:5000'


JST = timezone(timedelta(hours=+9), 'JST')


cert = Blueprint('cert', __name__, template_folder='templates',
        static_folder='./static')


def make_400_error(s):
    return {'error': {
        'code': 400,
        'name': 'Bad Request',
        'description': s,
    }}


@cert.route('/')
def index():
    return render_template('cert/index.html')


@cert.route('/build', methods=['POST'])
def build():
    s = request.form.get('json')

    headers = {'Content-Type': 'application/json'}

    if 'register' in request.form:

        try:
            dic = json.loads(s)

        except:
            return render_template('cert/error.html',
                        message=json.dumps(make_400_error('Bad JSON format'),
                        indent=2))

        if '_docs' in dic:
            docs = dic['_docs']

            # check for duplication
            for doc in docs:
                r = requests.get(PREFIX_API + '/api/proof', headers=headers,
                        data=json.dumps(doc, indent=2))
                res = r.json()

                if r.status_code == 200:
                    return render_template('cert/error.html',
                            message=json.dumps(make_400_error(
                            'Document already exists'), indent=2))

            # registration
            for doc in docs:
                r = requests.post(PREFIX_API + '/api/register',
                        headers=headers, data=json.dumps(doc, indent=2))
                res = r.json()

                if r.status_code != 200:
                    return render_template('cert/error.html',
                            message=json.dumps(res, indent=2))

        else:
            # check for duplication
            r = requests.get(PREFIX_API + '/api/proof', headers=headers,
                    data=s.encode('utf-8'))
            res = r.json()

            if r.status_code == 200:
                return render_template('cert/error.html',
                        message=json.dumps(make_400_error(
                        'Document already exists'), indent=2))

            # registration
            r = requests.post(PREFIX_API + '/api/register', headers=headers,
                    data=s.encode('utf-8'))
            res = r.json()

            if r.status_code != 200:
                return render_template('cert/error.html',
                        message=json.dumps(res, indent=2))

        return render_template('cert/results.html',
                results=json.dumps(res, indent=2),
                note='This was a non-blocking call. '
                + 'Writing a Merkle root to Ethereum is asynchronously '
                + 'performed according to domain configuration.')

    if 'proof' in request.form:
        r = requests.get(PREFIX_API + '/api/proof', headers=headers,
                data=s.encode('utf-8'))
        res = r.json()

        if r.status_code != 200:
            return render_template('cert/error.html',
                    message=json.dumps(res, indent=2))

        s1 = s.strip().strip('}').strip()
        s2 = json.dumps(res, indent=2).strip('{\n')

        return render_template('cert/results.html',
                results=json.dumps(res, indent=2), download=s1+',\n'+s2)

    if 'verify' in request.form:
        r = requests.get(PREFIX_API + '/api/verify', headers=headers,
                data=s.encode('utf-8'))
        res = r.json()

        if r.status_code != 200:
            return render_template('cert/error.html',
                    message=json.dumps(res, indent=2))

        return render_template('cert/results.html',
                results=json.dumps(res, indent=2),
                note='Stored Time: {0}'.format(datetime.fromtimestamp(
                res['time'])))

    if 'digest' in request.form:
        r = requests.get(PREFIX_API + '/api/digest', headers=headers,
                data=s.encode('utf-8'))
        res = r.json()

        if r.status_code != 200:
            return render_template('cert/error.html',
                    message=json.dumps(res, indent=2))

        return render_template('cert/results.html',
                results=json.dumps(res, indent=2),
                note='Replace the original key-value pair with the above pair '
                + 'to conceal part of the certificate.')


    if 'keypair' in request.form:
        r = requests.get(PREFIX_API + '/api/keypair', headers=headers)
        res = r.json()

        if r.status_code != 200:
            return render_template('cert/error.html',
                    message=json.dumps(res, indent=2))

        return render_template('cert/results.html',
                results=json.dumps(res, indent=2),
                note='Save "privkey" value (private key) safely.')


    if 'sign' in request.form:
        r = requests.get(PREFIX_API + '/api/sign', headers=headers,
                data=s.encode('utf-8'))
        res = r.json()

        if r.status_code != 200:
            return render_template('cert/error.html',
                    message=json.dumps(res, indent=2))

        return render_template('cert/results.html',
                results=json.dumps(res, indent=2),
                note='Put the above key-value pairs into your document.')


# end of cert/views.py

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


@cert.route('/')
def index():
    return render_template('cert/index.html')


@cert.route('/build', methods=['POST'])
def build():
    s = request.form.get('json')
#   dic = json.loads(s)

    headers = {'Content-Type': 'application/json'}

    if 'register' in request.form:
        r = requests.post(PREFIX_API + '/api/register', headers=headers,
                data=s)
        res = r.json()

        if r.status_code != 200:
            return render_template('cert/error.html',
                    message=res['error']['message'])
        return render_template('cert/results.html', results=json.dumps(res))

    if 'proof' in request.form:
        r = requests.get(PREFIX_API + '/api/proof', headers=headers,
                data=s)
        res = r.json()

        if r.status_code != 200:
            return render_template('cert/error.html',
                    message=res['error']['message'])
        return render_template('cert/results.html', results=json.dumps(res))

    if 'verify' in request.form:
        r = requests.get(PREFIX_API + '/api/verify', headers=headers,
                data=s)
        res = r.json()

        if r.status_code != 200:
            return render_template('cert/error.html',
                    message=res['error']['message'])
        return render_template('cert/results.html', results=json.dumps(res))


# end of cert/views.py

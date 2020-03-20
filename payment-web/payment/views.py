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
import base64
import bbc1
import binascii
import hashlib
import json
import os
import qrcode
import requests
import string
import sys
import time

from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, request, session, abort, jsonify, redirect
from io import BytesIO


# Prior to use this web application, please define a currency using API,
# and put the mint_id here.
# MINT_ID = 'e6500c9aefa1dddb4295dcfa102e574497dfa83baefa117b9f34f654606f876f'

# Put the initial amount when signed up here.
INIT_AMOUNT = '1000'

# Put API host name here, plus prefix for URL encoded in QR code.
PREFIX_API = 'http://127.0.0.1:5000'
PREFIX_QR  = 'http://127.0.0.1:5000'

# Put base time (to count transactions) in Unix time here.
BASE_TIME = 0

# Put the number of transactions to show in a list page here.
LIST_COUNT = 5


JST = timezone(timedelta(hours=+9), 'JST')


def get_balance(name, user_id):
    r = requests.get(PREFIX_API + '/api/status/' + user_id,
            params={'mint_id': session['mint_id']})
    res = r.json()

    if r.status_code != 200:
        return render_template('payment/error.html',
                message=res['error']['message'])

    return render_template('payment/balance.html', name=name, user_id=user_id,
            balance=res['balance'], symbol=res['symbol'],
            to_name=request.args.get('to_name'))


def make_qr(s):
    qr_img = qrcode.make(s)

    buf = BytesIO()
    qr_img.save(buf, format='png')

    qr_b64s = base64.b64encode(buf.getvalue()).decode('utf-8')
    qr_b64data = 'data:image/png;base64,{}'.format(qr_b64s)

    return qr_b64data


payment = Blueprint('payment', __name__, template_folder='templates',
        static_folder='./static')


@payment.route('/')
def index():
    if 'user_id' in session:
        return get_balance(session['name'], session['user_id'])

    return render_template('payment/index.html')

@payment.route('/currency', methods=['GET', 'POST'])
def define_currency():
    if request.method == 'GET':
        return render_template('/payment/currency.html')
    
    name = request.form.get('name')
    symbol = request.form.get('symbol')

    r = requests.post(PREFIX_API + '/api/currency', 
        json={'name': name, 'symbol': symbol})

    res = r.json()

    if 'error' in res:
        return render_template('/payment/error.html', message=res['error'])

    mint_id = res['mint_id']
    session['mint_id'] = mint_id

    return render_template('/payment/currency_spec.html', 
                    name=name, symbol=symbol, mint_id=mint_id)


@payment.route('/list')
def list():
    if 'user_id' not in session:
        return render_template('payment/index.html')

    name = session['name']

    offset = request.args.get('offset')

    if offset is None:
        offset = 0

    r = requests.get(PREFIX_API + '/api/transactions/' + session['mint_id'], params={
        'name': name,
        'basetime': BASE_TIME,
        'count': LIST_COUNT,
        'offset': offset,
    })
    res = r.json()

    for tx in res['transactions']:
        tx['timestamp'] = datetime.fromtimestamp(tx['timestamp'], JST)
        if len(tx['from_name']) <= 0:
            tx['from_name'] = 'PAYMENT'
            tx['label'] = '*JOINED*'

    return render_template('payment/list.html', name=name, count=LIST_COUNT,
            count_before=res['count_before'], count_after=res['count_after'],
            transactions=res['transactions'], symbol=res['symbol'])


@payment.route('/receive')
def receive():
    if 'user_id' not in session:
        return render_template('payment/index.html')

    name = session['name']

    s_url = PREFIX_QR + '/payment/transfer?to_name=' + name
    qr_b64data = make_qr(s_url)

    return render_template('payment/receive.html', name=name,
            qr_b64data=qr_b64data, qr_name=s_url)

@payment.route('/setup', methods=['GET', 'POST'])
def setup():
    if request.method == 'GET':
        r = requests.post(PREFIX_API + '/api/setup')
        res = r.json()
        return render_template('/payment/setup_success.html', domain_id=res['domain_id'])

@payment.route('/sign-in', methods=['GET', 'POST'])
def sign_in():
    if request.method == 'GET':
        return render_template('payment/sign-in.html')

    name = request.form.get('name')
    currency_name = request.form.get('currency_name')

    if name is None or len(name) <= 0:
        return render_template('payment/error.html', message='name is missing')

    if currency_name is None or len(name) <= 0:
        return render_template('payment/error.html', message='currency name is missing')

    r = requests.get(PREFIX_API + '/api/user', params={'name': name})
    res = r.json()

    if r.status_code != 200:
        return render_template('payment/error.html',
                message=res['error']['message'])

    session['name'] = name
    session['user_id'] = res['user_id']

    r = requests.get(PREFIX_API + '/api/currency', params={'name': currency_name})
    res = r.json()

    if r.status_code != 200:
        return render_template('payment/error.html',
                message=res['error']['message'])

    session['currency_name'] = currency_name
    session['mint_id'] = res['mint_id']

    return get_balance(name, session['user_id'])


@payment.route('/sign-out')
def sign_out():
    session.pop('user_id', None)
    session.pop('name', None)

    return render_template('payment/sign-in.html')


@payment.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'GET':
        return render_template('payment/sign-up.html')

    name = request.form.get('name')

    if name is None or len(name) <= 0:
        return render_template('payment/error.html', message='name is missing')

    r = requests.post(PREFIX_API + '/api/user', data={'name': name})
    res = r.json()

    if r.status_code != 201:
        return render_template('payment/error.html',
                message=res['error']['message'])

    user_id = res['user_id']

    session['name'] = name
    session['user_id'] = user_id

    r = requests.post(PREFIX_API + '/api/issue/' + session['mint_id'],
            data={'user_id': user_id, 'amount': INIT_AMOUNT})

    if r.status_code != 200:
        return render_template('payment/error.html',
                message=res['error']['message'])

    return get_balance(name, user_id)


@payment.route('/transfer', methods=['GET', 'POST'])
def transfer():
    if 'user_id' not in session:
        return render_template('payment/index.html')

    name = session['name']
    user_id = session['user_id']

    if request.method == 'GET':
        return get_balance(name, user_id)

    to_name = request.form.get('to_name')
    amount = request.form.get('amount')
    label = request.form.get('label')

    if to_name is None or len(to_name) <= 0:
        return render_template('payment/error.html',
                message='to_name is missing')

    if amount is None or len(amount) <= 0:
        return render_template('payment/error.html',
                message='amount is missing')

    if label is None:
        label = ''

    r = requests.get(PREFIX_API + '/api/user', params={'name': to_name})
    res = r.json()

    if r.status_code != 200:
        return render_template('payment/error.html',
                message=res['error']['message'])

    to_user_id = res['user_id']

    r = requests.post(PREFIX_API + '/api/transfer/' + session['mint_id'], data={
        'from_user_id': user_id,
        'to_user_id': to_user_id,
        'amount': amount,
        'label': label
    })

    if r.status_code != 200:
        return render_template('payment/error.html',
                message=res['error']['message'])

    return get_balance(name, user_id)


@payment.route('/update')
def update():
    if 'user_id' not in session:
        return render_template('payment/index.html')

    name = session['name']
    user_id = session['user_id']

    if name is None or len(name) <= 0:
        return render_template('payment/error.html',
                message='name is missing')
    if user_id is None or len(user_id) <= 0:
        return render_template('payment/error.html',
                message='user_id is missing')

    return get_balance(name, user_id)


# end of payment/views.py

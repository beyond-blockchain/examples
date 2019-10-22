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
import json
import os
import requests
import string
import sys
import time

from flask import Blueprint, render_template, request, abort, jsonify


# Prior to use this web application, please define a currency using API,
# and put the mint_id here.
MINT_ID = 'e6500c9aefa1dddb4295dcfa102e574497dfa83baefa117b9f34f654606f876f'

# Put the initial amount when signed up
INIT_AMOUNT = '1000'

# Put API host name here.
PREFIX_API = 'http://127.0.0.1:5000'


def get_balance(name, user_id):
    r = requests.get(PREFIX_API + '/api/status/' + user_id + \
            '?mint_id=' + MINT_ID)
    res = r.json()

    if r.status_code != 200:
        return render_template('payment/error.html',
                message=res['error']['message'])

    return render_template('payment/balance.html', name=name, user_id=user_id,
            balance=res['balance'], symbol=res['symbol'])


payment = Blueprint('payment', __name__, template_folder='templates',
        static_folder='./static')


@payment.route('/')
def index():
    return render_template('payment/index.html')


@payment.route('/sign-in')
def sign_in():
    return render_template('payment/sign-in.html')


@payment.route('/sign-in.do', methods=['POST'])
def sign_in_do():
    name = request.form.get('name')

    if name is None or len(name) <= 0:
        return render_template('payment/error.html', message='name is missing')

    r = requests.get(PREFIX_API + '/api/user' + '?name=' + name)
    res = r.json()

    if r.status_code != 200:
        return render_template('payment/error.html',
                message=res['error']['message'])

    return get_balance(name, res['user_id'])


@payment.route('/sign-up')
def sign_up():
    return render_template('payment/sign-up.html')


@payment.route('/sign-up.do', methods=['POST'])
def sign_up_do():
    name = request.form.get('name')

    if name is None or len(name) <= 0:
        return render_template('payment/error.html', message='name is missing')

    r = requests.post(PREFIX_API + '/api/user', data={'name': name})
    res = r.json()

    if r.status_code != 201:
        return render_template('payment/error.html',
                message=res['error']['message'])

    user_id = res['user_id']

    r = requests.post(PREFIX_API + '/api/issue/' + MINT_ID,
            data={'user_id': user_id, 'amount': INIT_AMOUNT})

    if r.status_code != 200:
        return render_template('payment/error.html',
                message=res['error']['message'])

    return get_balance(name, user_id)


@payment.route('/transfer.do', methods=['POST'])
def transfer_do():
    name = request.form.get('name')
    user_id = request.form.get('user_id')
    to_name = request.form.get('to_name')
    amount = request.form.get('amount')

    if to_name is None or len(to_name) <= 0:
        return render_template('payment/error.html',
                message='to_name is missing')

    if amount is None or len(amount) <= 0:
        return render_template('payment/error.html',
                message='amount is missing')

    r = requests.get(PREFIX_API + '/api/user' + '?name=' + to_name)
    res = r.json()

    if r.status_code != 200:
        return render_template('payment/error.html',
                message=res['error']['message'])

    to_user_id = res['user_id']

    r = requests.post(PREFIX_API + '/api/transfer/' + MINT_ID, data={
        'from_user_id': user_id,
        'to_user_id': to_user_id,
        'amount': amount
    })

    if r.status_code != 200:
        return render_template('payment/error.html',
                message=res['error']['message'])

    return get_balance(name, user_id)


@payment.route('/update.do', methods=['POST'])
def update_do():
    name = request.form.get('name')
    user_id = request.form.get('user_id')

    if name is None or len(name) <= 0:
        return render_template('payment/error.html',
                message='name is missing')
    if user_id is None or len(user_id) <= 0:
        return render_template('payment/error.html',
                message='user_id is missing')

    return get_balance(name, user_id)


# end of payment/views.py

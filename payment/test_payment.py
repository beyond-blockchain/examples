# -*- coding: utf-8 -*-
import os
import shutil
import subprocess


os.environ['BBC1_APP_SUPPORT_DIR'] = '.test'
try:
    shutil.rmtree('.test')
except FileNotFoundError:
    pass


def test_setup():
    res = subprocess.check_output([
        'python', 'payment.py', 'setup'
    ])
    assert res == b'domain b70ce05f is created.\n'


def test_def_user():
    res = subprocess.check_output([
        'python', 'payment.py', 'def-user', 'alice'
    ])
    assert res == b'user alice is defined.\n'

    res = subprocess.check_output([
        'python', 'payment.py', 'def-user', 'bob'
    ])
    assert res == b'user bob is defined.\n'

    res = subprocess.check_output([
        'python', 'payment.py', 'user'
    ])
    assert res == b' alice\n*bob\n'

    res = subprocess.check_output([
        'python', 'payment.py', 'user', 'alice'
    ])
    assert res == b'*alice\n bob\n'


def test_def_currency():
    res = subprocess.check_output([
        'python', 'payment.py', 'def-currency', 'Yen', 'JPY',
        'default_spec.json'
    ])
    assert res == b'currency Yen/JPY is defined.\n'

    res = subprocess.check_output([
        'python', 'payment.py', 'currency'
    ])
    assert res == b'*Yen\n'


def test_issue():
    res = subprocess.check_output([
        'python', 'payment.py', 'issue', '1000', 'alice'
    ])
    assert res == b'1000JPY is issued to alice.\n'

    res = subprocess.check_output([
        'python', 'payment.py', 'status', 'alice'
    ])
    assert res == b'balance = 1000JPY.\n'

    res = subprocess.check_output([
        'python', 'payment.py', 'status', 'bob'
    ])
    assert res == b'balance = 0JPY.\n'


def test_transfer():
    res = subprocess.check_output([
        'python', 'payment.py', 'transfer', '100', 'bob'
    ])
    assert res == b'100JPY is transferred to bob.\n'

    res = subprocess.check_output([
        'python', 'payment.py', 'status', 'alice'
    ])
    assert res == b'balance = 900JPY.\n'

    res = subprocess.check_output([
        'python', 'payment.py', 'status', 'bob'
    ])
    assert res == b'balance = 100JPY.\n'


def test_swap():
    res = subprocess.check_output([
        'python', 'payment.py', 'def-currency', 'Dollar', 'USD',
        'decimal_2.json'
    ])
    assert res == b'currency Dollar/USD is defined.\n'

    res = subprocess.check_output([
        'python', 'payment.py', 'currency'
    ])
    assert res == b' Yen\n*Dollar\n'

    res = subprocess.check_output([
        'python', 'payment.py', 'issue', '10', 'bob'
    ])
    assert res == b'10.00USD is issued to bob.\n'

    res = subprocess.check_output([
        'python', 'payment.py', 'status', 'alice'
    ])
    assert res == b'balance = 0.00USD.\n'

    res = subprocess.check_output([
        'python', 'payment.py', 'status', 'bob'
    ])
    assert res == b'balance = 10.00USD.\n'

    res = subprocess.check_output([
        'python', 'payment.py', 'currency', 'Yen'
    ])
    assert res == b'*Yen\n Dollar\n'

    res = subprocess.check_output([
        'python', 'payment.py', 'swap', '110', 'bob', '1', 'Dollar'
    ])
    assert res == b'110JPY is transferred to bob.\n' + \
                  b'1.00USD is transferred from bob.\n'

    res = subprocess.check_output([
        'python', 'payment.py', 'status', 'alice'
    ])
    assert res == b'balance = 790JPY.\n'

    res = subprocess.check_output([
        'python', 'payment.py', 'status', 'bob'
    ])
    assert res == b'balance = 210JPY.\n'

    res = subprocess.check_output([
        'python', 'payment.py', 'currency', 'Dollar'
    ])
    assert res == b' Yen\n*Dollar\n'

    res = subprocess.check_output([
        'python', 'payment.py', 'status', 'alice'
    ])
    assert res == b'balance = 1.00USD.\n'

    res = subprocess.check_output([
        'python', 'payment.py', 'status', 'bob'
    ])
    assert res == b'balance = 9.00USD.\n'


# end of test_payment.py

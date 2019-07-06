# -*- coding: utf-8 -*-
"""
Copyright (c) 2018 beyond-blockchain.org.

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
import sys
import time

from bbc1.lib import app_support_lib, id_lib, token_lib
from bbc1.core import bbc_app
from bbc1.core.bbc_config import DEFAULT_CORE_PORT
from bbc1.core import bbclib
from bbc1.core.bbc_error import *


F_JSON_CURRENCIES = 'payment_currencies.json'
F_JSON_USERS      = 'payment_users.json'


domain_id = bbclib.get_new_id("payment_test_domain", include_timestamp=False)


class User:

    def __init__(self, user_id, keypair, is_selected=False):
        self.user_id = user_id
        self.keypair = keypair
        self.is_selected = is_selected


    @staticmethod
    def from_dict(dic):
        user_id = bytes(binascii.a2b_hex(dic['user_id']))
        public_key = bytes(binascii.a2b_hex(dic['public_key']))
        private_key = bytes(binascii.a2b_hex(dic['private_key']))

        return User(user_id,
                bbclib.KeyPair(privkey=private_key, pubkey=public_key),
                dic['is_selected'])


    def to_dict(self):
        return ({
            'user_id': binascii.b2a_hex(self.user_id).decode(),
            'public_key': binascii.b2a_hex(self.keypair.public_key).decode(),
            'private_key': binascii.b2a_hex(self.keypair.private_key).decode(),
            'is_selected': self.is_selected,
        })


def argument_parser():
    argparser = argparse.ArgumentParser()
    subparsers = argparser.add_subparsers(dest="command_type", help='commands')

    # currency command
    parser = subparsers.add_parser('currency',
                        help='Show currencies or switch to a currency')
    parser.add_argument('name', nargs='?', action='store', default=None,
                        help='A currency name')

    # def-currency command
    parser = subparsers.add_parser('def-currency', help='Define a currency')
    parser.add_argument('name', action='store', help='A currency name')
    parser.add_argument('symbol', action='store', help='A currency symbol')
    parser.add_argument('file', action='store',
            help='Rest of the definition in JSON')

    # def-user command
    parser = subparsers.add_parser('def-user', help='Define a user')
    parser.add_argument('user_name', action='store', help='A user name')

    # issue command
    parser = subparsers.add_parser('issue',
                        help='Issue currency tokens to a user')
    parser.add_argument('amount', type=float, action='store',
                        help='Token amount')
    parser.add_argument('user_name', action='store', help='A user name')

    # new-keypair command
    parser = subparsers.add_parser('new-keypair',
                        help='Replace the key-pair for a user')
    parser.add_argument('user_name', action='store', help='A user name')

    # setup command
    parser = subparsers.add_parser('setup', help='Setup domain')

    # set-condition command
    parser = subparsers.add_parser('set-condition',
                        help='Set condition of currency')
    parser.add_argument('condition', type=int, action='store',
                        help='Currency condition')

    # status command
    parser = subparsers.add_parser('status',
                        help='Show status of user or currency')
    parser.add_argument('user_name', nargs='?', action='store', default=None,
                        help='A user name')

    # swap command
    parser = subparsers.add_parser('swap',
                        help='Atomically swap currency tokens between users')
    parser.add_argument('amount1', type=float, action='store',
                        help='Token amount')
    parser.add_argument('user_name', action='store', help='A user name')
    parser.add_argument('amount2', type=float, action='store',
                        help='Token amount')
    parser.add_argument('currency_name', action='store', help='currency name')

    # transfer command
    parser = subparsers.add_parser('transfer',
                        help='Transfer currency tokens to a user')
    parser.add_argument('amount', type=float, action='store',
                        help='Token amount')
    parser.add_argument('user_name', action='store', help='A user name')

    # user command
    parser = subparsers.add_parser('user',
                        help='Show users or switch to a user')
    parser.add_argument('user_name', nargs='?', action='store', default=None,
                        help='A user name')

    return argparser.parse_args()


def clear_selected(dic):
    for name, user in dic.items():
        user.is_selected = False


def define_currency(name, symbol, file, dic_currencies):
    if name in dic_currencies:
        print("currency %s is already defined." % (name))
        return
    if name in dic_users:
        print("%s is already defined as a user name." % (name))
        return

    idPubkeyMap = id_lib.BBcIdPublickeyMap(domain_id)
    mint_id, keypairs = idPubkeyMap.create_user_id(num_pubkeys=1)

    f = open(file, 'r')
    j_currency_spec = json.load(f)
    f.close()

    j_currency_spec['name'] = name
    j_currency_spec['symbol'] = symbol

    currency_spec = token_lib.CurrencySpec(j_currency_spec)

    mint = token_lib.BBcMint(domain_id, mint_id, mint_id, idPubkeyMap)
    mint.set_condition(0, keypair=keypairs[0])
    mint.set_currency_spec(currency_spec, keypair=keypairs[0])

    clear_selected(dic_currencies)
    dic_currencies[currency_spec.name] = User(mint_id, keypairs[0], True)

    write_dic(F_JSON_CURRENCIES, dic_currencies)

    print("currency %s/%s is defined." % (name, symbol))


def define_user(name, dic_users):
    if name in dic_users:
        print("user %s is already defined." % (name))
        return
    if name in dic_currencies:
        print("%s is already defined as a currency name." % (name))
        return

    idPubkeyMap = id_lib.BBcIdPublickeyMap(domain_id)
    user_id, keypairs = idPubkeyMap.create_user_id(num_pubkeys=1)

    clear_selected(dic_users)
    dic_users[name] = User(user_id, keypairs[0], True)

    write_dic(F_JSON_USERS, dic_users)

    print("user %s is defined." % (name))


def get_selected(dic):
    for name, user in dic.items():
        if user.is_selected:
            return name, user


def issue_to_user(name, amount, dic_currencies, dic_users):
    _, currency = get_selected(dic_currencies)

    idPubkeyMap = id_lib.BBcIdPublickeyMap(domain_id)
    mint = token_lib.BBcMint(domain_id, currency.user_id, currency.user_id,
            idPubkeyMap)

    currency_spec = mint.get_currency_spec()
    value = int(amount * (10 ** currency_spec.decimal))

    mint.issue(dic_users[name].user_id, value, keypair=currency.keypair)

    value_string = ("{0:.%df}" % (currency_spec.decimal)).format(
            value / (10 ** currency_spec.decimal))
    print("%s%s is issued to %s." % (value_string, currency_spec.symbol, name))


def list_users(dic):
    for name, user in dic.items():
        if user.is_selected:
            print("*" + name)
        else:
            print(" " + name)


def read_dic(file_name):
    dic = dict()

    try:
        f = open(app_support_lib.get_support_dir(domain_id) + file_name, 'r')
        j_dic = json.load(f)
        f.close()
    except FileNotFoundError:
        return dic

    for name, j_user in j_dic.items():
        dic[name] = User.from_dict(j_user)

    return dic


def replace_keypair(name, dic, file_name):
    for name0, user in dic.items():
        if name0 == name:
            keypair_old = user.keypair
            keypair = bbclib.KeyPair()
            keypair.generate()
            idPubkeyMap = id_lib.BBcIdPublickeyMap(domain_id)
            idPubkeyMap.update(user.user_id,
                    public_keys_to_replace=[keypair.public_key],
                    keypair=keypair_old)
            user.keypair = keypair
            break

    write_dic(file_name, dic)
    print("public key for %s is renewed:" % (name))
    print("old:", binascii.b2a_hex(keypair_old.public_key).decode())
    print("new:", binascii.b2a_hex(keypair.public_key).decode())


def select_user(name, dic, file_name):
    clear_selected(dic)
    for name0, user in dic.items():
        if name0 == name:
            user.is_selected = True
            break

    write_dic(file_name, dic)
    list_users(dic)


def setup():
    tmpclient = bbc_app.BBcAppClient(port=DEFAULT_CORE_PORT, multiq=False,
            loglevel="all")
    tmpclient.domain_setup(domain_id)
    tmpclient.callback.synchronize()
    tmpclient.unregister_from_core()
    print("domain %s is created." % (binascii.b2a_hex(domain_id[:4]).decode()))


def show_user(name, dic_currencies, dic_users):
    _, mint_info = get_selected(dic_currencies)

    idPubkeyMap = id_lib.BBcIdPublickeyMap(domain_id)
    mint = token_lib.BBcMint(domain_id, mint_info.user_id, mint_info.user_id,
            idPubkeyMap)

    currency_spec = mint.get_currency_spec()

    value = mint.get_balance_of(dic_users[name].user_id)
    value_string = ("{0:.%df}" % (currency_spec.decimal)).format(
            value / (10 ** currency_spec.decimal))

    print("balance = %s%s." % (value_string, currency_spec.symbol))


def sys_check(args):
    return


def swap_between_users(name, amount1, amount2, currency_name, dic_currencies,
        dic_users):
    _, currency = get_selected(dic_currencies)
    _, user = get_selected(dic_users)
    counter_currency = dic_currencies[currency_name]
    counter_user = dic_users[name]

    idPubkeyMap = id_lib.BBcIdPublickeyMap(domain_id)
    mint = token_lib.BBcMint(domain_id, currency.user_id, currency.user_id,
            idPubkeyMap)
    counter_mint = token_lib.BBcMint(domain_id,
            counter_currency.user_id, counter_currency.user_id, idPubkeyMap)

    currency_spec = mint.get_currency_spec()
    counter_currency_spec = counter_mint.get_currency_spec()
    value1 = int(amount1 * (10 ** currency_spec.decimal))
    value2 = int(amount2 * (10 ** counter_currency_spec.decimal))

    mint.swap(counter_mint, user.user_id, counter_user.user_id,
            value1, value2,
            keypair_this=user.keypair, keypair_that=counter_user.keypair,
            keypair_mint=currency.keypair,
            keypair_counter_mint=counter_currency.keypair)
    time.sleep(1) # this should be unnecessary but token_lib is incomplete now.

    value1_string = ("{0:.%df}" % (currency_spec.decimal)).format(
            value1 / (10 ** currency_spec.decimal))
    value2_string = ("{0:.%df}" % (counter_currency_spec.decimal)).format(
            value2 / (10 ** counter_currency_spec.decimal))

    print("%s%s is transferred to %s." % (value1_string,
            currency_spec.symbol, name))
    print("%s%s is transferred from %s." % (value2_string,
            counter_currency_spec.symbol, name))


def transfer_to_user(name, amount, dic_currencies, dic_users):
    _, currency = get_selected(dic_currencies)
    _, user = get_selected(dic_users)

    idPubkeyMap = id_lib.BBcIdPublickeyMap(domain_id)
    mint = token_lib.BBcMint(domain_id, currency.user_id, currency.user_id,
            idPubkeyMap)

    currency_spec = mint.get_currency_spec()
    value = int(amount * (10 ** currency_spec.decimal))

    mint.transfer(user.user_id, dic_users[name].user_id, value,
            keypair_from=user.keypair, keypair_mint=currency.keypair)

    value_string = ("{0:.%df}" % (currency_spec.decimal)).format(
            value / (10 ** currency_spec.decimal))
    print("%s%s is transferred to %s." % (value_string,
            currency_spec.symbol, name))


def write_dic(file_name, dic):
    j_dic = dict()

    for name, user in dic.items():
        j_dic[name] = user.to_dict()

    f = open(app_support_lib.get_support_dir(domain_id) + file_name, 'w')
    json.dump(j_dic, f, indent=2)
    f.close()


if __name__ == '__main__':
    parsed_args = argument_parser()
    try:
        sys_check(parsed_args)
    except Exception as e:
        print(str(e))
        sys.exit(0)

    dic_currencies = read_dic(F_JSON_CURRENCIES)
    dic_users = read_dic(F_JSON_USERS)

    if parsed_args.command_type == "currency":
        if parsed_args.name is None:
            list_users(dic=dic_currencies)
        else:
            select_user(name=parsed_args.name, dic=dic_currencies,
                    file_name=F_JSON_CURRENCIES)

    elif parsed_args.command_type == "def-currency":
        define_currency(name=parsed_args.name, symbol=parsed_args.symbol,
                file=parsed_args.file, dic_currencies=dic_currencies)

    elif parsed_args.command_type == "def-user":
        define_user(name=parsed_args.user_name, dic_users=dic_users)

    elif parsed_args.command_type == "issue":
        issue_to_user(name=parsed_args.user_name, amount=parsed_args.amount,
                dic_currencies=dic_currencies, dic_users=dic_users)

    elif parsed_args.command_type == "new-keypair":
        replace_keypair(name=parsed_args.user_name, dic=dic_users,
                file_name=F_JSON_USERS)

    elif parsed_args.command_type == "setup":
        setup()

    elif parsed_args.command_type == "set-condition":
        sys.exit(0)

    elif parsed_args.command_type == "status":
        if parsed_args.user_name is not None:
            show_user(name=parsed_args.user_name,
                    dic_currencies=dic_currencies, dic_users=dic_users)

    elif parsed_args.command_type == "swap":
        swap_between_users(name=parsed_args.user_name,
                amount1=parsed_args.amount1,
                amount2=parsed_args.amount2,
                currency_name=parsed_args.currency_name,
                dic_currencies=dic_currencies, dic_users=dic_users)

    elif parsed_args.command_type == "transfer":
        transfer_to_user(name=parsed_args.user_name, amount=parsed_args.amount,
                dic_currencies=dic_currencies, dic_users=dic_users)

    elif parsed_args.command_type == "user":
        if parsed_args.user_name is None:
            list_users(dic=dic_users)
        else:
            select_user(name=parsed_args.user_name, dic=dic_users,
                    file_name=F_JSON_USERS)

    sys.exit(0)

# end of payment.py

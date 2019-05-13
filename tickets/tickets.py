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
import sys
import time

from bbc1.lib import app_support_lib, id_lib, ticket_lib
from bbc1.core import bbc_app
from bbc1.core.bbc_config import DEFAULT_CORE_PORT
from bbc1.core import bbclib
from bbc1.core.bbc_error import *


F_JSON_SERVICES = 'tickets_services.json'
F_JSON_USERS    = 'tickets_users.json'


domain_id = bbclib.get_new_id("tickets_test_domain", include_timestamp=False)


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

    # def-service command
    parser = subparsers.add_parser('def-service', help='Define a service')
    parser.add_argument('name', action='store', help='A setvice name')

    # def-user command
    parser = subparsers.add_parser('def-user', help='Define a user')
    parser.add_argument('user_name', action='store', help='A user name')

    # issue command
    parser = subparsers.add_parser('issue',
                        help='Issue a ticket for a user')
    parser.add_argument('description', action='store',
                        help='Ticket description')
    parser.add_argument('user_name', action='store', help='A user name')

    # new-keypair command
    parser = subparsers.add_parser('new-keypair',
                        help='Replace the key-pair for a user')
    parser.add_argument('user_name', action='store', help='A user name')

    # redeem command
    parser = subparsers.add_parser('redeem',
                        help='Redeem a ticket from a user')
    parser.add_argument('ticket_id', action='store', help='Ticket ID')

    # service command
    parser = subparsers.add_parser('service',
                        help='Show services or switch to a service')
    parser.add_argument('name', nargs='?', action='store', default=None,
                        help='A service name')

    # setup command
    parser = subparsers.add_parser('setup', help='Setup domain')

    # status command
    parser = subparsers.add_parser('status',
                        help='Show status of user or service')
    parser.add_argument('user_name', nargs='?', action='store', default=None,
                        help='A user name')

    # transfer command
    parser = subparsers.add_parser('transfer',
                        help='Transfer a ticket to a user')
    parser.add_argument('ticket_id', action='store', help='Ticket ID')
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


def define_service(name, dic_services):
    if name in dic_services:
        print("service %s is already defined." % (name))
        return
    if name in dic_users:
        print("%s is already defined as a user name." % (name))
        return

    idPubkeyMap = id_lib.BBcIdPublickeyMap(domain_id)
    service_id, keypairs = idPubkeyMap.create_user_id(num_pubkeys=1)

    service = ticket_lib.BBcTicketService(domain_id, service_id, service_id,
            idPubkeyMap)

    clear_selected(dic_services)
    dic_services[name] = User(service_id, keypairs[0], True)

    write_dic(F_JSON_SERVICES, dic_services)

    print("service %s is defined." % (name))


def define_user(name, dic_users):
    if name in dic_users:
        print("user %s is already defined." % (name))
        return
    if name in dic_services:
        print("%s is already defined as a service name." % (name))
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


def issue_to_user(name, description, dic_services, dic_users):
    _, service_user = get_selected(dic_services)

    idPubkeyMap = id_lib.BBcIdPublickeyMap(domain_id)
    service = ticket_lib.BBcTicketService(domain_id, service_user.user_id,
            service_user.user_id, idPubkeyMap)

    spec = ticket_lib.TicketSpec(description=description, value=1, unit="x")

    ticket_id, _ = service.issue(dic_users[name].user_id, spec,
            keypair=service_user.keypair)

    print("ticket %s is issued to %s." % (bbclib.convert_id_to_string(
			ticket_id), name))


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


def redeem_from_user(ticket_id, dic_services, dic_users):
    _, service_user = get_selected(dic_services)
    name, user = get_selected(dic_users)

    idPubkeyMap = id_lib.BBcIdPublickeyMap(domain_id)
    service = ticket_lib.BBcTicketService(domain_id, service_user.user_id,
            service_user.user_id, idPubkeyMap)

    if not service.is_valid_holder(user.user_id, ticket_id):
        print("%s is not the valid holder." % (name))
        return

    service.redeem(user.user_id, ticket_id, keypair_from=user.keypair,
            keypair_service=service_user.keypair)

    print("%s is redeemed from %s." % (bbclib.convert_id_to_string(ticket_id),
            name))


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


def show_user(name, dic_services, dic_users):
    _, service_user = get_selected(dic_services)

    idPubkeyMap = id_lib.BBcIdPublickeyMap(domain_id)
    service = ticket_lib.BBcTicketService(domain_id, service_user.user_id,
            service_user.user_id, idPubkeyMap)
    ticket_dict = service.get_balance_of(dic_users[name].user_id)
    for ticket_id, ticket in ticket_dict.items():
        print("%s: %d%s" % (binascii.b2a_hex(ticket_id).decode(), ticket.spec.value, ticket.spec.unit))

# FIXME
#    print("balance = %s%s." % (value_string, currency_spec.symbol))


def show_all_tickets(dic_services, dic_users):
    _, service_user = get_selected(dic_services)

    idPubkeyMap = id_lib.BBcIdPublickeyMap(domain_id)
    service = ticket_lib.BBcTicketService(domain_id, service_user.user_id,
            service_user.user_id, idPubkeyMap)
    for user_name, user in dic_users.items():
        ticket_dict = service.get_balance_of(user.user_id)
        assert ticket_dict
        for ticket_id, ticket in ticket_dict.items():
            print("%s: %d%s" % (binascii.b2a_hex(ticket_id).decode(), ticket.spec.value, ticket.spec.unit))


def sys_check(args):
    return


def transfer_to_user(name, ticket_id, dic_services, dic_users):
    _, service_user = get_selected(dic_services)
    name0, user = get_selected(dic_users)

    idPubkeyMap = id_lib.BBcIdPublickeyMap(domain_id)
    service = ticket_lib.BBcTicketService(domain_id, service_user.user_id,
            service_user.user_id, idPubkeyMap)

    if not service.is_valid_holder(user.user_id, ticket_id):
        print("%s is not the valid holder." % (name0))
        return

    service.transfer(user.user_id, dic_users[name].user_id, ticket_id,
            keypair_from=user.keypair, keypair_service=service_user.keypair)

    print("%s is transferred to %s." % (bbclib.convert_id_to_string(ticket_id),
            name))


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

    dic_services = read_dic(F_JSON_SERVICES)
    dic_users = read_dic(F_JSON_USERS)

    if parsed_args.command_type == "def-service":
        define_service(name=parsed_args.name, dic_services=dic_services)

    elif parsed_args.command_type == "def-user":
        define_user(name=parsed_args.user_name, dic_users=dic_users)

    elif parsed_args.command_type == "issue":
        issue_to_user(name=parsed_args.user_name,
                description=parsed_args.description,
                dic_services=dic_services, dic_users=dic_users)

    elif parsed_args.command_type == "new-keypair":
        replace_keypair(name=parsed_args.user_name, dic=dic_users,
                file_name=F_JSON_USERS)

    elif parsed_args.command_type == "redeem":
        redeem_from_user(ticket_id=bbclib.convert_idstring_to_bytes(
                parsed_args.ticket_id),
                dic_services=dic_services, dic_users=dic_users)

    if parsed_args.command_type == "service":
        if parsed_args.name is None:
            list_users(dic=dic_services)
        else:
            select_user(name=parsed_args.name, dic=dic_services,
                    file_name=F_JSON_SERVICES)

    elif parsed_args.command_type == "setup":
        setup()

    elif parsed_args.command_type == "status":
        if parsed_args.user_name is not None:
            show_user(name=parsed_args.user_name,
                    dic_services=dic_services, dic_users=dic_users)
        else:
            show_all_tickets(dic_services, dic_users)

    elif parsed_args.command_type == "transfer":
        transfer_to_user(name=parsed_args.user_name,
                ticket_id=bbclib.convert_idstring_to_bytes(
                        parsed_args.ticket_id),
                dic_services=dic_services, dic_users=dic_users)

    elif parsed_args.command_type == "user":
        if parsed_args.user_name is None:
            list_users(dic=dic_users)
        else:
            select_user(name=parsed_args.user_name, dic=dic_users,
                    file_name=F_JSON_USERS)

    sys.exit(0)


# end of tickets.py

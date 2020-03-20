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

from flask import Flask


app = Flask(__name__)


from api.body import api
app.register_blueprint(api, url_prefix='/api')

from payment.views import payment
app.register_blueprint(payment, url_prefix='/payment')


app.secret_key = '!jnTCz._JM6eDRQW!xiRpA!M.8GdZy6cHnjX.!pY3@3Q2AjD_oyQh'


def parse_args():
    
    parser = argparse.ArgumentParser()

    parser.add_argument("-ip", "--ip_addr", type=str, default="127.0.0.1", help="host IP address")
    parser.add_argument("-p", "--port", type=int, default=5000, help="port number")
    parser.add_argument("--debug", action="store_true", help="turn on debug mode")

    return parser.parse_args()


if __name__ == '__main__':

    args = parse_args()

    port = args.port
    ip = args.ip_addr
    debug = args.debug

    app.run(host=ip, port=port , threaded=True, debug=debug)


# end of index.py

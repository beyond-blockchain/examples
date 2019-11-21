Payment Web
==========
This app provides very simple, non-secure Web API sample to provide functionality equivalent to payment example, plus a very simple sample Web application to use the API.

To use, first POST 'api/setup' to set up, and POST 'api/currency' to define a currency and obtain a mint_id. Then replace MINT_ID in 'payment/views.py' with the obtained mint_id.

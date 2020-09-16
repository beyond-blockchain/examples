Payment Web
==========
This app provides very simple, non-secure Web API sample to provide functionality equivalent to payment example, plus a very simple sample Web application to use the API.

To use, first POST 'api/setup' to set up.

```shell
$ curl -X POST -H "Content-Type: application/json" -d '{"domain_id":DOMAIN_ID}' IP_ADDRESS:5000/api/setup
{"domain_id":DOMAIN_ID} # returned
```

And POST 'api/currency' to define a currency and obtain a mint_id. Then replace MINT_ID in 'payment/views.py' with the obtained mint_id.

```shell
$ curl -X POST -H "Content-Type: application/json" -d '{"name":NAME, "symbol":SYMBOL, "mint_id":MINT_ID}' IP_ADDRESS:5000/api/currency
{"mint_id":MINT_ID,"name":NAME,"symbol":SYMBOL} # returned
```
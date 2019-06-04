Certificates
============

This app allows a user to do the following: \* register single or
multiple certificates to BBc-1 and the ledger subsystem \* verify the
content of certificates and the registration date & time. \* generate
verification query strings so that certificates can be verified
elsewhere Also provides a sample Flask web app for verifying
certificates.

Dependencies
------------

-  bbc1 >= 1.3
-  bbc1-lib-registry >= 0.4
-  ledger_subsystem >= 0.13.2
-  Flask >= 1.0.1

Installing dependencies
-----------------------

You need to pip-install bbc1 and Flask. Other, BBc-1 libraries are
currently at late development stage, and you will need to do
``git clone -b develop [URI]`` to clone the project’s development
branch, go to the project directory and ``python setup.py sdist`` to
generate an installer tar ball, and then
``pip install dist/[tar.gz file]``.

-  For bbc1, see
   `tutorials <https://github.com/beyond-blockchain/bbc1/tree/develop/docs>`__
-  Those tutorials are in Japanese for the time being.

.. _certificates-1:

Certificates
------------

A certificate for this app is an XML stanza. For example, the following
stanza with for container can be a valid certificate.

::

   <c>
     <id>000-000-0001</id>
     <name>Benjamin B. Clark</name>
     <membership>Fujisawa Don Tacos</membership>
     <expires-at>1906773886</expires-at>
   </c>

If you want to handle multiple certificates at one time, you can express
that as follows, for example.

::

   <set>
     <c>
       <id>000-000-0001</id>
       <name>Benjamin B. Clark</name>
       <membership>Fujisawa Don Tacos</membership>
       <expires-at>1906773886</expires-at>
     </c>
     <c>
       <id>000-000-0002</id>
       <name>Bettina B. Cameron</name>
       <membership>Fujisawa Don Tacos</membership>
       <expires-at>1906773886</expires-at>
     </c>
   </set>

The tag of the top-level element (‘set’ in the above) can be anything.
So is the tag of the element that contains the content of the
certificates (‘c’ in the above). To get the cryptographic digest of the
certificate (for proof), bbc1-lib-registry takes each element (, , , of
the above), calculate their SHA-256 digest, concatinate them all, and
then calculate its SHA-256 digest.

There are tags that give special meanings to the text. \* **** (any
level) Number or string that identifies the certificate. \* **** (first
level) Digest (SHA-256) of a hidden element (functionality of
bbc1-lib-registry). Upon getting the cryprographic digest of the
certificate, the text is considered as the hexadecimal representation of
the digest of the element at the position. \* **** Unix time, presented
as a date string for the time zone in the default locale of the
environment (first level).

How to use certificates.py
--------------------------

Below, it is assumed that bbc_core.py runs at the user’s home directory,
and Ethereum’s ropsten testnet is used. At first, bbc_core.py should be
stopped. 1. Set up ledger subsystem (this writes to BBc-1 core’s config
file)
``eth_subsystem_tool.py -w ~/.bbc1 auto [infura.io project ID] [private key]``
2. Start bbc_core.py 3. Create a domain.
``python certificates.py new_domain`` Take note (make a copy) of the
displayed domain id. 4. Stop bbc_core.py (because again we will write to
BBc-1 core’s config file) 5. Configure Merkle tree settings of the
ledger subsystem
``eth_subsystem_tool.py -w ~/.bbc1 -d [domain id] config_tree [number of certificates] [seconds]``
This configures the subsystem so that Merkle tree is closed and Merkle
root is written to Ethereum blockchain upon reaching either the
specified number of processed certificates or the specified seconds. 6.
Start bbc_core.py 7. Enable the ledger subsystem at BBc-1 core
``eth_subsystem_tool.py -w ~/.bbc1 -d [domain id] enable`` 8. Register
certificates \* Single certificate
``python certificates.py -d [domain id] register [certificate XML file]``
\* Multiple certificates in one file
``python certificates.py -d [domain id] -m register [certificate XML file]``
9. Verify certificates \* Single certificate
``python certificates.py -d [domain id] verify [certificate XML file]``
\* Multiple certificates in one file
``python certificates.py -d [domain id] -m verify [certificate XML file]``
10. Generate verification query strings for certificates \* Single
certificate
``python certificates.py -d [domain id] query [certificate XML file]``
\* Multiple certificates in one file
``python certificates.py -d [domain] -m query [certificate XML file]``

How to use cert_flask.py
------------------------

This is a simple web service to verify a certificate using the query
string generated using the **query** command of certificates.py The
functionality is wrapped by index.py.

::

   python index.py

The web service runs on localhost:5000. Try
``localhost:5000/?certificate=...&subtree=...`` to verify a certificate.

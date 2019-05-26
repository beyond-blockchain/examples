Certificates
============

This app allows a user to do the following: \* register single or
multiple certificates to BBc-1 and the ledger subsystem \* verify the
content of certificates and the registration date & time. \* generate
verification query strings so that certificates can be verified
elsewhere

How to use
==========

1. Set up ledger subsystem
2. Start bbc_core.py

-  See
   `tutorials <https://github.com/beyond-blockchain/bbc1/tree/develop/docs>`__
-  Those tutorials are in Japanese for the time being.

3. Create a domain. ``python certificates.py new_domain`` You then need
   to configure the domain and enable ledger subsystem with
   eth_subsystem_tool.py
4. Register certificates

   -  Single certificate
      ``python certificates.py -d [domain] register [certificate XML file]``
   -  Multiple certificates in one file
      ``python certificates.py -d [domain] -m register [certificate XML file]``

5. Verify certificates

   -  Single certificate
      ``python certificates.py -d [domain] verify [certificate XML file]``
   -  Multiple certificates in one file
      ``python certificates.py -d [domain] -m verify [certificate XML file]``

6. Generate verification query strings for certificates

   -  Single certificate
      ``python certificates.py -d [domain] query [certificate XML file]``

      -  Multiple certificates in one file

      ::

         python certificates.py -d [domain] -m query [certificate XML file]

Certificates
==========
This app allows a user to do the following:
* register single or multiple certificates to BBc-1 and the ledger subsystem
* verify the content of certificates and the registration date & time.
* generate verification query strings (which can be the contents of certificate files) so that certificates can be verified elsewhere.

Also provides a sample Flask web app for verifying certificates, and a tool for signed certificates and privacy control.

## Dependencies
* bbc1 >= 1.5
* py-bbclib >= 1.6
* bbc1-lib-std >= 0.19
* bbc1-lib-registry >= 0.8
* ledger_subsystem >= 0.14.1
* Flask >= 1.1.1

## Installing dependencies
You need to pip-install bbc1 and Flask. Others (BBc-1 libraries bbc1-lib-?? and ledger_subsystem) are currently at their late development stages, and you will need to do `git clone -b develop [URI]`  to clone the project's development branch, go to the project directory and `python setup.py sdist` to generate an installer tar ball, and then `pip install dist/[tar.gz file]`.

* For further information on installing and using bbc1, see [tutorials](https://github.com/beyond-blockchain/bbc1/tree/develop/docs)
* Those tutorials are in Japanese for the time being.

## Certificates
A certificate for this app is an XML stanza. For example, the following stanza with ```<c/>``` for container can be a valid certificate.
```
<c>
  <id>000-000-0001</id>
  <name>Benjamin B. Clark</name>
  <membership>Fujisawa Don Tacos</membership>
  <date>1559692800</date>
  <expires-at>1906773886</expires-at>
</c>
```
If you want to handle multiple certificates at one time, you can express that as follows, for example.
```
<set>
  <c>
    <id>000-000-0001</id>
    <name>Benjamin B. Clark</name>
    <membership>Fujisawa Don Tacos</membership>
    <date>1559692800</date>
    <expires-at>1906773886</expires-at>
  </c>
  <c>
    <id>000-000-0002</id>
    <name>Bettina B. Cameron</name>
    <membership>Fujisawa Don Tacos</membership>
    <date>1559692800</date>
    <expires-at>1906773886</expires-at>
  </c>
</set>
```
The tag of the top-level element ('set' in the above) can be anything. So is the tag of the element that contains the content of the certificates ('c' in the above), which is irrelevant for proof. To get the cryptographic digest of the certificate (for proof), bbc1-lib-registry takes each element (```<id/>```, ```<name/>```, ```<membership/>```, ```<express-at/>``` of the above), calculate their SHA-256 digests, concatinate them all, and then calculate its SHA-256 digest. For best results, strip spaces including new lines before and after all first level elements within the certificates. See provided sample XML files.

There are tags that give special meanings to their text.

* **id** (any level) Number or string that identifies the certificate.

* **digest** (first level) SHA-256 digest of a hidden element (functionality of bbc1-lib-registry). Upon getting the cryprographic digest of the certificate, the text is considered as the hexadecimal representation of the digest of the element at the position.

* **date** (first level) Unix time, presented as a date string for the time zone in the default locale of the environment.

The following attributes have special meanings (functionality of bbc1-lib-registry).

* **container="true"** Recursively apply the above algorithm for  cryptographic digests to child elements.
* **sig** Digital signature. Needs to be accompanied by **pubkey**. If this attribute is present (typically at the top level element of a certificate), the cryptographic digest of the part is considered signed, the signature is verified, and the new digest is calculated over concatination of the digest, the public key, the 2-byte key-type code (see bbclib.KeyType) and the signature.
* **pubkey** Public key for verifying the signature.
* **algo** Digital signature algorithm in use. Currently supports ECDSA_SECP256k1 (ecdsa-secp256k1) and ECDSA_P256v1 (ecdsa-p256v1). ECDSA p256v1 is the default.

"sample-nested-s.xml" is a sample with the above attributes.

## How to use certificates.py
Below, it is assumed that bbc_core.py runs at the user's home directory, and Ethereum's ropsten testnet is used (and you have a sufficient amount of ETH (1 would be more than enough) in an account in ropsten). At first, bbc_core.py should be stopped.

1. Set up ledger subsystem (this writes to BBc-1 core's config file)

    ```
    eth_subsystem_tool.py -w ~/.bbc1 auto [infura.io project ID] [private key]
    ```

    Take note (make copy) of the displayed contract address that was deployed by the command above.

2. Start bbc_core.py

3. Create a domain.

    ```
    python certificates.py new_domain
    ```
    
    Take note (make a copy) of the displayed domain id.

4. Stop bbc_core.py (because again we will write to BBc-1 core's config file)

5. Configure Merkle tree settings of the ledger subsystem

    ```
    eth_subsystem_tool.py -w ~/.bbc1 -d [domain id] config_tree [number of certificates] [seconds]
    ```
    
    This configures the subsystem so that Merkle tree is closed and Merkle root is written to a Ethereum blockchain (ropsten by default) upon reaching either the specified number of processed certificates or the specified seconds.

6. Start bbc_core.py

7. Enable the ledger subsystem at BBc-1 core

    ```
    eth_subsystem_tool.py -w ~/.bbc1 -d [domain id] enable
    ```

8. Register certificates

    * Single certificate
    
        ```
        python certificates.py -w ~/.bbc1 -d [domain id] register [certificate XML file]
        ```
        
    * Multiple certificates in one file
    
        ```
        python certificates.py -w ~/.bbc1 -d [domain id] -m register [certificate XML file]
        ```

9. Verify certificates

    * Single certificate
    
        ```
        python certificates.py -w ~/.bbc1 -d [domain id] verify [certificate XML file]
        ```
        
    * Multiple certificates in one file
    
        ```
        python certificates.py -w ~/.bbc1 -d [domain id] -m verify [certificate XML file]
        ```

10. Generate verification query strings for certificates

    * Single certificate
    
        ```
        python certificates.py -w ~/.bbc1 -d [domain id] query [certificate XML file]
        ```
        
    * Multiple certificates in one file
    
        ```
        python certificates.py -w ~/.bbc1 -d [domain] -m query [certificate XML file]
        ```

## How to use cert_flask.py
This is a simple web service to verify a certificate using the query string generated using the **query** command of certificates.py The functionality is wrapped by index.py.

Before use, make sure that **S_CONTRACT_ADDRESS** and **S_NETWORK** in cert_flask.py is modified according to your environment.

```
export WEB3_INFURA_PROJECT_ID=[infura.io project ID]
python index.py
```
The web service runs on localhost:5000. Try ```localhost:5000/cert/?certificate=...&subtree=...``` to verify a certificate.

If you put the query string into a file, you can try ```localhost:5000/cert/upload``` to upload the file as a certificate to verify.

## How to use certificate_tool.py
This tool enables you to obtain the ```<digest/>``` for (part of) certificates for privacy control, and to generate key pairs and digitally sign your certificates. Try --help to see how exactly it can be used.


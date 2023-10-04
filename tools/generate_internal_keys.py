from OpenSSL import crypto, SSL
import os
import time
import getpass
from envsetup import *

target_product_out = os.environ.get("TARGET_PRODUCT_OUT")
host_build_type = os.environ.get("HOST_BUILD_TYPE")
target_device = os.environ.get("TARGET_DEVICE")
user = getpass.getuser()


def cert_gen(
    emailAddress="buildsystem@local.domain",
    commonName=f"{user}",
    countryName="US",
    localityName="Los Angeles",
    stateOrProvinceName="California",
    organizationName="LFS",
    organizationUnitName="Linux From Scratch",
    serialNumber=0,
    validityStartInSeconds=0,
    validityEndInSeconds=10 * 365 * 24 * 60 * 60,
    KEY_FILE=f"{target_product_out}/obj/ETC/signing/build.key",
    CERT_FILE=f"{target_product_out}/obj/ETC/signing/{target_device}/cert_{host_build_type}_cert.key",
):
    # can look at generated file using openssl:
    # openssl x509 -inform pem -in selfsigned.crt -noout -text
    # create a key pair
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 4096)
    # create a self-signed cert
    cert = crypto.X509()
    cert.get_subject().C = countryName
    cert.get_subject().ST = stateOrProvinceName
    cert.get_subject().L = localityName
    cert.get_subject().O = organizationName
    cert.get_subject().OU = organizationUnitName
    cert.get_subject().CN = commonName
    cert.get_subject().emailAddress = emailAddress
    cert.set_serial_number(serialNumber)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(validityEndInSeconds)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, "sha512")
    os.makedirs(f"{target_product_out}/obj/ETC/signing/{target_device}", exist_ok=True)
    time.sleep(0.1)
    print("//internal_keys_gen:generating internal keys...", end="\r")
    with open(CERT_FILE, "wt") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode("utf-8"))
    with open(KEY_FILE, "wt") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k).decode("utf-8"))


cert_gen()

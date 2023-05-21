# 来自 Aegis 仓库里的脚本
# pip install cryptography

import base64
import io
import json
import sys

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.backends import default_backend
import cryptography

backend = default_backend()


def die(msg, code=1):
    print(msg, file=sys.stderr)
    exit(code)


def decrypt(data, password):
    # parse the Aegis vault file
    # with io.open(datafile, "r") as f:
    #     data = json.load(f)
    data = json.loads(data)
    # ask the user for a password
    password = password.encode("utf-8")

    # extract all password slots from the header
    header = data["header"]
    slots = [slot for slot in header["slots"] if slot["type"] == 1]

    # try the given password on every slot until one succeeds
    master_key = None
    for slot in slots:
        # derive a key from the given password
        kdf = Scrypt(
            salt=bytes.fromhex(slot["salt"]),
            length=32,
            n=slot["n"],
            r=slot["r"],
            p=slot["p"],
            backend=backend,
        )
        key = kdf.derive(password)

        # try to use the derived key to decrypt the master key
        cipher = AESGCM(key)
        params = slot["key_params"]
        try:
            master_key = cipher.decrypt(
                nonce=bytes.fromhex(params["nonce"]),
                data=bytes.fromhex(slot["key"]) + bytes.fromhex(params["tag"]),
                associated_data=None,
            )
            break
        except cryptography.exceptions.InvalidTag:
            pass

    if master_key is None:
        die("error: unable to decrypt the master key with the given password")

    # decode the base64 vault contents
    content = base64.b64decode(data["db"])

    # decrypt the vault contents using the master key
    params = header["params"]
    cipher = AESGCM(master_key)
    db = cipher.decrypt(
        nonce=bytes.fromhex(params["nonce"]),
        data=content + bytes.fromhex(params["tag"]),
        associated_data=None,
    )

    db = db.decode("utf-8")

    return db

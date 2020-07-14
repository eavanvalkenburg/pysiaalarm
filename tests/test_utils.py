"""Utils for testing pysiaalarm."""
from binascii import hexlify, unhexlify

from Crypto import Random
from Crypto.Cipher import AES


def create_test_items(key, content):
    """Create encrypted content."""
    encrypter = AES.new(
        key.encode("utf-8"), AES.MODE_CBC, unhexlify("00000000000000000000000000000000")
    )

    extra = len(content) % 16
    unencrypted = (16 - extra) * "0" + content
    return (
        hexlify(encrypter.encrypt(unencrypted.encode("utf-8")))
        .decode(encoding="utf-8")
        .upper()
    )

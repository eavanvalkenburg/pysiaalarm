"""Utils for testing pysiaalarm."""
from binascii import hexlify

from Crypto import Random
from Crypto.Cipher import AES


def create_test_items(key, content):
    """Create encrypted content."""
    encrypter = AES.new(
        key.encode("utf8"), AES.MODE_CBC, Random.new().read(AES.block_size)
    )

    extra = len(content) % 16
    unencrypted = (16 - extra) * "0" + content
    return (
        hexlify(encrypter.encrypt(unencrypted.encode("utf8")))
        .decode(encoding="UTF-8")
        .upper()
    )

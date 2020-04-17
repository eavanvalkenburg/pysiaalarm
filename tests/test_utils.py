"""Utils for testing pysia."""
from binascii import hexlify
from Crypto import Random
from Crypto.Cipher import AES


def create_test_items(key, content):
    """Create encrypted content."""
    # left in decryption methods for future reference.
    # decrypter = AES.new(
    #     key, AES.MODE_CBC, unhexlify("00000000000000000000000000000000")
    # )
    encrypter = AES.new(key, AES.MODE_CBC, Random.new().read(AES.block_size))

    extra = len(content) % 16
    unencrypted = (16 - extra) * "0" + content
    # encrypted = hexlify(encrypter.encrypt(unencrypted)).decode(encoding="UTF-8").upper()
    # decrypted = decrypter.decrypt(unhexlify(encrypted)).decode(encoding="UTF-8", errors="replace")
    return hexlify(encrypter.encrypt(unencrypted)).decode(encoding="UTF-8").upper()

"""This is the class for the Osborne-Hoffman encryption scheme."""
from Crypto.Cipher import DES3
from Crypto.Random import get_random_bytes


class OsborneHoffman():
    """Class for Osborn-Hoffman encryption."""

    _key: bytes = None
    _cipher: DES3 = None

    def __init__(
        self,
    ):
        self._key = DES3.adjust_key_parity(get_random_bytes(24))
        self._cipher = DES3.new(self._key, mode=DES3.MODE_ECB)

    def encrypt_data(
        self,
        data: bytes,
    ):
        block_size = 8
        padding_len = block_size-len(data)%block_size
        padding = bytearray(chr(0)*(padding_len), 'ascii')
        data += padding
        data = self._cipher.encrypt(data)
        return data

    def decrypt_data(
        self,
        data: bytes,
    ):
        data = self._cipher.decrypt(data)
        padding_len = len(data)-data.rfind(b'\r') - 1
        data = data[:-padding_len]
        return data

    def get_scrambled_key(self):
        key = bytearray(self._key)
        key[3] ^= 0x05
        key[4] ^= 0x23
        key[9] ^= 0x29
        key[1] ^= 0x2D
        key[6] ^= 0x39
        key[20] ^= 0x44
        key[8] ^= 0x45
        key[16] ^= 0x45
        key[5] ^= 0x49
        key[18] ^= 0x50
        key[23] ^= 0x54
        key[0] ^= 0x55
        key[22] ^= 0x69
        key[2] ^= 0x6A
        key[15] ^= 0x88
        key[19] ^= 0x8A
        key[12] ^= 0x94
        key[17] ^= 0xA3
        key[7] ^= 0xA8
        key[21] ^= 0xAA
        key[14] ^= 0xB5
        key[13] ^= 0xC2
        key[10] ^= 0xD3
        key[11] ^= 0xE9
        return key

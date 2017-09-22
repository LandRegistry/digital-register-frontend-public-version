from Crypto.Cipher import AES
import base64
import config

# Code based on snippet found here: https://gist.github.com/sekondus/4322469

# the block size for the cipher object; must be 16, 24, or 32 for AES
BLOCK_SIZE = 32

# the character used for padding--with a block cipher such as AES, the value
# you encrypt must be a multiple of BLOCK_SIZE in length.  This character is
# used to ensure that your value is always a multiple of BLOCK_SIZE
PADDING = '{'


def pad(s):
    """one-liner to sufficiently pad the text to be encrypted"""
    return s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING


def encode_aes(cipher, string):
    unencrypted_string = pad(string).encode('utf8')
    encrypted_string = cipher.encrypt(unencrypted_string)
    return base64.urlsafe_b64encode(encrypted_string)


def decode_aes(cipher, encoded_string):
    try:
        encrypted_str = base64.urlsafe_b64decode(encoded_string)
        decrypted_string = cipher.decrypt(encrypted_str)
        return decrypted_string.decode('utf8').rstrip(PADDING)
    except Exception:
        return None


def encrypt(data):
    return str(encode_aes(AES.new(pad(config.CONFIG_DICT['SECRET_KEY'])), data), 'utf-8')


def decrypt(data):
    return decode_aes(AES.new(pad(config.CONFIG_DICT['SECRET_KEY'])), data)

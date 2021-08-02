import hashlib

# hash funcs expect bytes as inputs
# this turns a string to bytes through encode()
input_bytes = b"backpack "

output = hashlib.sha256(input_bytes)
# we can turn bytes to hex, more readable and shorter
print(output.hexdigest())

hashlib.sha3_256
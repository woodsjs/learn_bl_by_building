import nacl.encoding
import nacl.signing

#signing a message - note this is NOT encrypting the message

#generate new keypair for bob
bobs_sk = nacl.signing.SigningKey.generate()
bobs_PK = bobs_sk.verify_key

print('Bobs private verify key ', bobs_sk.verify_key)

# it's in bytes, so serialize it to make it readable
bobs_PK_hex = bobs_PK.encode(encoder=nacl.encoding.HexEncoder)
fake_bobs_PK_hex = b'a6c79939106476087b68f6c695a03cc0cd4efe31d08c18de59bfd489b73464ff'

print('bobs public key in hex ', bobs_PK_hex)

# and sign a message
signed = bobs_sk.sign(b"Send $37 to alice")

print('signed message ', signed)

print('Lets verify the key')

# this verifies the message was sent by bob
verify_key = nacl.signing.VerifyKey(bobs_PK_hex, encoder=nacl.encoding.HexEncoder)
fake_verify_key = nacl.signing.VerifyKey(fake_bobs_PK_hex, encoder=nacl.encoding.HexEncoder)

print('verify key ', verify_key)
print('fake verify key ', fake_verify_key)

# now verify the message
try:
    is_verified = verify_key.verify(signed)
except nacl.signing.exc.BadSignatureError:
    print('Forgery!') 
else:
    print('Success!')
    print('Verified message: ', is_verified)

try:
     is_verified = fake_verify_key.verify(signed)
except nacl.signing.exc.BadSignatureError:
    print('Forgery!') 
    print('result is ', is_verified)
else:
    print('Success!')


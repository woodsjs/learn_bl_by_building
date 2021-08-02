from hashlib import sha256

file = open("image.jpg", "rb")
hash = sha256(file.read()).hexdigest()
file.close()

print(f"the has of the file is: {hash}")
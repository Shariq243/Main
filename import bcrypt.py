import bcrypt
plain_password = "admin123"
hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt())
print(hashed_password)
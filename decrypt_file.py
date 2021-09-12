from cryptography.fernet import Fernet
import sys

if len(sys.argv) != 3:
    print('Неправильное количество аргументов')
    sys.exit(1)

with open(sys.argv[1], 'rb+') as inf:
    crypt_data = inf.read()

key = sys.argv[2]
cipher = Fernet(key)
decrypt_data = cipher.decrypt(crypt_data)
with open(sys.argv[1] + '_decryp', 'wb+') as outf:
    outf.write(decrypt_data)


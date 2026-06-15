def encrypt(in_path, out_path, key):
    key &= 0xFF
    with open(in_path, 'rb') as file:
        data = file.read()

    result = bytearray()
    for b in data:
        shifted = (b << 2) | (b >> 6)
        shifted_8bit = shifted & 0xFF
        enc_byte = shifted_8bit ^ key
        result.append(enc_byte)

    with open(out_path, 'wb') as file:
        file.write(result)


def decrypt(in_path, out_path, key):
    key &= 0xFF
    with open(in_path, 'rb') as file:
        data = file.read()

    result = bytearray()
    for b in data:
        xored = b ^ key
        shifted = (xored << 6) | (xored >> 2)
        dec_byte = shifted & 0xFF
        result.append(dec_byte)

    with open(out_path, 'wb') as f:
        f.write(result)


test_bytes = bytes([10, 20, 30, 40, 50, 100, 200, 255])
with open('resource/original.bin', 'wb') as file:
    file.write(test_bytes)

encrypt('resource/original.bin', 'resource/encrypted.bin', 42)
decrypt('resource/encrypted.bin', 'resource/decrypted.bin', 42)

with open('resource/original.bin', 'rb') as file_1:
    orig = file_1.read()
with open('resource/decrypted.bin', 'rb') as file_2:
    dec = file_2.read()

if orig == dec:
    print('Проверка пройдена успешно')
else:
    print('Ошибка: файлы не совпадают!')
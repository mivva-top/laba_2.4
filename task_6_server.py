import socket
import json

SERVER_KEY = 123

def encrypt_data(input_bytes, key):
    key = key & 0xFF
    result = bytearray()
    for byte_value in input_bytes:
        shifted = (byte_value << 2) | (byte_value >> 6)
        shifted_8bit = shifted & 0xFF
        encrypted_byte = shifted_8bit ^ key
        result.append(encrypted_byte)
    return bytes(result)

def validate_json(text):
    json.loads(text)
    return text.encode("utf-8")

def validate_xml(text):
    text = text.strip()
    if not text.startswith("<") or not text.endswith(">"):
        raise ValueError("Неверный формат XML")
    return text.encode("utf-8")

def save_encrypted_file(original_name, encrypted_bytes):
    binary_name = original_name.rsplit(".", 1)[0] + ".bin"
    with open(binary_name, "wb") as file:
        file.write(encrypted_bytes)
    return binary_name

def load_encrypted_file(binary_name):
    with open(binary_name, "rb") as file:
        return file.read()

def receive_line(connection):
    buffer = b""
    while b"\n" not in buffer:
        chunk = connection.recv(4096)
        if not chunk:
            break
        buffer += chunk
    return buffer.decode("utf-8").strip()

def receive_exact(connection, size):
    buffer = b""
    while len(buffer) < size:
        chunk = connection.recv(min(4096, size - len(buffer)))
        if not chunk:
            break
        buffer += chunk
    return buffer

def send_response(connection, response_dict):
    connection.sendall(json.dumps(response_dict).encode("utf-8") + b"\n")

def handle_client_connection(connection):
    try:
        header_line = receive_line(connection)
        if not header_line:
            return
        command = json.loads(header_line)

        if command.get("action") == "upload":
            file_size = int(command.get("size", 0))
            raw_data = receive_exact(connection, file_size)
            file_extension = command["filename"].rsplit(".", 1)[-1].lower()
            try:
                if file_extension == "json":
                    validated_bytes = validate_json(raw_data.decode("utf-8"))
                elif file_extension == "xml":
                    validated_bytes = validate_xml(raw_data.decode("utf-8"))
                else:
                    raise ValueError("Разрешены только форматы json и xml")
                encrypted_bytes = encrypt_data(validated_bytes, SERVER_KEY)
                saved_filename = save_encrypted_file(command["filename"], encrypted_bytes)
                send_response(connection, {"status": "success", "saved_as": saved_filename})
            except Exception as error:
                send_response(connection, {"status": "error", "message": str(error)})

        elif command.get("action") == "download":
            requested_name = command["filename"]
            if not requested_name.endswith(".bin"):
                requested_name = requested_name.rsplit(".", 1)[0] + ".bin"
            try:
                file_data = load_encrypted_file(requested_name)
                send_response(connection, {"status": "success", "size": len(file_data)})
                connection.sendall(file_data)
            except Exception as error:
                send_response(connection, {"status": "error", "message": str(error)})
        else:
            send_response(connection, {"status": "error", "message": "Неизвестная команда"})
    except Exception as error:
        send_response(connection, {"status": "error", "message": str(error)})
    finally:
        connection.close()

def run_server(host="127.0.0.1", port=9999):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print("Сервер запущен на " + host + ":" + str(port))
    try:
        while True:
            connection, address = server_socket.accept()
            print("Подключение от " + str(address))
            handle_client_connection(connection)
    except KeyboardInterrupt:
        print("Сервер остановлен")
    finally:
        server_socket.close()

run_server()
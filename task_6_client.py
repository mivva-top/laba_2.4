import socket
import json

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

def upload_file(file_path, host="127.0.0.1", port=9999):
    file_extension = file_path.rsplit(".", 1)[-1].lower()
    if file_extension not in ("json", "xml"):
        return {"status": "error", "message": "Клиент поддерживает только json и xml"}

    with open(file_path, "rb") as file:
        file_data = file.read()

    command = {
        "action": "upload",
        "filename": file_path.replace("\\", "/").split("/")[-1],
        "size": len(file_data)
    }
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        client_socket.sendall(json.dumps(command).encode("utf-8") + b"\n")
        client_socket.sendall(file_data)
        response = json.loads(receive_line(client_socket))
        client_socket.close()
        return response
    except Exception as error:
        return {"status": "error", "message": str(error)}

def download_file(remote_filename, local_path, host="127.0.0.1", port=9999):
    command = {"action": "download", "filename": remote_filename}
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        client_socket.sendall(json.dumps(command).encode("utf-8") + b"\n")

        header = json.loads(receive_line(client_socket))
        if header.get("status") != "success":
            client_socket.close()
            return header

        file_data = receive_exact(client_socket, header["size"])
        with open(local_path, "wb") as file:
            file.write(file_data)
        client_socket.close()
        return {"status": "success", "saved_to": local_path}
    except Exception as error:
        return {"status": "error", "message": str(error)}

def run_client():
    print("Тест загрузки файла")
    test_file = "resource/sample.json"
    with open(test_file, "w") as file:
        json.dump({
  "user": {
    "id": 101,
    "username": "dev_user",
    "email": "dev@example.com"
  },
  "active": True,
  "roles": ["user", "editor"]
}, file)

    upload_response = upload_file(test_file)
    print("Ответ сервера: " + str(upload_response))

    print("Тест скачивания файла")
    if upload_response.get("status") == "success":
        binary_file = upload_response["saved_as"]
        download_response = download_file(binary_file, "received_" + binary_file)
        print("Ответ сервера: " + str(download_response))

run_client()
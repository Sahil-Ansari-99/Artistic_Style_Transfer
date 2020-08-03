import socket
import threading
import io
import base64
import os
import psutil
from StyleTransfer import NST
from PIL import Image


class Server:
    def __init__(self):
        self.clients = []
        self.HEADER = 64
        self.PORT = 8080
        self.SERVER = socket.gethostbyname(socket.gethostname())
        self.ADDR = (self.SERVER, self.PORT)
        self.FORMAT = 'utf-8'
        self.DISCONNECT_MESSAGE = '!DISCONNECT'
        self.PIC_FORMAT = '$P!C'
        self.STYLE_FORMAT = '$STYLE'
        self.CONTENT_FORMAT = '$CONTENT'
        self.START = '$START'
        self.RESULT_FORMAT = '$RES'
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(self.ADDR)
        self.connected_clients = []

    def start(self):
        self.server.listen()
        print('LISTENING ON: ', self.SERVER)
        while True:
            try:
                conn, addr = self.server.accept()
                port_num = str(addr[1])
                thread = threading.Thread(target=self.handle_client, args=(conn, port_num))
                thread.start()
                print("Connections ", threading.activeCount() - 1)
            except KeyboardInterrupt:
                print("Keyboard Interrupt")
                self.close()
                exit(0)

    def handle_client(self, conn, addr):
        self.connected_clients.append(addr)
        connected = True
        obj = NST()
        obj.set_client_port(addr)
        while connected:
            msg_length = conn.recv(self.HEADER).decode(self.FORMAT)
            if msg_length:
                msg_length = int(msg_length)
                msg = conn.recv(msg_length).decode(self.FORMAT)
                if msg == self.DISCONNECT_MESSAGE:
                    connected = False
                print(addr, msg)
                ret = self.handle_message(msg, addr, obj).encode(self.FORMAT)
                ret_len = len(ret)
                send_length = str(ret_len).encode(self.FORMAT)
                send_length += b' ' * (self.HEADER - len(send_length))
                conn.send(send_length)
                conn.send(ret)
        self.delete_client_files(addr)
        self.connected_clients.remove(addr)
        conn.close()

    def handle_message(self, msg, addr, obj):
        self.memory_usage()
        if msg.startswith(self.PIC_FORMAT):
            self.process_image(msg, self.PIC_FORMAT, f'received_{addr}.jpg')
        if msg.startswith(self.STYLE_FORMAT):
            save_name = 'style_'+addr+'.jpg'
            self.process_image(msg, self.STYLE_FORMAT, save_name)
            obj.set_style_img(save_name)
        if msg.startswith(self.CONTENT_FORMAT):
            save_name = 'content_' + addr + '.jpg'
            self.process_image(msg, self.CONTENT_FORMAT, save_name)
            obj.set_content_img(save_name)
        if msg == self.START:
            res = obj.start_style_transfer()
            if res:
                print('sending result')
                return self.encode_image(addr)
            else:
                return 'Error'
        return 'RECEIVED'

    def process_image(self, pic, form, save_name):
        pic_ = pic[len(form)+1:]
        pic_bytes = io.BytesIO(base64.b64decode(pic_))
        img = Image.open(pic_bytes)
        img.save(save_name)

    def encode_image(self, addr):
        file_name = f'res_{addr}.jpg'
        pic_file = open(file_name, 'rb')
        bytes = pic_file.read()
        pic_size = len(bytes)
        pic_base64 = str(base64.b64encode(bytes))
        pic_base64 = self.RESULT_FORMAT + pic_base64
        return pic_base64

    def delete_client_files(self, addr):
        print('deleting')
        style_path = f'style_{addr}.jpg'
        content_path = f'content_{addr}.jpg'
        res_path = f'res_{addr}.jpg'
        if os.path.isfile(style_path):
            os.remove(style_path, dir_fd=None)
        if os.path.isfile(content_path):
            os.remove(content_path, dir_fd=None)
        if os.path.isfile(res_path):
            os.remove(res_path, dir_fd=None)

    def memory_usage(self):
        process = psutil.Process(os.getpid())
        mem = process.memory_info()[0] / float(2 ** 20)
        print('Server Memory usage:', mem, 'MB')

    def close(self):
        self.server.shutdown(socket.SHUT_RDWR)
        self.server.close()


if __name__ == '__main__':
    server = Server()
    server.start()

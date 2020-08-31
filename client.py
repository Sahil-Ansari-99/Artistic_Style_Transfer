import socket
import base64
from PIL import Image
import io


class Client:
    def __init__(self):
        self.HEADER = 64
        self.PORT = 8080
        self.FORMAT = 'utf-8'
        self.DISCONNECT_MESSAGE = '!DISCONNECT'
        self.SERVER = '192.168.1.6'
        self.STYLE_FORMAT = '$STYLE'
        self.CONTENT_FORMAT = '$CONTENT'
        self.START = '$START'
        self.RESULT_FORMAT = '$RES'
        self.ADDR = (self.SERVER, self.PORT)
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect(self.ADDR)

    def start(self):
        connected = True
        while connected:
            msg = input('Enter message: ')
            if msg == self.DISCONNECT_MESSAGE:
                connected = False
                self.send(msg)
            elif msg == 'style':
                self.send_pic('starry_night.jpg', self.STYLE_FORMAT)
            elif msg == 'content':
                self.send_pic('eiffel_tower.jpg', self.CONTENT_FORMAT)
            elif msg == 'start':
                self.send(self.START)
            else:
                print('Sending default')
                self.send(msg)

    def send(self, msg):
        message = msg.encode(self.FORMAT)
        msg_length = len(msg)
        send_length = str(msg_length).encode(self.FORMAT)
        send_length += b' ' * (self.HEADER - len(send_length))
        print('Send Length:', send_length, len(send_length))
        print(message)
        self.client.send(send_length)
        self.client.send(message)
        return_msg_len = self.client.recv(self.HEADER).decode(self.FORMAT)
        if return_msg_len:
            return_msg_len = int(return_msg_len)
            # return_msg = self.client.recv(return_msg_len).decode(self.FORMAT)
            return_msg = self.receive_all_data(return_msg_len, self.client)
            if return_msg.startswith(self.RESULT_FORMAT):
                print(return_msg)
                self.process_image(return_msg)
            print(return_msg)

    def receive_all_data(self, msg_length, conn):
        msg = ''
        while len(msg) < msg_length:
            part = conn.recv(msg_length).decode(self.FORMAT)
            print('Part length:', len(part))
            msg += part
        print('Received all data...')
        return msg

    def send_pic(self, name, img_type):
        pic_file = open(name, 'rb')
        bytes = pic_file.read()
        pic_size = len(bytes)
        pic_base64 = base64.b64encode(bytes)
        pic_base64 = str(pic_base64)
        pic_base64 = img_type + pic_base64
        self.send(pic_base64)

    def process_image(self, pic):
        pic_ = pic[len(self.RESULT_FORMAT)+1:]
        if len(pic_) % 4 != 0:
            pic_ += '==='
        pic_bytes = io.BytesIO(base64.b64decode(pic_))
        img = Image.open(pic_bytes)
        img.save('received_res.jpg')

if __name__ == '__main__':
    client = Client()
    client.start()

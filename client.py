import socket
import threading
import time
import json
import random
import websocket

from tcn import tcn_encode

# --------------------------
# Client Code
# --------------------------
class Client:
    def __init__(self, username, phpsessid, host='localhost', port=12345, partner=None, board_num=0):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.username = username
        self.phpsessid = phpsessid
        self.partner = partner
        self.board_num = board_num
        self.clientId = ''
        self.ply = 0
        self.gid = -1
        self.side = -1
        self.id = 1
        self.ack = 1
        self.ping = random.randint(23,49)
        self.playing = False
        self.ws = None

    def start(self):
        try:
            self.client_socket.connect((self.host, self.port))
            print(f"[CLIENT {self.id}] Connected to server {self.host}:{self.port}")
        except ConnectionRefusedError:
            print(f"[CLIENT {self.id}] Connection refused by the server")
            return

        # Start a thread to listen for messages from the server
        listener_thread = threading.Thread(target=self.listen_server, daemon=True)
        listener_thread.start()

        self.ws = websocket.WebSocket()  # Initialize WebSocket as an instance variable
        self.ws.connect('wss://live2.chess.com/cometd', cookie=f'PHPSESSID={self.phpsessid}')

        data = [
            {
                'version': '1.0',
                'minimumVersion': '1.0',
                'channel': '/meta/handshake',
                'supportedConnectionTypes': ['ssl-websocket'],
                'advice': {'timeout': 60000, 'interval': 0},
                'clientFeatures': {
                    'protocolversion': '2.1',
                    'clientname': 'LC6;chrome/121.0.6167/browser;Windows 10;jxk3sm4;78.0.2',
                    'skiphandshakeratings': True,
                    'adminservice': True,
                    'announceservice': True,
                    'arenas': True,
                    'chessgroups': True,
                    'clientstate': True,
                    'events': True,
                    'gameobserve': True,
                    'genericchatsupport': True,
                    'genericgamesupport': True,
                    'guessthemove': True,
                    'multiplegames': True,
                    'multiplegamesobserve': True,
                    'offlinechallenges': True,
                    'pingservice': True,
                    'playbughouse': True,
                    'playchess': True,
                    'playchess960': True,
                    'playcrazyhouse': True,
                    'playkingofthehill': True,
                    'playoddschess': True,
                    'playthreecheck': True,
                    'privatechats': True,
                    'stillthere': True,
                    'teammatches': True,
                    'tournaments': True,
                    'userservice': True},
                'serviceChannels': ['/service/user'],
                'ext': {
                    'ack': True,
                    'timesync': {'tc': int(time.time() * 1000), 'l': self.ping, 'o': 0}
                },
                'id': self.id,
                'clientId': None
            }
        ]
        self.ws.send(json.dumps(data))
        self.id += 1

        # Start WebSocket message loop in a thread
        ws_thread = threading.Thread(target=self.main_loop)
        ws_thread.start()
        ws_thread.join()

    def main_loop(self) -> None:
        while True:
            message = json.loads(self.ws.recv())[0]
            #print(message)

            if 'clientId' in message and not self.clientId:
                self.clientId = message['clientId']
                self.send_partnership()

            if 'data' in message and 'tid' in message['data'] and message['data'][
                'tid'] == 'RequestBughousePair' and 'from' in message['data']:
                self.send_partnership()

            if 'data' in message and 'tid' in message['data'] and message['data']['tid'] == 'BughousePair':
                if self.board_num == 0:
                    self.seek_game()

            if 'data' in message and 'message' in message['data']:
                if 'from' in message['data']['message']:
                    print(message['data']['message']['from']["uid"] + ": " + message['data']['message']['txt'])
                #if str(self.gid) in message['data']['message']['id']:
                #    self.send_message(f"chat {message['data']['message']['txt']}\n")

            # Send heartbeat back to server
            if (message['channel'] == '/meta/connect' or message['channel'] == '/meta/handshake') and message['successful']:
                if message['channel'] == '/meta/connect':
                    self.ack = message['ext']['ack']
                data = [{'channel': '/meta/connect', 'connectionType': 'ssl-websocket',
                         'ext': {'ack': self.ack, 'timesync': {'tc': int(time.time() * 1000), 'l': self.ping, 'o': 0}},
                         'id': self.id, 'clientId': self.clientId}]
                self.ws.send(json.dumps(data))
                self.id += 1

            # Handle game logic
            if 'data' in message and 'game' in message['data'] and 'status' in message['data']['game']:
                if message['data']['game']['status'] == 'finished':
                    if self.playing:
                        self.playing = False
                        time.sleep(1)
                        if self.board_num == 0:
                            self.seek_game()
                        self.send_message("chat :bughouse-ns\n")

                else:
                    if message['data']['game']['status'] == 'starting':
                        self.playing = True

                    players = message['data']['game']['players']
                    user_index = -1
                    for i in range(len(players)):
                        if players[i]['uid'].lower() == self.username.lower():
                            user_index = i
                            break

                    if user_index != -1:
                        tcn_moves = message['data']['game']['moves']
                        times = message['data']['game']['clocks']
                        self.gid = message['data']['game']['id']
                        self.ply = message['data']['game']['seq']
                        self.side = user_index

                        if self.board_num == 0:
                            self.send_message(f"side {self.side}\n")

                        self.send_message(f"times {self.board_num} {times[0]} {times[1]}\nmoves {self.board_num} {tcn_moves}\n")
                    else:
                        tcn_moves = message['data']['game']['moves']
                        times = message['data']['game']['clocks']
                        self.send_message(
                            f"times {1 - self.board_num} {times[0]} {times[1]}\nmoves {1 - self.board_num} {tcn_moves}\n")

    def listen_server(self):
        while True:
            try:
                data = self.client_socket.recv(1024)
                if not data:
                    break
                move = data.decode()
                self.send_move(move)
            except ConnectionResetError:
                break

    def send_message(self, message):
        try:
            self.client_socket.sendall(message.encode())
        except BrokenPipeError:
            print(f"[CLIENT {self.id}] Cannot send message, connection broken.")

    def send_partnership(self) -> None:
        if not self.partner:
            return

        data = [
            {
                'channel': '/service/game',
                'data': {
                    'tid': 'RequestBughousePair',
                    'to': self.partner,
                    'from': self.username,
                },
                'id': self.id,
                'clientId': self.clientId,
            },
        ]
        self.ws.send(json.dumps(data))
        self.id += 1

    def seek_game(self) -> None:
        data = [
            {
                'channel': '/service/game',
                'data': {
                    'tid': 'Challenge',
                    'uuid': '',
                    'to': None,
                    'from': self.username,
                    'gametype': 'bughouse',
                    'initpos': None,
                    'rated': True,
                    'minrating': None,
                    'maxrating': None,
                    'basetime': 1800,
                    'timeinc': 0
                },
                'id': self.id,
                'clientId': self.clientId,
            },
        ]
        self.ws.send(json.dumps(data))
        self.id += 1

    def send_move(self, move: str) -> None:
        data = [
            {
                'channel': '/service/game',
                'data': {
                    'move': {
                        'gid': self.gid,
                        'move': tcn_encode([move]),
                        'seq': self.ply,
                        'uid': self.username,
                    },
                    'tid': 'Move',
                },
                'id': self.id,
                'clientId': self.clientId,
            },
        ]
        self.ws.send(json.dumps(data))
        self.id += 1

    def seek_rematch(self) -> None:
        # Compute color based on the user's side
        color = 2 if self.side else 1

        data = [
            {
                'channel': '/service/game',
                'data': {
                    'tid': 'Challenge',
                    'uuid': '',
                    'to': self.opponent,
                    'from': self.username,
                    'gametype': 'bughouse',
                    'initpos': None,
                    'rated': True,
                    'minrating': None,
                    'maxrating': None,
                    'rematchgid': self.game_id,
                    'color': color,
                    'basetime': time,
                    'timeinc': 0
                },
                'id': self.id,
                'clientId': self.clientId,
            }
        ]

        self.ws.send(json.dumps(data))
        self.id += 1
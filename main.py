import threading
import time
import configparser

from server import Server
from client import Client

NUM_CLIENTS = 2  # Number of clients to start

# --------------------------
# Main Code: Start server and multiple clients
# --------------------------
def main():
    # Start the server
    server = Server(host='localhost', port=12345)
    server.start()

    # Give the server a moment to start up
    time.sleep(1)

    # Start multiple client threads
    config = configparser.ConfigParser()
    config.read('config.ini')
    client_threads = []
    for i in range(NUM_CLIENTS):
        client = Client(host='localhost', port=12345, username=config.get('credentials', f'username{i+1}'),  phpsessid=config.get('credentials', f'phpsessid{i+1}'), partner=config.get('credentials', f'username{[2, 1][i]}'), board_num=i)
        t = threading.Thread(target=client.start, daemon=True)
        client_threads.append(t)
        t.start()

    # Wait for all client threads to complete
    for t in client_threads:
        t.join()

    print("[MAIN] All clients have disconnected. Server still running (press Ctrl+C to stop).")

if __name__ == '__main__':
    main()

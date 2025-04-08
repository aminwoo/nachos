import chess
import socket
import concurrent.futures
import threading
import random
import pickle
from threading import Lock

from board import BughouseBoard
from engine import Engine, parse_moves

engine = Engine("./hivemind")

def clean_fen(extended_fen):
    # Split the FEN string by whitespace into its components.
    parts = extended_fen.split()

    # Expecting at least 4 parts: board, active color, castling, en passant.
    if len(parts) < 4:
        raise ValueError("FEN string does not contain enough fields.")

    board_field = parts[0]
    active_color = parts[1]
    castling = parts[2]
    en_passant = parts[3]

    # Remove any piece drop extension from the board field if present.
    if '[' in board_field:
        board_field = board_field.split('[')[0]

    # Reconstruct the FEN without the halfmove clock and fullmove number.
    clean = f"{board_field} {active_color} {castling} {en_passant}"
    return clean

def biased_random_number(min_val, max_val, exponent=2):
    """
    Generate a random number between min_val and max_val (inclusive) biased toward min_val.

    Parameters:
        min_val (int): The minimum value.
        max_val (int): The maximum value.
        exponent (float): The exponent used to bias the result.
                          Values >1 skew toward min_val, values <1 skew toward max_val.

    Returns:
        int: A biased random number between min_val and max_val.
    """
    # Generate a uniform random number in [0, 1]
    u = random.random()
    # Transform u to bias the distribution toward 0 (min_val when scaled)
    biased_u = u ** exponent
    # Scale biased_u to the range [min_val, max_val]
    return min_val + int(biased_u * (max_val - min_val))

def compute_thinking_time(q, min_time, max_time, exponent=1, random_range=200):
    # Linear mapping: when |q|=0, time=700; when |q|=1, time=1500
    time = min_time + (max_time - min_time) * (abs(q) ** exponent)

    random_offset = random.uniform(-random_range, random_range)
    time += random_offset
    # Clamp the time so it stays within the desired boundaries.
    time = max(min(time, max_time), min_time)
    return time

def save_book(book):
    with open('book.pkl', 'wb') as f:
        pickle.dump(book, f)

def sort_hand(hand):
    return ''.join(sorted(hand))

from enum import Enum


class GamePhase(Enum):
    OPENING = "opening phase"
    MIDDLE = "middle game"
    SCRAMBLE = "scramble phase"


def get_phase(times, upper_threshold=1700, lower_threshold=100):
    """
    Determine the current phase of the game based on time values.

    Args:
        times: A 2D array of time values like [[1800, 1800], [1800, 1800]]

    Returns:
        GamePhase: The current phase enum (OPENING, MIDDLE, or SCRAMBLE)
        :param times:
        :param lower_threshold:
        :param upper_threshold:
    """
    # Flatten the 2D array
    flat_times = [time for player_times in times for time in player_times]

    # Check for opening phase (any time above upper threshold)
    if any(time >= upper_threshold for time in flat_times):
        return GamePhase.OPENING

    # Check for scramble phase (any time below lower threshold)
    if any(time <= lower_threshold for time in flat_times):
        return GamePhase.SCRAMBLE

    # Default to middle game
    return GamePhase.MIDDLE


def get_time_bounds(phase):
    """
    Get the min and max thinking time bounds based on game phase.

    Args:
        phase: GamePhase enum value

    Returns:
        tuple: (min_time, max_time) in milliseconds
    """
    if phase == GamePhase.OPENING:
        return 300, 800  # Fairly quick in opening
    elif phase == GamePhase.MIDDLE:
        return 1200, 2000  # Slower in middle game
    elif phase == GamePhase.SCRAMBLE:
        return 50, 200  # Super fast in scramble
    else:
        return 500, 1000  # Default fallback


def compute_thinking_time(q, phase, exponent=1, random_range=500):
    """
    Compute thinking time based on evaluation score and game phase.

    Args:
        q: Evaluation score (-1 to 1)
        phase: GamePhase enum value
        exponent: Exponent to apply to abs(q) for non-linear scaling
        random_range: Range for random variation

    Returns:
        float: Thinking time in milliseconds
    """
    # Get min and max time based on phase
    min_time, max_time = get_time_bounds(phase)

    # Linear mapping between min_time and max_time based on abs(q)
    time = min_time + (max_time - min_time) * (abs(q) ** exponent)

    # Add randomness for more natural behavior
    # Scale random range based on phase - less randomness in scramble
    if phase == GamePhase.SCRAMBLE:
        adjusted_random_range = random_range / 2
    else:
        adjusted_random_range = random_range

    random_offset = random.uniform(-adjusted_random_range, adjusted_random_range)
    time += random_offset

    # Clamp the time so it stays within the desired boundaries
    time = max(min(time, max_time), min_time)

    return time

# --------------------------
# Server Code
# --------------------------
class Server:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Allow the server to reuse the address to avoid "Address already in use" errors
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"[SERVER] Listening on {self.host}:{self.port}")
        self.moves = ["", ""]
        self.moves_snapshot = ""
        self.last_move = ["", ""]
        self.hands = ["", ""]
        self.clients = []  # List of client sockets
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.current_future = None
        self.times = [[1800, 1800], [1800, 1800]]
        self.board = BughouseBoard()
        self.side = chess.WHITE
        self.mutex = Lock()
        self.positions = []
        self.job_id = 0
        self.q = 0
        #self.book = {}
        with open('book.pkl', 'rb') as f:
            self.book = pickle.load(f)

    def start(self):
        thread = threading.Thread(target=self.accept_clients, daemon=True)
        thread.start()

    def accept_clients(self):
        while True:
            client_sock, client_addr = self.server_socket.accept()
            self.clients.append(client_sock)
            print(f"[SERVER] Accepted connection from {client_addr}")
            # Start a new thread to handle communication with this client
            client_thread = threading.Thread(target=self.handle_client, args=(client_sock, client_addr), daemon=True)
            client_thread.start()

    def handle_client(self, client_sock, client_addr):
        while True:
            try:
                data = client_sock.recv(1024)
                if not data:
                    print(f"[SERVER] Client {client_addr} disconnected")
                    self.clients.remove(client_sock)
                    client_sock.close()
                    break

                message = data.decode()

                for cmd in message.split("\n"):
                    if not cmd:
                        continue

                    with self.mutex:
                        if cmd.startswith("side"):
                            _, side = cmd.split(" ")
                            self.side = side == "0"

                        elif cmd.startswith("times"):
                            _, board_num, a, b = cmd.split(" ")
                            board_num = int(board_num)
                            self.times[board_num] = [int(a), int(b)]

                        elif cmd.startswith("moves"):
                            _, board_num, tcn_moves = cmd.split(" ")
                            board_num = int(board_num)

                            if tcn_moves != self.moves[board_num]:
                                self.moves[board_num] = tcn_moves
                                try:
                                    print(self.moves)
                                    self.board, self.moves_snapshot = parse_moves(self.moves)
                                except Exception as e:
                                    print(e)
                                    continue

                future_to_wait = None
                with self.mutex:
                    if self.moves_snapshot not in self.positions:
                        self.positions.append(self.moves_snapshot)
                        while len(self.positions) > 1:
                            self.positions.pop(0)

                        # Create a snapshot of the current board state and other variables
                        board_snapshot = self.board.fen()[:]  # Adjust copying as needed
                        side_snapshot = self.side
                        clients_snapshot = self.clients[:]  # shallow copy of client list
                        # Note: If your board is mutable, consider a deep copy.

                        # Calculate time difference etc.
                        time_difference = self.times[1][self.side] - self.times[0][self.side]

                        # Abort any currently running computation.
                        if self.current_future is not None and not self.current_future.done():
                            print("[MAIN LOOP] Stopping previous engine computation.")
                            # Tell the engine to stop (which internally sends "stop" to the engine).
                            engine.stop()
                            self.job_id += 1
                            future_to_wait = self.current_future

                        phase = get_phase(self.times)
                        movetime = compute_thinking_time(self.q, phase)

                        # Submit the new job and update the current_future reference.
                        self.current_future = self.executor.submit(
                            self.compute_and_send_move,
                            board_snapshot,
                            self.moves_snapshot,
                            time_difference,
                            movetime,
                            side_snapshot,
                            clients_snapshot,
                            self.job_id
                        )

                # Release the lock before waiting for the previous future to complete.
                if future_to_wait is not None:
                    try:
                        future_to_wait.result(timeout=50)
                    except concurrent.futures.TimeoutError:
                        print("[MAIN LOOP] Previous computation did not finish in time.")

            except Exception as e:
                print(f"[SERVER] Error with client {client_addr}: {e}")
                self.clients.remove(client_sock)
                client_sock.close()
                break

    def compute_and_send_move(self, board_snapshot, moves_snapshot, time_difference, movetime, side, clients, job_id):
        """
        Runs in a separate thread. It checks that the board state hasn't changed
        since the snapshot was taken, then sets the engine position based on that snapshot,
        computes the best move, and sends the move to the appropriate client.
        """
        global engine

        # First, check that the board state is still what we expect.
        with self.mutex:
            current_snapshot = self.board.fen()[:]  # make a copy of the current board state
        if current_snapshot != board_snapshot:
            print("[ENGINE THREAD] Board state updated before move calculation. Aborting move.")
            return

        best_move = None
        # Compute best move based on the snapshot.
        should_sit = (time_difference > 10) and self.q < 0.3

        if job_id == self.job_id:
            if (self.board.turn(0) == self.side and self.board.turn(1) != self.side) or (not should_sit and (self.board.turn(0) == self.side or self.board.turn(1) != self.side)):
                engine.set_mode("go")
                #engine.set_mode("sit" if sit else "go")
                engine.set_side(side)
                engine.set_position(moves=moves_snapshot)
                best_move, q_value, nodes = engine.get_best_move(movetime=movetime)

        if best_move is None or best_move == "pass" or best_move == "(none)":
            return

        with self.mutex:
            self.q = q_value

        print(q_value)

        # Check again that the board state hasn't changed during calculation.
        with self.mutex:
            current_snapshot = self.board.fen()[:]
        if current_snapshot != board_snapshot:
            print("[ENGINE THREAD] Board state updated after move calculation. Aborting move.")
            return

        # Send the move to the appropriate client.
        client_index = int(best_move[0]) - 1
        clients[client_index].sendall(best_move[1:].encode())
        print(f"Sent move {best_move} to client {client_index + 1}")
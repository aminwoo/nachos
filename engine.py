import re
import os
import subprocess

import chess

from board import BughouseBoard
from tcn import tcn_decode

class Engine:
    def __init__(self, engine_path):
        """
        Initialize the hivemind engine.

        :param engine_path: Path to the hivemind executable.
        """
        env = os.environ.copy()
        env['LD_LIBRARY_PATH'] = '.'

        self.engine = subprocess.Popen(
            engine_path,
            universal_newlines=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env = env
        )
        self._initialize_engine()

    def _initialize_engine(self):
        """
        Initialize the engine by sending the 'uci' command and waiting for 'uciok'.
        """
        self.send_command("uci")
        while True:
            output = self.read_output()
            if "uciok" in output:
                break

    def send_command(self, command):
        """
        Send a command to the hivemind engine.

        :param command: The command to send.
        """
        self.engine.stdin.write(command + "\n")
        self.engine.stdin.flush()

    def read_output(self):
        """
        Read the output from the hivemind engine.

        :return: The output from the engine.
        """
        return self.engine.stdout.readline().strip()

    def stop(self):
        self.send_command("stop")

    def set_position(self, fen=None, moves=None):
        """
        Set the position on the board.

        :param fen: The FEN string representing the board position.
        :param moves: A list of moves in UCI format.
        """
        if fen:
            self.send_command(f"position fen {fen}")
        if moves:
            self.send_command(f"position startpos moves {moves}")

    def set_side(self, side):
        self.send_command(f"team {'white' if side == chess.WHITE else 'black'}")

    def set_mode(self, mode):
        self.send_command(f"set mode {mode}")

    def get_best_move(self, movetime=1000):
        """
        Get the best move from the current position.

        :param movetime: The depth to search for the best move.
        :return: The best move in UCI format.
        """

        self.send_command(f"go movetime {movetime}")

        q_value = 0
        nodes = 0
        while True:
            output = self.read_output()

            # Extract Q value
            q_pattern = r"Q value\s+(-?\d+\.\d+)"
            q_match = re.search(q_pattern, output)
            if q_match:
                q_value = float(q_match.group(1))

            # Extract nodes count
            nodes_pattern = r"nodes\s+(\d+)"
            nodes_match = re.search(nodes_pattern, output)
            if nodes_match:
                nodes = int(nodes_match.group(1))

            if "bestmove" in output:
                best_move = output.split()[1]
                return best_move, q_value, nodes

def parse_moves(tcn_moves):
    board = BughouseBoard()
    moves = ""

    # Use separate indices for board 1 and board 2 move strings.
    i0 = 0  # index into tcn_moves[0]
    i1 = 0  # index into tcn_moves[1]

    # Process moves from board 1
    while i0 < len(tcn_moves[0]):
        segment = tcn_moves[0][i0:i0+2]
        move = tcn_decode(segment)[0]

        if move.drop is not None and not board.can_drop(0, move):
            segment = tcn_moves[1][i1:i1 + 2]
            move = tcn_decode(segment)[0]
            moves += f"2{board.push(1, move)} "
            i1 += 2
        else:
            moves += f"1{board.push(0, move)} "
            i0 += 2

    # Process any remaining moves from board 2.
    while i1 < len(tcn_moves[1]):
        segment = tcn_moves[1][i1:i1+2]
        move = tcn_decode(segment)[0]
        moves += f"2{board.push(1, move)} "
        i1 += 2

    return board, moves.strip()


# Example usage:
if __name__ == "__main__":
    #print(parse_moves(["mCZJCJ7JbsJ7lB0Sgv5QfH", "mC0Sgv5Q"]))

    # Replace with the path to your Stockfish executable
    engine_path = "./hivemind"

    engine = Engine(engine_path)

    # Set the position to the starting position
    #engine.set_position()

    # Get the best move from the starting position with a depth of 10
    engine.stop()
    #engine.set_position("r1bqk2r/pppp1Qp1/2n2n1p/2b1p3/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 0 6|rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    engine.set_side(chess.WHITE)
    #engine.set_mode("sit")
    engine.set_mode("go")
    engine.set_position(moves=parse_moves(['mC!Tbs0SlBZRgv5QfH90BJ8!JQXQHQ45=V2VcVTEV979eg-D-uEKvKRK-N=xNDKDCK+XdE92ExXQuE6Xnv0IghIB+TBKTK-MEV!9K292xE1TED-UDY&0Y0U0VE0L*Y=0Y0L0+V21VMTMae0LsCQCvC*DfDMD-M10+T08=18Z-KZYMSYRCLXohoDvKv=xox-nEn=EnE-nEn+E', 'lB0KBK5Qgv70bsQKsJKvov07mC=SJs9ziqzsjs-y=j*R=t-Fhg=U+M-ofoFogo=xog+T+F&ogoxo-gTMcM=TMuUMFw=D+mDunu3NwRYR-nNF=r=wnxwpelp{dg&w+pwxry-fmfo{af*ogoxo*n-blc']
)[1])
    print(parse_moves(['mC!Tbs0SlBZRgv5QfH90BJ8!JQXQHQ45=V2VcVTEV979eg-D-uEKvKRK-N=xNDKDCK+XdE92ExXQuE6Xnv0IghIB+TBKTK-MEV!9K292xE1TED-UDY&0Y0U0VE0L*Y=0Y0L0+V21VMTMae0LsCQCvC*DfDMD-M10+T08=18Z-KZYMSYRCLXohoDvKv=xox-nEn=EnE-nEn+E', 'lB0KBK5Qgv70bsQKsJKvov07mC=SJs9ziqzsjs-y=j*R=t-Fhg=U+M-ofoFogo=xog+T+F&ogoxo-gTMcM=TMuUMFw=D+mDunu3NwRYR-nNF=r=wnxwpelp{dg&w+pwxry-fmfo{af*ogoxo*n-blc']
)[1])
    #print(parse_moves(['mC0SbsZRlB!Tgv90CKRKvK8!=V-LV2!2ft=UtLSL+V2!V909K1!1BJ70=S6SJS0Ssm9z', 'mC!TltZJCJTJgv5Qfm0K=AJDcDKDeg=xfe=unuDu=J9I+F=ngf*h-gn}vg'])[0].fen())
    #print(parse_moves(['mC0SbsZRlB!Tgv90CKRKvK8!=V-LV2!2ft=UtLSL+V2!V909K1!1BJ70=S6SJS0Ssm9z', 'mC!TltZJCJTJgv5Qfm0K=AJDcDKDeg=xfe=unuDu=J9I+F=ngf*h-gn}vg'])[1])
    best_move = engine.get_best_move(movetime=1000)
    print(best_move[2] * 100)
    print(f"Best move: {best_move}")

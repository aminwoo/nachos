import csv
import chess
from engine import Engine

# Define the CSV file name and header
csv_file = "positions.csv"
header = ["fen", "color", "mode", "move"]

# Sample data to write (as a list of dictionaries)
data = [
    {
        "fen": "rnbqkbnr/1ppp1ppp/4p3/4N3/3PP3/p1N5/PPP2PPP/R1BQKB1R[pP] b KQkq|r1bqk2r/ppp2ppp/2n1pn2/6N1/1b1P4/2P2N2/PP3PPP/R1BQKB1R[P] b KQkq",
        "color": "white",
        "mode": "go",
        "move": ""
    },
    {
        "fen": "rnbqkbnr/1ppp1ppp/4p3/4N3/3PP3/2N5/PpP2PPP/R1BQKB1R[pP] w KQkq|r1bqk2r/ppp2ppp/2n1pn2/6N1/1b1P4/2P2N2/PP3PPP/R1BQKB1R[P] b KQkq",
        "color": "white",
        "mode": "go",
        "move": ""
    },
    {
        "fen": "r2q3r/ppp2k2/2n1NpBp/3p4/3P4/2P1P3/P1P2PPP/R2QK1NR[NrqbnpppP] b KQ|r1bk4/ppp1npNp/2nb3B/3B2B1/3P4/2P5/P1P2PPP/R2QK2R[bpp] b KQ",
        "color": "black",
        "mode": "go",
        "move": ""
    },
    {
        "fen": "r2q3r/ppp2k2/2n1NpBp/3p4/3P4/2P1P3/P1P2PPP/R2QK1NR[NrqbnpppP] b KQ|r1bk4/ppp1npNp/2nb3B/3p2B1/3P4/2P2B2/P1P2PPP/R2QK2R[bpp] w KQ",
        "color": "black",
        "mode": "sit",
        "move": ""
    },
    {
        "fen": "r2q3r/ppp5/2n1Npkp/3p4/3P4/2P1P3/P1P2PPP/R2QK1NR[NrqbnpppP] w KQ|r1bk4/ppp1npNp/2nb3B/3B2B1/3P4/2P5/P1P2PPP/R2QK2R[Bbpp] b KQ",
        "color": "white",
        "mode": "sit",
        "move": ""
    },
    {
        "fen": "r2q3r/ppp5/2n1Npkp/3p4/3P4/2P1P3/P1P2PPP/R2QK1NR[NrqbnpppP] w KQ|r1bk4/ppp1npNp/2nb3B/3B2B1/3P4/2P5/P1P2PPP/R2QK2R[Bbpp] b KQ",
        "color": "white",
        "mode": "go",
        "move": ""
    },
    {
        "fen": "rn3qk1/pp4pp/2p5/8/2b1P1n1/2N3P1/PPPP3P/R1BQ2K1[BNP] w|rnbr4/ppp2kpp/8/4n3/4PB1b/2N2bB1/PPP2KpP/R5R1[NRQrqpppppPPP] b",
        "color": "white",
        "mode": "sit",
        "move": ""
    },
    {
        "fen": "rn3qk1/pp4pp/2p5/8/2b1P1n1/2N3P1/PPPP3P/R1BQ2K1[BNP] w|rnbr4/ppp2kpp/8/4n3/4PB1b/2N2bB1/PPP2KpP/R5R1[NRQrqpppppPPP] b",
        "color": "white",
        "mode": "go",
        "move": ""
    },
    {
        "fen": "2rq1rk1/pppnb1p1/4p1p1/3pP1pp/8/2N1PPB1/PPP2NPP/R2Q1RK1/Nn b - - 1 2|r4rk1/ppp2p1p/4bB1p/8/6b1/2P5/P1PB1PPP/R3R1K1/qbbnnppPB w",
        "color": "black",
        "mode": "sit",
        "move": "1N@e4"
    },
    {
        "fen": "r1bq1b1r/ppp1k1pp/3npp2/4N1B1/3Q4/2N2N2/PPP2KPP/R6R/NQqbnPPP w|r1b1k2r/ppp2ppp/2p1p3/6B1/B2nn3/2P1P3/P4PPP/R1B1K2R/pPP b kq",
        "color": "white",
        "mode": "sit",
        "move": "1Q@f7"
    },
    {
        "fen": "2rq1rk1/pppnb1p1/4p1p1/3pP1pp/4P3/2N1P1B1/PPP2NPP/R2Q1RK1/NN b - - 0 3|r4rk1/ppp2p1p/4bB1p/8/6b1/2P5/P1PB1PPP/R3R1K1/qbbnnppPB w",
        "color": "black",
        "mode": "sit",
        "move": "1f8f2"
    },
    {
        "fen": "r1bk1b1r/ppp1p1pp/5n2/6NB/B7/2Nn4/PP1B1PPP/5K1R[BNRQqbbpPP] b|r2q1rk1/p1p1ppP1/2p3nQ/3p2Pp/3P3n/2N1PP2/PPPp3P/R2K2R1[p] b",
        "color": "black",
        "mode": "go",
        "move": ""
    },
    {
        "fen": "r1bqk2r/ppp2ppp/2n5/3nP3/1b6/2N2N2/PPP2PPP/R1BQKB1R[Bnp] w KQkq|rnbqkb1r/ppp2ppp/5p2/3p4/1p1P4/4P3/PPP1P1PP/RN1QKBNR[P] b KQkq",
        "color": "white",
        "mode": "sit",
        "move": ""
    },
    {
        "fen": "r2qr1k1/p1p1ppP1/2p3nQ/3p2Pp/3P3n/2N1PP2/PPPp3P/R2K2R1/p w - - 1 2|r1bk1b1r/ppp1p1pp/5n2/6NB/B7/2Nn4/PP1B1PPP/5K1R[BNRQqbbpPP] b",
        "color": "white",
        "mode": "sit",
        "move": ""
    },
    {
        "fen": "r2qr1k1/p1p1ppP1/2p3nQ/3p2Pp/3P3n/2N1PP2/PPPp3P/R2K2R1/p w - - 1 2|r1bk1b1r/ppp1p1pp/5n2/6NB/B7/2Nn4/PP1B1PPP/5K1R[BNRQqbbpPP] b",
        "color": "white",
        "mode": "go",
        "move": ""
    },
    {
        "fen": "r2q1rk1/p1p1ppP1/2p3nQ/3p2Pp/3P3n/2N1PP2/PPPp3P/R2K2R1[p] b|r1bk1b1r/ppp1p1pp/5n2/6NB/B7/2Nn4/PP1B1PPP/5K1R[BNRQqbbpPP] b",
        "color": "black",
        "mode": "go",
        "move": ""
    },
    {
        "fen": "r1bk1b1r/ppp1p1pp/8/6Nn/B7/2Nn4/PP1B1PPP/5K1R/PPNBRQpbbbq w - - 0 2|r2qr1k1/p1p1ppP1/2p3nQ/3p2Pp/3P3n/2N1PP2/PPPp3P/R2K2R1/pP w - - 1 2",
        "color": "white",
        "mode": "sit",
        "move": ""
    },
    {
        "fen": "r1bqk2r/pppp1pp1/2n2n1p/2b1p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 0 6|r4rk1/ppp2p1p/4bB1p/8/6b1/2P5/P1PB1PPP/R3R1K1/qbbnnppPB w",
        "color": "white",
        "mode": "sit",
        "move": ""
    },
    {
        "fen": "r2q1rk1/ppp1bpBp/3p4/3B4/3pP3/1B1P4/PPP2PPP/R2b1RK1[NNNnnp] b|r2q1r1k/p1pb1pnp/2pbp2N/3n4/3Pp2P/2B1P3/PPP2PP1/R2QK2R[Qp] w KQ",
        "color": "black",
        "mode": "sit",
        "move": ""
    },
]

# Write data to the CSV file using DictWriter
with open(csv_file, mode="w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=header)
    writer.writeheader()  # Write the header row
    for row in data:
        writer.writerow(row)

print(f"Data successfully written to {csv_file}.\n")

engine_path = "./hivemind"
engine = Engine(engine_path)

# Read the CSV file using DictReader and print each row
with open(csv_file, mode="r") as file:
    reader = csv.DictReader(file)
    print("Reading the CSV file:")
    for row in reader:
        print(row["fen"])
        engine.set_position(row["fen"])
        engine.set_side(row["color"] == "white")
        engine.set_mode(row["mode"])
        print(engine.get_best_move(movetime=5000))

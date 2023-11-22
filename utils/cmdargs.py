import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-m', '--mode', type=str, help="Mode (leave blank for default rendering mode)",
                    choices=['playing', 'testing'],
                    default='playing')
parser.add_argument('-s', "--seed", type=int,
                    help="Seed for random number generator",
                    default=None)
parser.add_argument('-t', "--tempo", type=int,
                    help="Specify song BPM",
                    default=None)
parser.add_argument('-d', "--difficulty", type=float,
                    help="Difficulty",
                    default=None)
parser.add_argument('-a', "--ar", type=float,
                    help="Circle approach rate",
                    default=None)

args = parser.parse_args()
print(args)

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-m', '--mode', type=str, help="Mode (leave blank for default rendering mode)",
                    choices=['playing', 'testing'],
                    default='playing')
parser.add_argument('-s', "--seed", type=int,
                    help="Seed for random number generator",
                    default=None)

args = parser.parse_args()
print(args)

import argparse

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawTextHelpFormatter,
    description="Pygame rhythm game app with automatic map generation."
)
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
parser.add_argument('-y', "--youtube", type=str,
                    help="YouTube link for the music video",
                    default=None)

parser.epilog = """Example usage:
  python main.py -d 6 -a 10 --tempo 246 -y "https://www.youtube.com/watch?v=-LwBbLa_Vhc"
"""

args = parser.parse_args()

if hasattr(args, 'help'):
    parser.print_help()
else:
    print(args)

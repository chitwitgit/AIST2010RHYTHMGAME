import logging
from utils.cmdargs import args


def main():
    fmt = '%(asctime)s (%(filename)s) [%(levelname)s] - %(message)s'
    logging.basicConfig(level=logging.INFO, format=fmt)

    mode = args.mode


if __name__ == "__main__":
    main()

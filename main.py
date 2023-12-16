from game.game import Game
from game.utils.cmdargs import args


def main():
    # Manage command line arguments
    youtube_link = args.youtube if args.youtube is not None else "https://www.youtube.com/watch?v=_5aZ6bhho68"
    seed = args.seed if args.seed is not None else 777
    given_tempo = args.tempo if args.tempo is not None else None
    difficulty = args.difficulty if args.difficulty is not None else 5
    approach_rate = args.ar if args.ar is not None else 10

    is_use_new_files = True
    use_game_background = True
    settings = youtube_link, seed, given_tempo, difficulty, approach_rate, is_use_new_files, use_game_background

    game = Game(settings)
    game.run()


if __name__ == '__main__':
    main()

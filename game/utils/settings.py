from utils.cmdargs import args

if args.youtube is not None:
    youtube_link = args.youtube
else:
    youtube_link = "https://www.youtube.com/watch?v=HFPBd_mQYhg"
    youtube_link = "https://www.youtube.com/watch?v=fsrORJ4Spxc"

if args.tempo is not None:
    given_tempo = args.tempo
else:
    given_tempo = 76
if args.difficulty is not None:
    difficulty = args.difficulty
else:
    difficulty = 6  # usually (0, 10]
if args.ar is not None:
    approach_rate = args.ar
else:
    approach_rate = 10  # must be >0, usually [1, 10]

mode = "debug x"
is_use_new_files = False
settings = youtube_link, given_tempo, difficulty, approach_rate, mode, is_use_new_files

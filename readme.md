# Rhythm Game with Automatic Map Generation

## Description
A Pygame app created for AIST2010 course project. It is a rhythm game which can take in any piece of music via a
downloaded music file or a youtube link, and generate a map for the music according to its musical data. The rhythm game
has similar gameplay as the popular rhythm game osu!

## Table of Contents

1. [Description](#description)
2. [Installation](#installation)
   - [Setting up the Python Environment](#setting-up-the-python-environment)
     - [Step 1: Create a Python Environment](#step-1-create-a-python-environment)
       - [Using conda](#using-conda)
       - [Using python (virtualenv)](#using-python-virtualenv)
     - [Step 2: Install the Required Packages](#step-2-install-the-required-packages)
   - [Install FFmpeg](#step-3-install-ffmpeg)
3. [Running the Project](#running-the-project)
4. [Repository Section Description](#repository-section-description)


# Installation
To use and interact with the project, follow the guidelines below.

## Setting up the Python Environment
The project requires Python 3.11. To set up the project environment, you'll need to create a Python 
virtual environment and install the required packages using `pip`.

### Step 1: Create a Python Virtual Environment
Start by creating a new Python virtual environment. You have two options: `conda` or `python` (virtualenv).

#### Using conda
If you have Anaconda or Miniconda installed, follow these steps:

1. Create a new conda environment:
   ````bash
   conda create -n rhythmgame python=3.11

2. Activate the environment:
   ````bash
   conda activate rhythmgame

#### Using python (virtualenv)
If you prefer using `python` and `virtualenv`, follow these steps:

1. Create a new virtual environment :
   ````bash
   python3 -m venv rhythmgame

2. Activate the virtual environment:
   - For Linux/Mac:
     ````bash
     source rhythmgame/bin/activate

   - For Windows:
     ````bash
     .\rhythmgame\Scripts\activate

After this step, you will have created a Python virtual environment named "rhythmgame," 
which will contain all the necessary dependencies and packages required to run the project smoothly.

### Step 2: Install the Required Packages
After creating the Python environment, you can install the required packages using pip.
Make sure you are in the project directory before running this command.

To install packages using `pip`, run the following command:
```bash
pip install -r requirements.txt
```
This command will install all the required packages into your Python environment.

## Install FFmpeg
FFmpeg is a powerful multimedia framework used in the project to convert mp4 files to mp3 files. Follow the instructions below to install FFmpeg on your system:

### Windows
1. Visit the FFmpeg website and navigate to the "Download" section.
2. Download the FFmpeg binaries for Windows from the provided links.
3. Extract the downloaded ZIP file and add the FFmpeg executable path to your system's environment variables.
4. To verify the installation, open a command prompt and enter `ffmpeg`. You should see the FFmpeg version and command line options printed to the console.

### macOS
FFmpeg can be installed using Homebrew. Open a terminal and run the following command to install FFmpeg:

```bash
brew install ffmpeg
```

To verify the installation, enter `ffmpeg` in the terminal. You should see the FFmpeg version and command line options printed to the console.

### Linux (Ubuntu)
1. Open a terminal.
2. Update the package list:
   ````shell
   sudo apt update
3. Install FFmpeg with the following command:
   ````shell
   sudo apt install ffmpeg
4. To verify the installation, enter `ffmpeg` in the terminal. You should see the FFmpeg version and command line options printed to the console.

# Running the Project
Once everything has been set up, you can run the project using an IDE like PyCharm or Visual Studio, or through the command line.

1. Navigate to the project folder
```commandline
cd C:\path\to\project
```

2. Run the main program
```commandline
python main.py
```

3. You can also specify some command line arguments to run the program. 
The command below outputs the help menu for you to learn more about the available command line arguments.
```commandline
python main.py -h
```

## Repository Section Description

### Game
The `game` section contains the source code and assets for the game. It includes game scripts, images, audio files, or any other resources specific to the game development.

- ### Data
  This section contains the assets used in the game. It includes fonts, image files, audio files, or any other relevant data resources.

- ### Utils
    The `utils` section contains utility scripts or modules that provide helper functions or tools for the game and the.

### main.py
The `main.py` file is the entry point of the project. It contains the main code that executes when the project is run. The main program drives the whole pipeline of the app.

### requirements.txt
The `requirements.txt` file specifies the Python packages and dependencies required to run the project. It includes a list of packages and their versions.

### runtime.txt
Specifies the version of python the game is intended to be run in.
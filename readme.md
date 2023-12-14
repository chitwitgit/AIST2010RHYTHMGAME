# Rhythm Game with Automatic Map Generation

## Description
A Pygame app created for AIST2010 course project. It is a rhythm game which can take in any piece of music via a
downloaded music file or a youtube link, and generate a map for the music according to its musical data. The rhythm game
has similar gameplay as the popular rhythm game osu!

## Table of Contents

1. [Description](#description)
2. [Installation](#installation)
   - [Cloning the Repository](#cloning-the-repository)
   - [Setting up the Python Environment](#setting-up-the-python-environment)
     - [Step 1: Create a Python Environment](#step-1-create-a-python-environment)
       - [Using conda](#using-conda)
       - [Using python (virtualenv)](#using-python-virtualenv)
     - [Step 2: Install the Required Packages](#step-2-install-the-required-packages)
   - [Running the Project](#running-the-project)
   - [Submitting Changes](#submitting-changes)
3. [Repository Section Description](#repository-section-description)


# Installation
To use and interact with the project, follow the guidelines below.

## Cloning the Repository
1. Start by cloning the project repository from GitHub. Open a terminal or command prompt and navigate to the directory where you want to clone the repository.
   ```bash
   git clone <repository_url>
   ```

Replace `<repository_url>` with the URL of the project repository. You can find the repository URL on the GitHub page of the project.

2. Once the repository is cloned, navigate into the project directory:
   ```bash
   cd <project_directory>
   ```
Replace `<project_directory>` with the name of the directory created during the cloning process.

## Setting up the Python Environment
We will be using Python 3.11 for this project. To set up the project environment, you'll need to create a Python environment and then install the required packages using either `conda` or `pip`.

### Step 1: Create a Python Environment
Start by creating a new Python environment. You have two options: `conda` or `python` (virtualenv).

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

1. Create a new virtual environment (optional but recommended):
   ````bash
   python3 -m venv rhythmgame

2. Activate the virtual environment:
   - For Linux/Mac:
     ````bash
     source rhythmgame/bin/activate

   - For Windows:
     ````bash
     .\rhythmgame\Scripts\activate

After this step, you will have created a Python virtual environment named "rhythmgame," which will contain all the necessary dependencies and packages required to run the project smoothly.

### Step 2: Install the Required Packages
After creating the Python environment, you can choose to install the required packages using either `conda` or `pip`.

To install packages using `conda`, run the following command:
```bash
conda install --file requirements_conda.txt
```
To install packages using `pip`, run the following command:
```bash
pip install -r requirements_pip.txt
```
These commands will install all the required packages into your Python environment.

### Running the Project
Once the environment is set up, you can run the project, edit the files, and submit changes.

### Submitting Changes
1. If you have made any changes to the dependencies, follow these steps to update the requirements files and submit your changes:

    - Activate the project environment using the appropriate command. <br><br>

    - If you added new dependencies, update the respective requirements file:
    
        - If using `conda`, run:
        ```bash
        conda list --export > requirements_conda.txt
        ```

        - If using `pip`, run:
        ```bash
        pip freeze > requirements_pip.txt
        ```


3. Commit your changes to the repository and push them to your forked repository.
   - Use the `git status` command to check the modified files.
   - Add the modified files to the staging area:
     ```bash
     git add file1 file2 ...
     ```
     Replace `file1 file2 ...` with the names of the modified files or use `git add .` to add all modified files.
   - Commit your changes with a descriptive commit message:
     ```bash
     git commit -m "Your commit message"
     ```

4. Push the Changes and Create a Pull Request:
   - Push your changes to the main branch of the project repository:
     ```bash
     git push origin main
     ```
   - Visit the project repository on GitHub.
   - You should see a notification banner indicating that you pushed changes to the main branch.
   - Click on the "Compare & pull request" button.
   - Provide a descriptive title and additional comments explaining the changes you made.
   - Review the changes in the pull request and ensure everything looks correct.
   - Click on the "Create pull request" button to submit the pull request directly to the main branch.


## Repository Section Description

### Docs
The `docs` section contains the project documentation. 

### Game
The `game` section contains the source code and assets for the game. It includes game scripts, images, audio files, or any other resources specific to the game development.

- ### Data
  This section contains the assets used in the game. It includes fonts, image files, audio files, or any other relevant data resources.

### Utils
The `utils` section contains utility scripts or modules that provide helper functions or tools for the project.

### Tests
The `tests` section contains the test cases and test scripts for the project.

### main.py
The `main.py` file is the entry point of the project. It contains the main code that executes when the project is run. The main program would drive the whole pipeline of the app.

### requirements_conda.txt
The `requirements_conda.txt` file specifies the Conda packages and dependencies required to run the project. It includes a list of packages and their versions.

### requirements_pip.txt
The `requirements_pip.txt` file specifies the Python packages and dependencies required to run the project. It includes a list of packages and their versions.
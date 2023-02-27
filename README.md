# Amy

Amy is a chatbot with memory. Amy is designed to have conversations with a user, asking open-ended questions and saving the answers to generate the user's life story.  This could be used for recording family history, creating a memoir, or just for enterainment.

## Running Amy

### Prerequisites

- Python 3.8
- Anaconda
- VSCode

### Install

Amy is written in Python using the Django framework. Create a Python 3.8 environment and install requirements:

    git checkout https://github.com/jonfleming/Amy
    cd Amy
    conda create --name=django python=3.8
    pip install -r requirements.txt

### Configuration

There are a few settings that are needed to run.  These settings should be placed in a `.env` file in the root Amy folder.

    cp example.eve .env

### Run

In VSCode:

1. Open the Amy Folder.
2. Install the Microsoft Python extension.
3. Open the Command Palette (Ctrl+Shift+P) and type `Python: Select Interpreter` and choose your `django` environment. 
4. Click the Run icon in the Activity Bar and select `Python Django` from the RUN AND DEBUG dropdown.
5. Press F5 to run.

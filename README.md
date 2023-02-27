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
    conda activate django
    pip install -r requirements.txt

### Configuration

There are a few settings that are needed to run.  These settings should be placed in a `.env` file in the root Amy folder.

    cp example.eve .env

Edit `.env` to set your values:
    # Secret Key for your Django installation
    SECRET_KEY=q5pEroX6onq8YzQrspJJp4JRBEtEEXGx

    # URL to access the app
    BASE_URL=http://localhost:8000

    # Django debug setting
    DEBUG=True

### Run

In VSCode:

1. Open the Amy Folder.
2. Install the Microsoft Python extension.
3. Open the Command Palette (Ctrl+Shift+P) and type `Python: Select Interpreter` and choose your `django` environment. 
4. Click the Run icon in the Activity Bar and select `Python Django` from the RUN AND DEBUG dropdown.
5. Press F5 to run.

Bash:

1. conda activate django
2. python manage.py runserver

Then navigate to http://localhost:8000 in your browser

### To Debug unit tests

1. Install Pytest
2. Edit launch.json and set the `program` to the path for pytest
3. Click the Run icon in the Activity Bar and select `Debug Unit Tests` from the RUN AND DEBUG dropdown.
4. Press F5 to run.

### Create an Admin user

To manage your Django application and database records you need to create an admin user.  For details see [Creating an admin user](https://docs.djangoproject.com/en/1.8/intro/tutorial02/#creating-an-admin-user).

from pathlib import Path


# Model paths
MISTRAL7B_MODEL_PATH = Path.home().joinpath('mistral_models', '7B-Instruct-v0.3')

LAZY_LOAD = True

# TODO: make server dictionary to modularize different servers
# Email servers config
GMAIL_SERVER = "imap.gmail.com"
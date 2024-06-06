from summaily.provider import IMAPProvider
from summaily.constants import GMAIL_SERVER
from summaily.user import User
from dotenv import load_dotenv
import os


if __name__ == "__main__":   
    load_dotenv()
    gmail = IMAPProvider(GMAIL_SERVER, os.getenv('EMAIL'), os.getenv('PASSWORD'))
    user = User(gmail, "0")
    user.summarize_emails(5)
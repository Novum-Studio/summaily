from dotenv import load_dotenv
import os
from provider import IMAPProvider, GMAIL_SERVER
from user import User


if __name__ == "__main__":
    load_dotenv()
    gmail = IMAPProvider(GMAIL_SERVER, os.getenv('EMAIL'), os.getenv('PASSWORD'))
    user = User(gmail, "0")
    user.summarize_emails(5)
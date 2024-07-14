from summaily.provider import IMAPProvider
from summaily.constants import GMAIL_SERVER
from summaily.user import User
from dotenv import load_dotenv
import os



def main():
    load_dotenv()
    print("Logging in...")
    gmail = IMAPProvider(GMAIL_SERVER, os.getenv('EMAIL'), os.getenv('PASSWORD'))
    user = User(gmail, "0")
    print("Summarizing...")
    print(user.summarize_emails(5))



if __name__ == "__main__":   
    main()
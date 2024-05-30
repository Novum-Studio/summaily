from provider import EmailProvider, IMAPProvider
from dotenv import load_dotenv

class User:
    def __init__(self, email_provider : EmailProvider, user_id : str):
        self.email_provider = email_provider
        self.user_id = user_id
    
    def fetch_emails(self, num_emails = -1) -> list:
        self.email_provider.connect()
        result = self.email_provider.fetch_emails(num_emails=-1)
        return result

    def summarize_emails(self, num_emails = -1):
        pass

        






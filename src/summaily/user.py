from .provider import EmailProviderInterface
from .summarizer import Summarizer
from .constants import MISTRAL7B_MODEL_PATH

class User:
    def __init__(self, email_provider : EmailProviderInterface, user_id : str):
        self.email_provider = email_provider
        self.user_id = user_id
        self.categories = ["Others", "Job-related"]    # Email categories after summarization (User Preferences)
        self.summarizer = Summarizer(MISTRAL7B_MODEL_PATH)


    def fetch_emails(self, num_emails = -1) -> list:
        self.email_provider.connect()
        result = self.email_provider.fetch_emails(num_emails)
        return result

    def summarize_emails(self, num_emails):
        # TODO: return dictionary in which keys are different categories.
        for mail in self.fetch_emails(num_emails):
            if not mail["Body"]: continue
            summary = self.summarizer.summarize(mail['Body'], self.categories)
            print(summary)

    def _add_new_category(self, new_category):
        return 

        

        






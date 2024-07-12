from .provider import EmailProviderInterface
from .summarizer import Summarizer
from .constants import MISTRAL7B_MODEL_PATH
import json

class User:
    def __init__(self, email_provider : EmailProviderInterface, user_id : str):
        self.email_provider = email_provider
        self.user_id = user_id
        self.categories = ["Others", "Job-related"]    # Email categories after summarization (User Preferences)
        self.summarizer = Summarizer(MISTRAL7B_MODEL_PATH)


    def fetch_emails(self, num_emails: int = -1) -> list:
        self.email_provider.connect()
        result = self.email_provider.fetch_emails(num_emails)
        return result

    def summarize_emails(self, num_emails: int):
        # TODO: return dictionary in which keys are different categories.
        # TODO: store emails ids for easy access of the emails? 
        #       for example, user should be able to see full emails when they choose to see the emails in one 
        #       of the report categories.
        for id, mail in self.fetch_emails(num_emails).items():
            if not mail.body: continue
            summary = self.summarizer.summarize(' '.join(mail.body.extracted_text), self.categories)
            summary = json.loads(summary)
            summary['id'] = id
            print(summary)

    def _add_new_category(self, new_category):
        return 

        

        






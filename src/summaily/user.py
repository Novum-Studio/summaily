from .provider import EmailProviderInterface, Email
from .summarizer import Summarizer
from .constants import MISTRAL7B_MODEL_PATH
from typing import List, Dict, Any
import json

class User:
    def __init__(self, email_provider : EmailProviderInterface, user_id : str):
        self.email_provider = email_provider
        self.user_id = user_id
        self.categories = ["Others", "Transactions", "Promotions", "Updates", "Primary"]    # Email categories after summarization (User Preferences)
        self.summarizer = Summarizer(MISTRAL7B_MODEL_PATH)


    def fetch_emails(self, num_emails: int=-1) -> list:
        self.email_provider.connect()
        result = self.email_provider.fetch_emails(num_emails)
        return result

    def summarize_emails(self, num_emails: int) -> Dict[str, List[Email]]:
        result = {category: [] for category in self.categories}
        for mail in self.fetch_emails(num_emails):
            if not mail.body: continue
            summary = self.summarizer.summarize(' '.join(mail.body.extracted_text), self.categories)
            summary = json.loads(summary)
            mail.summary, mail.category = summary['summary'], summary['category']
            result[mail.category].append(mail)
        return result
    

    def _add_new_category(self, new_category: str) -> bool:
        if new_category not in self.categories: return False
        self.categories.append(new_category)
        return True

from abc import ABC, abstractmethod
import imaplib
from typing import List, Dict, Any
from .parser import EmailParser

# Abstract Base Class for all email providers.
class EmailProviderInterface(ABC):

    @abstractmethod
    def connect(self):
        """
        Establish a connection to the email server. Implementations should handle login or authentication.
        """
        pass

    @abstractmethod
    def fetch_emails(self, num_emails=-1)->list:
        """
        Retrieve specified number of emails from the server.

        Args:
            num_emails (int, optional): The number of emails to fetch. Defaults to -1 to fetch all.

        Returns:
            list: A list of dictionaries containing email fields (subject, from, to, date, body)
        """
        pass





class IMAPProvider(EmailProviderInterface):
    PROVIDER_TYPE = 'imap'
    def __init__(self, server : str, username : str, password : str):
        # TODO: Need support for OAuth (credentials_path, token_path)
        self.server = server
        self.username = username
        self.password = password
        self.credentials = None
        self.imap = None

    def connect(self):
        self.imap = imaplib.IMAP4_SSL(self.server)
        self.imap.login(self.username, self.password)
    
    def fetch_emails(self, num_emails: int =-1) -> List[Dict[str, Any]]:
        result = list()
        self.imap.select('INBOX', readonly=True)
        print("Fetching Emails...")

        _, data1 = self.imap.search(None, 'ALL')
        all_mails = data1[0].split()
        recent_n_mails = all_mails[-num_emails:] if num_emails != -1 else all_mails
        for id in recent_n_mails:
            _, data2 = self.imap.fetch(id, '(RFC822)')
            raw_email = data2[0][1]
            cur = EmailParser.parse_email(raw_email, self.PROVIDER_TYPE)
            print(cur['Body'])
            result.append(EmailParser.parse_email(raw_email, self.PROVIDER_TYPE)) 

        return result
    

    

if __name__ == "__main__":
    # This is just a demonstration. In reality, you'd use this with IMAPProvider
    sample_email = b"""From: "Sender Name" <sender@example.com>
To: "Recipient Name" <recipient@example.com>
Subject: Test Email
Date: Tue, 15 Aug 2023 14:30:00 +0000

This is a test email body."""

    parsed_email = EmailParser.parse_email(sample_email, 'imap')
    print(f"Subject: {parsed_email['Subject']}")
    print(f"From: {parsed_email['From']}")
    print(f"To: {parsed_email['To']}")
    print(f"Date: {parsed_email['Date']}")
    print(f"Body: {parsed_email['Body']['plain'][0] if parsed_email['Body']['plain'] else 'No plain text body'}")
from abc import ABC, abstractmethod
from dotenv import load_dotenv
import imaplib, email, os
from email.header import decode_header

GMAIL_SERVER = "imap.gmail.com"

# Abstract Base Class for all email providers.
class EmailProvider(ABC):
    # FIXME: storing email address as default attribute but gmail OAuth would have empty username and pwd.

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

class IMAPProvider(EmailProvider):
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
    
    def fetch_emails(self, num_emails=-1) -> list:
        result = list()
        self.imap.select('INBOX', readonly=True)

        _, data1 = self.imap.search(None, 'ALL')
        all_mails = data1[0].split()
        recent_n_mails = all_mails[-num_emails:] if num_emails != -1 else all_mails
        for id in recent_n_mails:
            current_email = dict()
            _, data2 = self.imap.fetch(id, '(RFC822)')
            raw_email = data2[0][1]

            # Parse email data
            email_message = email.message_from_bytes(raw_email)
            
            # Access email fields
            subject, encoding = decode_header(email_message['Subject'])[0]
            if isinstance(subject, bytes) and encoding: subject = subject.decode(encoding)

            from_address = email_message['From']
            to_address = email_message['To']
            date = email_message['Date']

            # emails might have multipart body, combine them into one
            # TODO: could store body parts in list
            
            body = ''
            for part in email_message.walk():
                body_part = part.get_payload(decode=True)
                # FIXME: need support for scraping text/html
                if part.get_content_type() == 'text/plain':
                    body_part = body_part.decode()
                    body += body_part


            current_email['Subject'] = subject
            current_email['From'] = from_address
            current_email['To'] = to_address
            current_email['Date'] = date
            current_email['Body'] = body

            result.append(current_email)  

        return result


if __name__ == "__main__":
    load_dotenv()
    gmail = IMAPProvider(GMAIL_SERVER, os.getenv('EMAIL'), os.getenv('PASSWORD'))
    gmail.connect()

    print(gmail.fetch_emails(1))

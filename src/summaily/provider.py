from abc import ABC, abstractmethod
import imaplib, email
from email.header import decode_header
import requests
import base64

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
            # FIXME: Default set to UTF-8 decoding
            if isinstance(subject, bytes) and encoding: subject = subject.decode(encoding)

            from_address = email_message['From']
            to_address = email_message['To']
            date = email_message['Date']

            # emails might have multipart body, combine them into one
            # TODO: could store body parts in list
            
            body = ''
            for part in email_message.walk():
                body_part = part.get_payload(decode=True)
                # FIXME: need support for scraping all type of MIME text
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

class GoogleProvider(EmailProvider):
    def __init__(self, token: str):
        self.token = token
        self.session = None

    def connect(self):
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})

    def fetch_emails(self, num_emails=-1) -> list:
        result = list()
        if not self.session:
            raise Exception("Not connected to the Google API.")

        # Fetch emails from Gmail API
        response = self.session.get(
            "https://www.googleapis.com/gmail/v1/users/me/messages",
            params={"maxResults": num_emails} if num_emails > 0 else {}
        )

        if response.status_code != 200:
            raise Exception(f"Failed to fetch emails: {response.status_code}")

        messages = response.json().get("messages", [])
        for msg in messages:
            email_data = self.get_email(msg["id"])
            result.append(email_data)

        return result

    def get_email(self, msg_id):
        # Fetch a single email by ID
        response = self.session.get(
            f"https://www.googleapis.com/gmail/v1/users/me/messages/{msg_id}"
        )

        if response.status_code != 200:
            raise Exception(f"Failed to fetch email: {response.status_code}")

        msg = response.json()
        email_data = {
            "Subject": self.get_header(msg, "Subject"),
            "From": self.get_header(msg, "From"),
            "To": self.get_header(msg, "To"),
            "Date": self.get_header(msg, "Date"),
            "Body": self.get_body(msg)
        }
        return email_data

    def get_header(self, msg, header_name):
        headers = msg["payload"]["headers"]
        for header in headers:
            if header["name"] == header_name:
                return header["value"]
        return None

    def get_body(self, msg):
        parts = msg["payload"].get("parts", [])
        body = ""
        for part in parts:
            if part["mimeType"] == "text/plain":
                data = part["body"]["data"]
                body += base64.urlsafe_b64decode(data).decode()
        return body
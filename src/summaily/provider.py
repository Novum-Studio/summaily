from abc import ABC, abstractmethod
import email.utils
import imaplib, email
from email.header import decode_header
from email.message import EmailMessage, Message
from typing import List, Dict, Any, Optional, Type
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

# Abstract Base Class for all email providers.
class EmailProviderInterface(ABC):
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


class EmailParser:
    @staticmethod
    def parse_email(raw_email: Any, provider_obj: Type[EmailProviderInterface]) -> Dict[str, Any]:
        if issubclass(provider_obj, IMAPProvider):
            return EmailParser._parse_imap_email(raw_email)
    
    @staticmethod
    def _parse_imap_email(raw_email: Any) -> Dict[str, Any]:
        email_message = email.message_from_bytes(raw_email)
        return {
            "Subject": EmailParser._decode_header_value(email_message["Subject"]),
            "From": EmailParser._decode_header_value(email_message["From"]),
            "To": EmailParser._decode_header_value(email_message["To"]),
            "Date": EmailParser._parse_date(email_message["Date"]),
            "Body": EmailParser._parse_body(email_message),
            "Attachments": EmailParser._parse_attachments(email_message)
        }

    @staticmethod
    def _decode_header_value(value: Optional[str]) -> Optional[str]:
        if not value: return None
        decoded_parts = decode_header(value)
        return ''.join([part.decode(encoding or 'utf-8') if isinstance(part, bytes) else part 
                        for part, encoding in decoded_parts])

    @staticmethod
    def _get_decoded_payload(part: Message) -> Optional[str]:
        payload = part.get_payload(decode=True)
        if not payload: return None

        charset = part.get_content_charset()
        if not charset: charset = 'utf-8'  # default to UTF-8 if charset is not specified

        try:
            return payload.decode(charset)
        except UnicodeDecodeError:
            # Fallback to 'ascii' if decoding fails
            return payload.decode('ascii', errors='ignore')


    @staticmethod
    def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
        if not date_str: return None

        try:
            # Parse the date string into a tuple
            parsed_date = email.utils.parsedate_tz(date_str)
            if not parsed_date: return None

            dt = datetime(*parsed_date[:6])

            if parsed_date[9]:
                dt = dt.replace(tzinfo=pytz.FixedOffset(parsed_date[9] // 60))
            else:
                dt = pytz.utc.localize(dt)
            
            return dt
        except Exception as e:
            print(f"Error parsing date '{date_str}': {e}")
            return None
        

    @staticmethod
    def _parse_body(email_message: Message) -> Dict[str, str]:
        body = {
            "ordered_parts": [],
            "plain": [],
            "html": [],
            "extracted_text": []
        }

        if email_message.is_multipart():
            EmailParser._process_multipart(email_message, body)
        else:
            EmailParser._process_part(email_message, body)

        # Extrace text from HTML parts
        for part_type, content in body['ordered_parts']:
            if part_type == "html":
                soup = BeautifulSoup(content, 'html.parser')
                body['extracted_text'].append(soup.get_text(separator=' ', strip=True))
            elif part_type == "plain":
                body['extracted_text'].append(content)
        return body
        
    @staticmethod
    def _process_multipart(email_message: Message, body: Dict[str, Any]):
        for part in email_message.walk():
            if part.is_multipart():
                continue

            EmailParser._process_part(part, body)


    @staticmethod
    def _process_part(part: Message, body: Dict[str, Any]):
        content_type = part.get_content_type()
        content = EmailParser._get_decoded_payload(part)
        if content:
            if content_type == "text/plain":
                body["plain"].append(content)
                body["ordered_parts"].append(("plain", content))
            elif content_type == "text/html":
                body["html"].append(content)
                body["ordered_parts"].append(("html", content))


    @staticmethod
    def _parse_attachments(email_message: Message) -> List[Dict[str, Any]]:
        attachments = []
        for part in email_message.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            filename = part.get_filename()
            if filename:
                attachments.append({
                    'filename': EmailParser._decode_header_value(filename),
                    'content_type': part.get_content_type(),
                    'size': len(part.get_payload(decode=True))
                })
        return attachments

def process_email_body(email_body: Dict[str, Any]):
    print("Email Body Content:")
    for i, (part_type, content) in enumerate(email_body["ordered_parts"], 1):
        print(f"Part {i} ({part_type}):")
        print(f"{content[:100]}..." if len(content) > 100 else content)
        print()

    print("Extracted Text (in order):")
    for i, text in enumerate(email_body["extracted_text"], 1):
        print(f"Part {i}:")
        print(f"{text[:100]}..." if len(text) > 100 else text)
        print()

def process_emails(provider: EmailProviderInterface, num_emails: int = -1):
    raw_emails = provider.fetch_emails(num_emails)
    parsed_emails = [EmailParser.parse_email(raw_email, type(provider)) for raw_email in raw_emails]

    for email in parsed_emails:
        print(f"Subject: {email['Subject']}")
        print(f"From: {email['From']}")
        print(f"To: {email['To']}")
        print(f"Date: {email['Date']}")
        process_email_body(email['Body'])
        for attachment in email['Attachments']:
            print(f"Attachment: {attachment['filename']} ({attachment['content_type']})")
        print("---")
    


class IMAPProvider(EmailProviderInterface):
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
            
            result.append(EmailParser.parse_email(raw_email, type(self))) 

        return result
    

    

if __name__ == "__main__":
    # This is just a demonstration. In reality, you'd use this with IMAPProvider
    sample_email = b"""From: "Sender Name" <sender@example.com>
To: "Recipient Name" <recipient@example.com>
Subject: Test Email
Date: Tue, 15 Aug 2023 14:30:00 +0000

This is a test email body."""

    parsed_email = EmailParser.parse_email(sample_email, IMAPProvider)
    print(f"Subject: {parsed_email['Subject']}")
    print(f"From: {parsed_email['From']}")
    print(f"To: {parsed_email['To']}")
    print(f"Date: {parsed_email['Date']}")
    print(f"Body: {parsed_email['Body']['plain'][0] if parsed_email['Body']['plain'] else 'No plain text body'}")
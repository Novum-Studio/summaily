import imaplib
from dotenv import load_dotenv
import email
from email.header import decode_header
import webbrowser
import os

class User:
    def __init__(self, email, emailPwd):
        # load email and password from .env file for default testing
        self.emailAddress = email
        self.emailPwd = emailPwd

        # imap object for handling user email
        self.mail = imaplib.IMAP4_SSL("imap.gmail.com")
        self.mail.login(self.emailAddress, self.emailPwd)
        
    def getRecentNEmails(self, num=20) -> list:
        """Get the N recent emails from email account.

        Args:
            num (int, optional): The number of recent emails to get. Defaults to 20.

        Returns:
            list: list of dict including subject, from, to, date, and body of the num emails.
                  Its length would be the same as its argument num.
        """
        result = list()
        self.mail.select('INBOX', readonly=True)

        _, data1 = self.mail.search(None, 'ALL')
        all_mails = data1[0].split()
        recent_n_mails = all_mails[-num:] if num < len(all_mails) else all_mails
        for id in recent_n_mails:
            current_email = dict()
            _, data2 = self.mail.fetch(id, '(RFC822)')
            raw_email = data2[0][1]

            # Parse email data
            email_message = email.message_from_bytes(raw_email)
            
            # Access email fields
            subject, encoding = decode_header(email_message['Subject'])[0]
            if isinstance(subject, bytes): subject = subject.decode(encoding)

            from_address = email_message['From']
            to_address = email_message['To']
            date = email_message['Date']

            # emails might have multipart body, combine them into one
            # TODO: could store body parts in list
            body = ''
            for part in email_message.walk():
                body_part = part.get_payload(decode=True)
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
    user = User(os.getenv('EMAIL'), os.getenv('PASSWORD'))
    print(user.getRecentNEmails(1))

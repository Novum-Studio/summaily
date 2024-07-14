import email
import email.utils
from email.header import decode_header
from email.message import Message
from typing import List, Dict, Any, Optional, Callable
from bs4 import BeautifulSoup
from datetime import datetime
from dataclasses import dataclass, field, asdict
import pytz, re

@dataclass
class Attachment:
    filename: str
    content_type: str
    size: int

@dataclass
class EmailBody:
    plain: List[str]
    html: List[str]
    extracted_text: List[str]

@dataclass
class Email:
    id: str
    subject: str
    from_address: str
    to_address: str
    date: datetime
    body: EmailBody
    attachments: List[Attachment] = field(default_factory=list)
    category: Optional[str] = None
    summary: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        email_dict = asdict(self)
        email_dict['date'] = self.date.isoformat()
        return email_dict

    @classmethod
    def from_dict(cls, data: dict):
        data['date'] = datetime.fromisoformat(data['date'])
        data['body'] = EmailBody(**data['body'])
        data['attachement'] = [Attachment(**att) for att in data['attachement']]
        return cls(**data)
    

class EmailParser: 
    @staticmethod
    def parse_email(email_id: str, raw_email: Any, provider_type: str) -> Dict[str, Any]:
        parsing_strategy = EmailParser.PARSING_STRATEGIES.get(provider_type)
        if parsing_strategy:
            return parsing_strategy(email_id, raw_email)
        else:
            return ValueError(f"Unsupported email provider type: {provider_type}")
    
    @staticmethod
    def _parse_imap_email(email_id: str, raw_email: Any) -> Email:
        email_message = email.message_from_bytes(raw_email)
        subject = EmailParser._decode_header_value(email_message["Subject"])
        from_address = EmailParser._decode_header_value(email_message["From"])
        to_address = EmailParser._decode_header_value(email_message["To"])
        date = EmailParser._parse_date(email_message["Date"])
        body = EmailParser._parse_body(email_message)
        attachments = EmailParser._parse_attachments(email_message)


        return Email(
            id=email_id,
            subject=subject,
            from_address=from_address,
            to_address=to_address,
            date=date,
            body=EmailBody(**body),
            attachments=[Attachment(**att) for att in attachments]
        )

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
            "plain": [],
            "html": [],
            "extracted_text": []
        }

        if email_message.is_multipart():
            EmailParser._process_multipart(email_message, body)
        else:
            EmailParser._process_part(email_message, body)

        return body
        
    @staticmethod
    def _process_multipart(email_message: Message, body: Dict[str, Any]):
        for part in email_message.walk():
            if part.is_multipart(): continue

            EmailParser._process_part(part, body)


    @staticmethod
    def _process_part(part: Message, body: Dict[str, Any]):
        content_type = part.get_content_type()
        content = EmailParser._get_decoded_payload(part)
        # TODO: store image reference for future use.
        content = re.sub(r'\[image:.*?\]', '', content)
        content = content.replace('\r\n', '\n')
        content = '\n'.join(line.strip() for line in content.splitlines() if line.strip())
        if content:
            if content_type == "text/plain":
                body["plain"].append(content)
                body['extracted_text'].append(content)
            elif content_type == "text/html":
                body["html"].append(content)
                soup = BeautifulSoup(content, 'html.parser')
                body['extracted_text'].append(soup.get_text(separator=' ', strip=True))


    @staticmethod
    def _parse_attachments(email_message: Message) -> List[Dict[str, Any]]:
        attachments = []
        for part in email_message.walk():
            if part.get_content_maintype() == 'multipart' or not part.get('Content-Disposition'):
                continue
            
            filename = part.get_filename()
            if filename:
                attachments.append({
                    'filename': EmailParser._decode_header_value(filename),
                    'content_type': part.get_content_type(),
                    'size': len(part.get_payload(decode=True))
                })
        return attachments

    PARSING_STRATEGIES: Dict[str, Callable] = {
        'imap' : _parse_imap_email
    }
from abc import ABC, abstractmethod

# Abstract Base Class for all email providers.
class EmailProvider(ABC):
    # FIXME: storing email address as default attribute but gmail OAuth would have empty username and pwd.
    def __init__(self):
        self.imap = None

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



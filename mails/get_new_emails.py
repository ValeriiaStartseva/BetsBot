import email
from typing import List

from mails.config import ENCODING
from mails.helpers import connection, get_link


def get_new_emails() -> List[str]:
    imap = connection()
    if not imap:
        return []

    status, messages = imap.select("INBOX")  # inbox folder
    res, unseen_msgs = imap.uid("search", "UNSEEN", "ALL")
    letter_links = []
    unseen_msgs = [msg for msg in unseen_msgs if msg]
    for unseen_msg in unseen_msgs:
        unseen_msg = unseen_msg.decode(ENCODING).split(" ")
        if unseen_msg:
            for letter in unseen_msg:
                res, msg = imap.uid("fetch", letter, "(RFC822)")
                if res == "OK":
                    msg = email.message_from_bytes(msg[0][1])
                    letter_links.append(get_link(msg))

        else:
            continue

    imap.logout()
    return letter_links

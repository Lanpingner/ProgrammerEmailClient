from datetime import datetime
from threading import Thread
from typing_extensions import Tuple
from connection.database_base import DataBaseConfig
from db import getDB
from connection.postgres_connector import PostgresSQL
import imaplib
import time
import re
from typing import List, Dict
import traceback
from email import message_from_bytes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import make_msgid
from email.utils import parsedate_to_datetime, getaddresses, parseaddr
from email.header import decode_header
from psycopg.types.json import Json as PJson
import numpy as np


class ImapAccount:
    def __init__(self) -> None:
        self.host = ""
        self.user = ""
        self.password = ""

    def __repr__(self) -> str:
        return str({"host": self.host, "user": self.user, "pass": self.password})


class ImapFolderWorker(Thread):
    def __init__(self, folder_id, account: ImapAccount):
        self.db = PostgresSQL(getDB())
        self.folder_id = folder_id
        self.account = account
        self.running = True
        self.folder_name = self.getFolderInfo()
        super().__init__()

    def getFolderInfo(self):
        conn = self.db.new_connection()
        data = self.db.fetchone(
            conn,
            "select folder_name from accounts.folders where id = %s",
            [self.folder_id],
        )
        self.db.commit(conn)
        return data[0]

    def process_email(self, imap, lnum):
        for num in lnum[::-1]:
            start_time = datetime.now()
            enStatus, endata = imap.fetch(num, "BODY.PEEK[HEADER]")
            fstatus, flag_data = imap.fetch(num, "(FLAGS)")
            flag_str = flag_data[0].decode()
            flags = flag_str.split("(")[2].strip(")").split()

            if enStatus == "OK":
                msg = None
                raw_email = endata[0][1]
                try:
                    msg = message_from_bytes(raw_email)
                except Exception as e:
                    print(f"Error parsing email {num}: {e}")
                    return

                if msg is not None:
                    uploaded = False
                    try:
                        st, tags = self.check_email_taggers(email=msg, flags=flags)
                        if st:
                            self.workEmail(num=num, cimap=imap, flags=flags, tags=tags)
                        uploaded = True
                    except Exception as e:
                        traceback.print_exc(None, None)
                        print("Error work email: ", num, "\n error:", e)

                    end_time = datetime.now()
                    if 1 == 2:
                        print(
                            "Total seconds to work ",
                            num,
                            " email UploadedStatus:",
                            uploaded,
                            " :",
                            (end_time - start_time).total_seconds(),
                        )

    def newWorker(self, list):
        imap = imaplib.IMAP4_SSL(self.account.host)
        imap.login(self.account.user, self.account.password)
        imap.select(self.folder_name)
        xa = Thread(
            target=self.process_email,
            args=(
                imap,
                list,
            ),
        )
        return (xa, imap)

    def run(self) -> None:
        folder_workers = []
        try:
            imap = imaplib.IMAP4_SSL(self.account.host)
            imap.login(self.account.user, self.account.password)
            imap.select(self.folder_name)
            status, data = imap.search(None, "ALL")
            if status == "OK":
                emails = data[0].decode().split(" ")
                workers_list = np.array_split(emails, 5)
                for ls in reversed(workers_list):
                    (res) = self.newWorker(ls)
                    res[0].start()
                    folder_workers.append(res)
            imap.close()
            imap.logout()
            for index, w in enumerate(folder_workers):
                if not w[0].is_alive():
                    w[1].close()
                    w[1].logout()
                    folder_workers.pop(index)
        except Exception as e:
            print(f"Error in run loop: {e}")

    def parseMultipleAddress(self, email, field):
        to_ = email.get(field)
        to_addresses = getaddresses([to_])
        to_names_emails = []
        for to_name, to_email in to_addresses:
            decoded_name = decode_header(to_name)[0]
            if isinstance(decoded_name, bytes):
                decoded_name = decoded_name.decode(encoding if encoding else "utf-8")
            to_names_emails.append({"name": decoded_name[0], "address": to_email})
        if len(to_names_emails) == 0 or to_names_emails[0]["address"] == "None":
            return []
        else:
            return to_names_emails

    def check_email_taggers(self, email, flags) -> Tuple[bool, list[str]]:
        in_conn = self.db.new_connection()
        taggers = self.db.fetchall(
            in_conn,
            """
            SELECT 
            th.id, 
            th.tags,
            th.operator,
            (select json_agg(row_to_json(ti.*)) from accounts.tagger_item ti where ti.tagger_id = th.id)
            FROM accounts.tagger_header th
            where folder_id = %s and enabled
            """,
            [self.folder_id],
        )
        self.db.commit(in_conn)
        if len(taggers) == 0:
            return (False, [])
        for data in taggers:
            if data[3] is None:
                return (True, data[1])
        return (False, [])

    def workEmail(self, num, cimap, flags, tags) -> bool:
        def concat_unique_arrays(array1, array2):
            combined_array = array1 + array2
            seen = set()
            unique_list = []
            for item in combined_array:
                if (
                    item and item not in seen
                ):  # Check if the item is not empty and not seen
                    seen.add(item)
                    unique_list.append(item)

            return unique_list

        def lst2pgarr(alist):
            return "{" + ",".join(alist) + "}"

        enStatus, endata = cimap.fetch(num, "(RFC822)")
        raw_email = endata[0][1]
        msg = None
        try:
            msg = message_from_bytes(raw_email)
        except Exception as e:
            print(e)
        if msg is not None:
            email = msg
            text = ""
            html = ""
            in_conn = self.db.new_connection()
            exists_tags = []
            attachments = []
            msg_tags = self.db.fetchone(
                in_conn,
                "select from email_storage.emails where folder_id = %s and email_id = %s",
                [self.folder_id, email["Message-ID"]],
            )
            if msg_tags is not None and len(msg_tags) != 0:
                if msg_tags[0] is not None:
                    exists_tags = msg_tags[0]
            if "\\Seen" not in flags:
                exists_tags.append("unread")
            else:
                if "Unread" in exists_tags:
                    exists_tags.remove("unread")
            subject, encoding = decode_header(email["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding if encoding else "utf-8")
            if email.is_multipart():
                # Iterate over email parts
                for part in email.walk():
                    # Extract content type of email
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))

                    try:
                        # Get the email body
                        body = part.get_payload(decode=True).decode()
                        if content_type == "text/plain":
                            text += body
                        elif content_type == "text/html":
                            html += body
                    except:
                        pass
                    if "attachment" in content_disposition:
                        filename = part.get_filename()
                        if filename:
                            # print(part.get_payload())
                            try:
                                attachment_size = len(part.get_payload(decode=True))
                            except:
                                attachment_size = 0
                            attachments.append(
                                {"filename": filename, "size": attachment_size}
                            )
            else:
                # Extract content type of email
                content_disposition = str(email.get("Content-Disposition"))
                content_type = email.get_content_type()
                if "attachment" in content_disposition:
                    filename = email.get_filename()
                    if filename:
                        attachment_size = len(email.get_payload(decode=True))
                        attachments.append((filename, attachment_size))
                else:
                    # Get the email body
                    body = email.get_payload(decode=True).decode()
                    if content_type == "text/plain":
                        text += body
                    elif content_type == "text/html":
                        html += body
            from_ = email.get("From")
            from_name, from_email = parseaddr(from_)
            from_name = decode_header(from_name)[0]
            if isinstance(from_name, bytes):
                from_name = from_name.decode(encoding if encoding else "utf-8")
            from_name = from_name[0]
            references = email.get("References")
            decoded_references = []
            if references:
                for ref in references.split():
                    decoded_ref = decode_header(ref)[0]
                    if isinstance(decoded_ref[0], bytes):
                        decoded_ref = decoded_ref[0].decode(
                            decoded_ref[1] if decoded_ref[1] else "utf-8"
                        )
                    else:
                        decoded_ref = decoded_ref[0]
                    decoded_references.append(decoded_ref)
            print(
                "Saving :",
                subject.center(150),
                "from: ".center(10),
                from_email.center(50),
                "\nwith tags:",
                str(concat_unique_arrays((exists_tags or [""]), tags)).center(30),
                " flags: ".center(10),
                str(flags).center(30),
            )
            self.db.execsql(
                in_conn,
                """
                            INSERT INTO email_storage.emails(
                                folder_id, email_id, subject, flags, tags, email_from, email_to, cc, bcc, reference, 
                                reply_to, email_date, txtbody, htmlbody, attachments)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                            ON CONFLICT (folder_id, email_id)
                            do update
                            set flags = excluded.flags, tags = excluded.tags,
                                reference = excluded.reference, email_from = excluded.email_from, email_to = excluded.email_to,
                                cc = excluded.cc, bcc = excluded.bcc,
                                reply_to = excluded.reply_to, attachments = excluded.attachments
                            """,
                [
                    self.folder_id,
                    email["Message-ID"],
                    subject,
                    lst2pgarr(flags),
                    lst2pgarr(concat_unique_arrays((exists_tags or [""]), tags)),
                    PJson({"name": from_name, "address": from_email}),
                    PJson(
                        {"accounts": self.parseMultipleAddress(email=email, field="To")}
                    ),
                    PJson({"accounts": self.parseMultipleAddress(email, "CC")}),
                    PJson({"accounts": self.parseMultipleAddress(email, "BCC")}),
                    lst2pgarr(decoded_references),
                    email["In-Reply-To"],
                    parsedate_to_datetime(email["Date"]),
                    text,
                    html,
                    PJson(attachments),
                ],
            )
            self.db.commit(in_conn)

    def join(self, timeout: float | None = None) -> None:
        self.running = False
        return super().join(timeout)


class ImapAccountWorker(Thread):
    def __init__(self, account_id: int):
        self.db = PostgresSQL(getDB())
        self.account_id: int = account_id
        self.running = True
        self.account = self.getAccount()
        self.folder_workers: list[ImapFolderWorker] = []
        self.downlaod_fold = 0
        super().__init__()

    def run(self) -> None:
        fh = ImapFolderWorker(folder_id=1, account=self.account)
        fh.start()
        self.folder_workers.append(fh)
        while self.running:
            try:
                self.updateFolders()
            except Exception as e:
                print(e)

            time.sleep(5)

    def updateFolders(self) -> None:
        folders = self.getFolders()
        for folder in folders:
            in_conn = self.db.new_connection()
            try:
                self.db.execsql(
                    in_conn,
                    """
                INSERT INTO accounts.folders(
                account_id, folder_attrib, folder_name)
                VALUES (%s, %s, %s)
                on conflict (account_id, folder_name)
                do update set folder_attrib=EXCLUDED.folder_attrib;
                """,
                    [self.account_id, folder["attributes"], folder["name"]],
                )
            except Exception as e:
                print(e)
                traceback.print_exc(e)
            self.db.commit(in_conn)

    def getFolders(self) -> List[dict]:
        imap = imaplib.IMAP4_SSL(self.account.host)
        imap.login(self.account.user, self.account.password)
        status, mailboxes = imap.list()
        if status != "OK":
            print("Error fetching mailbox list")
            exit()
        mailbox_pattern = re.compile(r'\(([^)]+)\) "." "([^"]+)"')
        mailbox_list = []
        for mailbox in mailboxes:
            decoded_mailbox = mailbox.decode()
            match = mailbox_pattern.search(decoded_mailbox)
            if match:
                attributes, name = match.groups()
                mailbox_list.append(
                    {"attributes": attributes.replace("\\", "").split(), "name": name}
                )
        return mailbox_list

    def getAccount(self) -> ImapAccount:
        ia = ImapAccount()
        in_con = self.db.new_connection()
        data = self.db.fetchone(
            in_con,
            """SELECT 
            host, port, username, password
            FROM accounts.email_accounts
            where id = %s
            """,
            [self.account_id],
        )
        self.db.commit(in_con)
        ia.host = data[0]
        ia.user = data[2]
        ia.password = data[3]
        return ia

    def join(self, timeout: float | None = None) -> None:
        self.running = False
        super().join(timeout=timeout)


class ImapAcountHandler(Thread):
    def __init__(self) -> None:
        self.running = True
        self.accounts: list[ImapAccountWorker] = []
        self.db = PostgresSQL(getDB())
        super().__init__()

    def run(self) -> None:
        while self.running:
            in_con = self.db.new_connection()
            data = self.db.fetchall(
                in_con,
                "select id from accounts.email_accounts where email_accounts.enabled",
            )
            self.db.commit(in_con)
            for em in data:
                found = False
                for th in self.accounts:
                    if th.account_id == int(em[0]):
                        found = True
                if not found:
                    th = ImapAccountWorker(account_id=int(em[0]))
                    th.start()
                    self.accounts.append(th)
            time.sleep(10)

import os
import time
import datetime

MULTIMAIL_FILE = '/path/to/multimail.py'
MULTIMAIL_RECIPIENTS_FILE = '/path/to/recipients.txt'
MULTIMAIL_CONFIG_FILE = '/path/to/multimail.cfg'
MULTIMAIL_ATTACHMENT_FILE = '/path/to/attachment.pdf'
MULTIMAIL_LOG_FILE = '/path/to/log'

DELAY_BETWEEN_DISPATCH = 1  # seconds

SUBJECT = 'Subject'
TEXT = """
LONG TEXT
"""


with open(MULTIMAIL_RECIPIENTS_FILE, 'r') as f:
    recipients = list(addr.strip() for addr in f)

    with open(MULTIMAIL_LOG_FILE, 'a') as log:

        for recipient in recipients:
            cmd = "/usr/bin/python %s -C %s -Ss '%s' -m '%s' -r %s -a %s" % (MULTIMAIL_FILE,
                                                                             MULTIMAIL_CONFIG_FILE,
                                                                             SUBJECT,
                                                                             TEXT,
                                                                             recipient,
                                                                             MULTIMAIL_ATTACHMENT_FILE)
            now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            msg = "[%s] Sending mail to %s\n" % (now, recipient)
            print msg
            log.write(msg)

            os.system(cmd)
            time.sleep(DELAY_BETWEEN_DISPATCH)

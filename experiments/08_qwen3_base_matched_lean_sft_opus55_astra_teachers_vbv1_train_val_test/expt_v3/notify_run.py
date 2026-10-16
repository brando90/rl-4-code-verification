"""Send checked experiment mail once; preserve ambiguous interrupted delivery without retry."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from recovery_watch import write

HERE = Path(__file__).resolve().parent
TO = 'brando.science@gmail.com'
CC = ['brandojazz@gmail.com', 'brando9@stanford.edu', 'brando@vals.ai']


def durable_write(path, value):
    write(path, value)
    with path.open('rb') as stream:
        os.fsync(stream.fileno())
    fd = os.open(path.parent, os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def deliver(receipt, subject, body, sender):
    expected = {'status': 'SENT', 'subject': subject, 'body': body, 'to': TO, 'cc': CC}
    intent = receipt.with_suffix('.sending.json')
    with receipt.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if receipt.exists():
            existing = json.loads(receipt.read_text())
            assert all(existing.get(k) == v for k, v in expected.items()), 'Existing mail receipt does not match requested delivery'
            return 'PREVIOUSLY_SENT'
        assert not intent.exists(), 'Ambiguous prior delivery; inspect native evidence before any resend'
        durable_write(intent, {'status': 'SENDING', 'subject': subject, 'to': TO, 'cc': CC,
                       'body_sha256': hashlib.sha256(body.encode()).hexdigest(),
                       'started_utc': datetime.now(timezone.utc).isoformat()})
        sender(to=TO, cc=','.join(CC), subject=subject, body=body,
               from_addr='brandojazz@gmail.com', smtp_pass_file='~/keys/gmail_app_password.txt')
        durable_write(receipt, {**expected, 'body_sha256': hashlib.sha256(body.encode()).hexdigest(),
                        'all_recipients_accepted': True, 'sent_utc': datetime.now(timezone.utc).isoformat()})
        return 'SENT'


def smtp_sender():
    spec = importlib.util.spec_from_file_location('uutils_emailing', Path.home() / 'ultimate-utils/py_src/uutils/emailing.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    # The existing utility handles credentials and message construction. Check its native
    # SMTP recipient response as well: partial recipient refusal must not count as SENT.
    original = module.SMTPNotifier

    class CheckedSMTP(original):
        @contextmanager
        def _smtp_client(self):
            with super()._smtp_client() as server:
                send = server.sendmail

                def checked(*args, **kwargs):
                    refused = send(*args, **kwargs)
                    if refused:
                        raise RuntimeError('SMTP refused one or more required recipients; delivery is ambiguous')
                    return refused

                server.sendmail = checked
                yield server

    module.SMTPNotifier = CheckedSMTP
    return module.send_email_smtp


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('event', choices=['START', 'DONE']); parser.add_argument('--status', default='')
    parser.add_argument('--body-file', type=Path, required=True); args = parser.parse_args()
    subject = f'[RUN {args.event}] rl4cv-e08-v3-sft-continuation' + (f': {args.status}' if args.status else '')
    receipt = HERE / f'results/email_{args.event.lower()}_v3.json'
    print(deliver(receipt, subject, args.body_file.read_text(), smtp_sender()), subject)


if __name__ == '__main__':
    main()

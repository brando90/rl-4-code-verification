#!/usr/bin/env python3
"""Send only the watchdog's authorized completion or human-needed notice through existing mail credentials."""
import importlib.util
import json
from pathlib import Path
import sys


def main():
    message = json.load(sys.stdin)
    if message['to'] != ['brando.science@gmail.com'] or message['cc']:
        raise ValueError('notification recipient mismatch')
    path = Path.home() / 'ultimate-utils/py_src/uutils/emailing.py'
    spec = importlib.util.spec_from_file_location('e13v2_emailing', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.send_email_smtp(
        to='brando.science@gmail.com', subject=message['subject'],
        body=message['body'] + '\n\nBrando (drafted with Codex)\n',
        smtp_user='brandojazz@gmail.com', from_addr='brandojazz@gmail.com',
        smtp_pass_file=str(Path.home() / 'keys/gmail_app_password.txt'), cc='', bcc='')


if __name__ == '__main__':
    main()

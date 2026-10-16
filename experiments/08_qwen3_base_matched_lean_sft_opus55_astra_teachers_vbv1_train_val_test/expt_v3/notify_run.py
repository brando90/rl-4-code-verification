"""Send deduplicated experiment start/completion mail through the existing SMTP utility."""
import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('event', choices=['START', 'DONE'])
    parser.add_argument('--status', default='')
    parser.add_argument('--body-file', type=Path, required=True)
    args = parser.parse_args()
    receipt = HERE / f'results/email_{args.event.lower()}_v3.json'
    if receipt.exists():
        print('Previously sent:', receipt)
        return
    spec = importlib.util.spec_from_file_location('uutils_emailing', Path.home() / 'ultimate-utils/py_src/uutils/emailing.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    subject = f'[RUN {args.event}] rl4cv-e08-v3-sft-continuation' + (f': {args.status}' if args.status else '')
    body = args.body_file.read_text()
    module.send_email_smtp(to='brando.science@gmail.com', cc='brandojazz@gmail.com,brando9@stanford.edu,brando@vals.ai',
                           subject=subject, body=body, from_addr='brandojazz@gmail.com', smtp_pass_file='~/keys/gmail_app_password.txt')
    receipt.write_text(json.dumps({'status': 'SENT', 'subject': subject, 'body': body,
                                   'to': 'brando.science@gmail.com', 'cc': ['brandojazz@gmail.com','brando9@stanford.edu','brando@vals.ai'],
                                   'sent_utc': datetime.now(timezone.utc).isoformat()}, indent=2) + '\n')
    print('Sent:', subject)


if __name__ == '__main__':
    main()

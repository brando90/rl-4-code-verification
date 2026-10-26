"""Send one authorized E20 notification through uutils with explicit SMTP envelope recipients."""
import email.utils
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

BCC = ['brando.science@gmail.com', 'brando9@stanford.edu', 'brandojazz@gmail.com', 'brando@vals.ai']
ENVELOPE = []


def send_with_expanded_bcc(self, msg, to_email):
    if not self.user or not self.password or not self.from_addr:
        raise ValueError('SMTP identity is incomplete')
    assert to_email == 'brando.science@gmail.com'
    assert self.cc == ''
    bcc = [addr for _, addr in email.utils.getaddresses([self.bcc])]
    assert bcc == BCC
    recipients = [to_email] + bcc
    assert not msg.get('Bcc') and not msg.get('Cc')
    if not msg.get('Message-ID'):
        msg['Message-ID'] = email.utils.make_msgid(domain='rl4cv.e20.local')
    if not msg.get('Date'):
        msg['Date'] = email.utils.formatdate(localtime=True)
    with self._smtp_client() as server:
        refused = server.sendmail(self.from_addr, recipients, msg.as_string())
    ENVELOPE.append(dict(to=to_email, bcc=bcc, smtp_recipients=recipients,
                         message_id=msg['Message-ID'], refused=refused))
    if refused:
        raise RuntimeError('SMTP refused one or more recipients; inspect receipt before retrying')


def main():
    payload_path, receipt_path = map(Path, sys.argv[1:])
    assert not receipt_path.exists(), 'Receipt already exists; do not duplicate the message'
    payload = json.loads(payload_path.read_text())
    assert payload['subject'].startswith('[RUN DONE] rl4cv expt20')
    spec = importlib.util.spec_from_file_location('e20_uutils_emailing', '/lfs/skampere1/0/brando9/ultimate-utils/py_src/uutils/emailing.py')
    module = importlib.util.module_from_spec(spec); sys.modules[spec.name]=module; spec.loader.exec_module(module)
    module.SMTPNotifier._send = send_with_expanded_bcc
    receipt = dict(subject=payload['subject'], body=payload['body'],
                   transport='uutils.emailing.send_email_smtp; task-local envelope expansion for legacy comma-joined BCC handling',
                   status='send_attempt_started', started_at=subprocess.check_output(['date','+%m-%d-%Y %H:%M:%S %Z'],text=True).strip())
    receipt_path.write_text(json.dumps(receipt,indent=2)+'\n')
    try:
        module.send_email_smtp(to='brando.science@gmail.com', subject=payload['subject'],body=payload['body'],
                              smtp_user='brandojazz@gmail.com',from_addr='brandojazz@gmail.com',
                              smtp_pass_file='~/keys/gmail_app_password.txt',bcc=','.join(BCC))
    except Exception as error:
        receipt.update(status='send_failed_or_partial_do_not_blindly_retry', error_type=type(error).__name__,envelope=ENVELOPE)
        receipt_path.write_text(json.dumps(receipt,indent=2)+'\n'); raise
    receipt.update(status='SMTP accepted all explicit envelope recipients',envelope=ENVELOPE,
                   sent_at=subprocess.check_output(['date','+%m-%d-%Y %H:%M:%S %Z'],text=True).strip())
    receipt_path.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:receipt[k] for k in ('subject','status','sent_at','envelope')}))


if __name__ == '__main__':
    main()

"""Stream only manifest-bound regular files and verify every byte on the GX10 before publishing readiness."""
import argparse
import hashlib
import io
import json
from pathlib import Path,PurePosixPath
import sys
import tarfile
import time


def write(path,value):
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n');tmp.replace(path)


def send(manifest):
    raw=manifest.read_bytes();data=json.loads(raw)
    with tarfile.open(fileobj=sys.stdout.buffer,mode='w|') as archive:
        member=tarfile.TarInfo('transfer_manifest_'+data['identity']+'.json');member.size=len(raw);member.mode=0o644
        archive.addfile(member,io.BytesIO(raw))
        for row in data['entries']:
            source=Path(row['source']);assert source.is_file() and not source.is_symlink()
            assert source.stat().st_size==row['bytes']
            archive.add(source,arcname=row['destination'],recursive=False)


def receive(output):
    output.mkdir(parents=True,exist_ok=True);start=time.time();copied=0;done=[];last=0
    with tarfile.open(fileobj=sys.stdin.buffer,mode='r|') as archive:
        first=archive.next();assert first and first.isfile() and first.name.startswith('transfer_manifest_') and '/' not in first.name
        raw=archive.extractfile(first).read();manifest=json.loads(raw);identity=manifest['identity']
        assert identity.replace('_','').isalnum();expected={row['destination']:row for row in manifest['entries']}
        assert len(expected)==manifest['declared_files']
        (output/first.name).write_bytes(raw)
        def progress(state,current=None):
            write(output/f'transfer_progress_{identity}.json',dict(state=state,current_file=current,bytes_copied=copied,
                total_bytes=manifest['total_bytes'],completed_files=len(done),declared_files=len(expected),
                elapsed_seconds=time.time()-start,observed_unix=time.time()))
        progress('RECEIVING')
        while True:
            member=archive.next()
            if member is None:break
            assert member.isfile() and member.name in expected,member.name
            relative=PurePosixPath(member.name);assert not relative.is_absolute() and '..' not in relative.parts
            row=expected[member.name];assert member.size==row['bytes'] and member.name not in done
            target=output/member.name;target.parent.mkdir(parents=True,exist_ok=True)
            assert not target.is_symlink()
            temporary=target.with_name(target.name+'.transfer-partial');h=hashlib.sha256();n=0
            source=archive.extractfile(member)
            with temporary.open('wb') as dest:
                for block in iter(lambda:source.read(8<<20),b''):
                    dest.write(block);h.update(block);n+=len(block);copied+=len(block)
                    if time.time()-last>=5:progress('RECEIVING',member.name);last=time.time()
            assert n==row['bytes'] and h.hexdigest()==row['sha256'],member.name
            temporary.replace(target);done.append(member.name);progress('RECEIVING',member.name)
        assert set(done)==set(expected) and copied==manifest['total_bytes']
    progress('DONE')
    result=dict(state='READY',identity=identity,manifest_sha256=hashlib.sha256(raw).hexdigest(),
        files=len(done),bytes_verified=copied,elapsed_seconds=time.time()-start,observed_unix=time.time(),
        all_files_hash_checked=True,model_or_training_launched=False)
    write(output/f'transfer_completion_{identity}.json',result);print(json.dumps(result,sort_keys=True))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['send','receive']);p.add_argument('--manifest',type=Path);p.add_argument('--output',type=Path)
    a=p.parse_args();send(a.manifest) if a.action=='send' else receive(a.output)

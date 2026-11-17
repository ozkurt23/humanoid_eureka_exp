#!/usr/bin/env python3
"""Verify release segments or restore the archived experiment into an empty directory."""
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tarfile

MIB = 1024 * 1024

def validate_parts(folder):
    parts = []
    for index, line in enumerate((folder / 'PARCALAR.sha256').read_text().splitlines()):
        expected, name = line.split()
        if name != f'proje.tar.zst.part-{index:03d}' or not re.fullmatch('[a-f0-9]{64}',expected):
            raise ValueError(f'Geçersiz parça kaydı {index}')
        path = folder / name
        with path.open('rb') as stream:
            actual = hashlib.file_digest(stream, 'sha256').hexdigest()
        if expected != actual:
            raise ValueError(f'Parça doğrulanamadı {name}')
        parts.append(path)
    if not parts:
        raise ValueError('Parça listesi boş')
    return parts

def checked_name(name):
    path = PurePosixPath(name)
    if (not path.parts or path.is_absolute() or '..' in path.parts
            or str(path) != name.rstrip('/')):
        raise ValueError(f'Geçersiz yol {name}')
    return path

def copy_payload(src, dest):
    with src.open('rb') as a, dest.open('xb') as b:
        try:
            fcntl.ioctl(b.fileno(), 0x40049409, a.fileno())  # Linux FICLONE
        except OSError:
            shutil.copyfileobj(a, b, 4*MIB)

def unpack(parts, dest):
    # All restored paths are rooted in a new or previously empty directory.
    if dest is not None:
        dest = dest.resolve()
        dest.mkdir(parents=True, exist_ok=True)
        if any(dest.iterdir()):
            raise ValueError('Hedef klasör boş olmalı')
    observed = {}
    cat = subprocess.Popen(['cat', '--', *map(str,parts)], stdout=subprocess.PIPE)
    dec = subprocess.Popen(['zstd','-dc','--long=27'],stdin=cat.stdout,stdout=subprocess.PIPE)
    cat.stdout.close()
    manifest = None
    pending_symlinks = []
    try:
        with tarfile.open(fileobj=dec.stdout,mode='r|',bufsize=MIB) as archive:
            for item in archive:
                path = checked_name(item.name)
                for parent in path.parents:
                    if observed.get(str(parent), (None,))[0] == 'symlink':
                        raise ValueError(f'Bağ altına yazılamaz {path}')
                if item.name == 'ENVANTER.jsonl':
                    if manifest is not None or not item.isreg():
                        raise ValueError('Çift envanter')
                    raw = archive.extractfile(item).read()
                    manifest = [json.loads(line) for line in raw.splitlines()]
                    if dest:
                        with (dest / item.name).open('xb') as stream:
                            stream.write(raw)
                    continue
                if item.name in observed:
                    raise ValueError(f'Çift yol {item.name}')
                target = dest / path if dest else None
                if target:
                    if not target.parent.resolve().is_relative_to(dest):
                        raise ValueError(f'Dış hedef {path}')
                    target.parent.mkdir(exist_ok=True,parents=True)
                if item.isdir():
                    observed[item.name]=('dir',)
                    if target:target.mkdir(exist_ok=True)
                elif item.issym():
                    observed[item.name]=('symlink',item.linkname)
                    if target:pending_symlinks.append((target, item.linkname))
                elif item.islnk():
                    checked_name(item.linkname)
                    other = observed[item.linkname]
                    if other[0]!='file':
                        raise ValueError(f'Dosya bağı geçersiz {item.name}')
                    observed[item.name] = other
                    if target:copy_payload(dest / item.linkname, target)
                elif item.isreg():
                    digest = hashlib.sha256()
                    with contextlib.ExitStack() as stack:
                        src=stack.enter_context(archive.extractfile(item))
                        writer=stack.enter_context(target.open('xb')) if target else None
                        for block in iter(lambda:src.read(MIB),b''):
                            digest.update(block)
                            if writer:writer.write(block)
                    observed[item.name]=('file',item.size,digest.hexdigest())
                else:
                    raise ValueError(f'Desteklenmeyen TAR girdisi {path}')
        while dec.stdout.read(MIB):pass
        if dec.wait() or cat.wait():raise RuntimeError('zstd akışı tamamlanamadı')
    finally:
        dec.stdout.close()
        for proc in [cat,dec]:
            if proc.poll() is None:proc.kill()
            proc.wait()
    if manifest is None or len(manifest)!=len(observed):raise ValueError('Envanter eşleşmedi')
    for row in manifest:
        kind = row['kind']
        expected = {'file':lambda:(kind,row['size'],row['sha256']),
                    'symlink':lambda:(kind,row['target']), 'dir':lambda:(kind,)}[kind]()
        if observed.get(row['path']) != expected:raise ValueError(f'İçerik eşleşmedi {row["path"]}')
    if dest:
        for target, linkname in pending_symlinks:
            target.symlink_to(linkname)
        for row in manifest:
            if row.get('hardlink'):
                a=dest / checked_name(row['hardlink'])
                b=dest / checked_name(row['path'])
                if observed[row['path']]!=observed[row['hardlink']]:raise ValueError(row['path'])
                b.unlink()
                os.link(a,b)
        for row in reversed(manifest):
            target=dest / row['path']
            if row['kind']!='symlink':target.chmod(row['mode'])
            os.utime(target, times=(row['mtime'],row['mtime']),follow_symlinks=False)
    print(f'{len(parts)} parça ve {len(manifest)} envanter kaydı doğrulandı.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('parca_klasoru',type=Path)
    parser.add_argument('--ac',type=Path,metavar='BOS_KLASOR',help='Tüm dosyaları belirtilen boş klasöre aç')
    args=parser.parse_args()
    unpack(validate_parts(args.parca_klasoru),args.ac)

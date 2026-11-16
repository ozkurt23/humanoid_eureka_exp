"""Download private release assets by name and verify them against the committed index."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

REPO = 'ozkurt23/humanoid-dual-pen-recovery'
TAG = 'v1.0.0'


def gh(*args):
    return subprocess.check_output(['gh', 'api', *args], text=True)


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    dest = parser.parse_args().folder.resolve()
    dest.mkdir(parents=True, exist_ok=True)
    index = Path(__file__).with_name('PARCALAR.sha256')
    release = json.loads(gh(f'repos/{REPO}/releases/tags/{TAG}'))
    records = gh('--paginate', f'repos/{REPO}/releases/{release["id"]}/assets?per_page=100',
                 '--jq', '.[] | @json')
    assets = {a['name']: a for a in map(json.loads, records.splitlines())}
    for line in index.read_text().splitlines():
        expected, name = line.split()
        asset = assets[name]
        final = dest / name
        if final.is_file() and digest(final) == expected:
            continue
        tmp = final.with_suffix('.tmp')
        print(name, flush=True)
        with tmp.open('wb') as stream:
            subprocess.run(['gh', 'api', '-H', 'Accept: application/octet-stream',
                            f'repos/{REPO}/releases/assets/{asset["id"]}'],
                           stdout=stream, check=True)
        if digest(tmp) != expected:
            raise ValueError(f'Dosya özeti eşleşmedi: {name}')
        tmp.replace(final)
    (dest / index.name).write_bytes(index.read_bytes())


if __name__ == '__main__':
    main()

"""Download release assets by name and verify them against the committed index."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

REPO = 'ozkurt23/humanoid_eureka_exp'
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
        print(name, flush=True)
        with tempfile.NamedTemporaryFile(dir=dest, prefix='.' + name + '.', delete=False) as stream:
            tmp = Path(stream.name)
            try:
                subprocess.run(['gh', 'api', '-H', 'Accept: application/octet-stream',
                                f'repos/{REPO}/releases/assets/{asset["id"]}'],
                               stdout=stream, check=True)
                stream.flush()
                if digest(tmp) != expected:
                    raise ValueError(f'Dosya özeti eşleşmedi: {name}')
                tmp.replace(final)
            finally:
                tmp.unlink(missing_ok=True)
    with tempfile.NamedTemporaryFile(dir=dest, prefix='.manifest-', delete=False) as stream:
        tmp = Path(stream.name)
        try:
            stream.write(index.read_bytes())
            stream.flush()
            tmp.replace(dest / index.name)
        finally:
            tmp.unlink(missing_ok=True)


if __name__ == '__main__':
    main()

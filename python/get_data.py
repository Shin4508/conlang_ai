"""Explicitly download frequency word lists. Importing this module performs no I/O."""
import argparse
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/{0}/{0}_50k.txt'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--languages', nargs='+', choices=['ja', 'ru', 'ar', 'fi', 'hu'], default=['ru', 'ar', 'fi', 'hu'])
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'data/raw')
    parser.add_argument('--limit', type=int, default=5000)
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    if args.limit < 1:
        parser.error('--limit must be positive')
    try:
        pending = {}
        for lang in args.languages:
            path = args.output_dir / f'{lang}.txt'
            if path.exists() and not args.overwrite:
                raise ValueError(f'{path} exists; use --overwrite to replace it')
            with urllib.request.urlopen(BASE_URL.format(lang), timeout=30) as response:
                words = [line.rsplit(maxsplit=1)[0] for line in response.read().decode('utf-8').splitlines() if line.strip()][:args.limit]
            if not words:
                raise ValueError(f'Empty download for {lang}')
            pending[path] = '\n'.join(words) + '\n'
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for path, content in pending.items():
            path.write_text(content, encoding='utf-8')
            print(f'Saved {path}')
    except (OSError, ValueError) as exc:
        parser.exit(1, f'Error: {exc}\n')


if __name__ == '__main__':
    main()

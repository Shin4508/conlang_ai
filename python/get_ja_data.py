"""Extract Japanese readings from all five local JLPT CSV files, without pandas."""
import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def extract_readings(paths):
    words = []
    for path in paths:
        with Path(path).open(encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            if 'reading' not in (reader.fieldnames or []):
                raise ValueError(f'{path}: missing reading column')
            words.extend(row['reading'].strip() for row in reader if row.get('reading', '').strip())
    if not words:
        raise ValueError('No readings found')
    return list(dict.fromkeys(words))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=ROOT / 'data')
    parser.add_argument('--output', type=Path, default=ROOT / 'data/raw/ja_readings.txt')
    args = parser.parse_args()
    try:
        words = extract_readings([args.data_dir / f'n{i}.csv' for i in range(1, 6)])
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text('\n'.join(words) + '\n', encoding='utf-8')
        print(f'Saved {len(words)} readings to {args.output}')
    except (OSError, ValueError) as exc:
        parser.exit(1, f'Error: {exc}\n')


if __name__ == '__main__':
    main()

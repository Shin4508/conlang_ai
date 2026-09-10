"""Report local data quality without modifying source files or loading ML packages."""
import argparse
import csv
import json
from pathlib import Path
import unicodedata
try:
    from .preprocess import suspicious_characters
except ImportError:
    from preprocess import suspicious_characters

ROOT = Path(__file__).resolve().parents[1]


def audit(root):
    report = {}
    paths = sorted((root / 'data').rglob('*.txt')) + [root / 'generated_10k.txt']
    for path in paths:
        if not path.exists():
            continue
        lines = path.read_text(encoding='utf-8').splitlines()
        words = [unicodedata.normalize('NFC', line.strip()) for line in lines if line.strip()]
        item = {'lines': len(lines), 'blank_lines': len(lines)-len(words),
                'unique_entries': len(set(words)), 'duplicate_entries': len(words)-len(set(words)),
                'punctuation_only_entries': sum(not any(unicodedata.category(c)[0] == 'L' for c in w) for w in words)}
        if 'processed' in path.parts or path.name == 'generated_10k.txt':
            item['entries_with_suspected_unconverted_script'] = sum(bool(suspicious_characters(w)) for w in words)
            item['suspected_characters'] = suspicious_characters(''.join(words))
        report[str(path.relative_to(root))] = item
    for path in sorted((root / 'data').glob('*.csv')):
        with path.open(encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            report[str(path.relative_to(root))] = {'records': len(rows), 'columns': reader.fieldnames,
                'missing_readings': sum(not row.get('reading', '').strip() for row in rows)}
    for path in sorted((root / 'klej_nkjp-ner').glob('*.tsv')):
        with path.open(encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f, delimiter='\t')
            rows = list(reader)
            report[str(path.relative_to(root))] = {'records': len(rows), 'columns': reader.fieldnames}
    path = root / 'vocab.json'
    if path.exists():
        vocab = json.loads(path.read_text(encoding='utf-8'))
        report['vocab.json'] = {'tokens': len(vocab['ipa2id']), 'context_length': vocab['block_size'],
            'suspected_characters': suspicious_characters(''.join(vocab['ipa2id'])),
            'round_trip_valid': all(vocab['id2ipa'].get(str(i)) == c for c, i in vocab['ipa2id'].items())}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    content = json.dumps(audit(args.root), ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding='utf-8')
    else:
        print(content, end='')


if __name__ == '__main__':
    main()

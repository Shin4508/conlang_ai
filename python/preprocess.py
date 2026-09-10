"""Convert raw word lists to IPA while retaining language labels and IPA marks."""
import argparse
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = {'ar': 'ara-Arab', 'fi': 'fin-Latn', 'hu': 'hun-Latn', 'ru': 'rus-Cyrl', 'ja': 'jpn-Jpan'}


def clean_text(text):
    text = re.sub(r'https?://\S+|www\.\S+', '', unicodedata.normalize('NFC', text))
    # Reject digits rather than turning an alphanumeric entry into a different word.
    if any(c.isdigit() for c in text):
        return ''
    return ''.join(c for c in text if unicodedata.category(c)[0] in 'LM' or c.isspace() or c in "'-").strip()


def suspicious_characters(text):
    """Conservative contamination check, not a complete IPA validator."""
    return sorted({c for c in text if any(s in unicodedata.name(c, '') for s in
                  ('ARABIC', 'CYRILLIC', 'HIRAGANA', 'KATAKANA', 'CJK', 'DIGIT'))})


def convert_to_ipa(file_path, converter):
    result = []
    for number, line in enumerate(Path(file_path).read_text(encoding='utf-8').splitlines(), 1):
        word = clean_text(line)
        if not word:
            continue
        try:
            ipa = unicodedata.normalize('NFC', converter.transliterate(word).strip())
        except Exception as exc:
            raise ValueError(f'{file_path}:{number}: conversion failed for {word!r}: {exc}') from exc
        if not ipa:
            raise ValueError(f'{file_path}:{number}: conversion returned no pronunciation')
        if suspicious_characters(ipa):
            raise ValueError(f'{file_path}:{number}: unconverted characters in {ipa!r}; review this source entry')
        result.extend(ipa.split())
    if not result:
        raise ValueError(f'No pronunciations in {file_path}')
    return list(dict.fromkeys(result))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--languages', nargs='+', choices=LANGUAGES, default=['ar', 'fi', 'hu', 'ru'])
    parser.add_argument('--raw-dir', type=Path, default=ROOT / 'data/raw')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'data/processed')
    args = parser.parse_args(argv)
    try:
        import epitran
        # Finish all conversions before replacing any output files.
        corpora = {lang: convert_to_ipa(args.raw_dir / f'{lang}.txt', epitran.Epitran(LANGUAGES[lang])) for lang in args.languages}
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for lang, words in corpora.items():
            (args.output_dir / f'ipa_{lang}.txt').write_text('\n'.join(words) + '\n', encoding='utf-8')
            print(f'{lang}: {len(words)} unique pronunciations')
        (args.output_dir / 'mixed_ipa_corpus.txt').write_text('\n'.join(w for words in corpora.values() for w in words) + '\n', encoding='utf-8')
    except (ImportError, OSError, ValueError) as exc:
        parser.exit(1, f'Error: {exc}\nInstall Epitran for conversion; review source entries if conversion fails.\n')


if __name__ == '__main__':
    main()

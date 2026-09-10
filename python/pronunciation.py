"""Reproducible, rule-based pronunciation design. Uses only Python's standard library."""
import argparse
import csv
import json
from pathlib import Path
import random
import unicodedata

ROOT = Path(__file__).resolve().parents[1]


def load_profile(path):
    profile = json.loads(Path(path).read_text(encoding='utf-8'))
    for group in ('consonants', 'vowels'):
        sounds = profile.get(group)
        if not isinstance(sounds, dict) or not sounds:
            raise ValueError(f'{group} must map IPA sounds to spellings')
        if any(not isinstance(k, str) or not k or not isinstance(v, str) or not v
               or any(c.isspace() for c in k + v) for k, v in sounds.items()):
            raise ValueError('Sounds and spellings must be nonempty strings without spaces')
    if set(profile['consonants']) & set(profile['vowels']):
        raise ValueError('Consonants and vowels must be distinct')
    templates = profile.get('syllables', [])
    if not templates or any(not isinstance(t, str) or 'V' not in t or set(t) - set('CV') for t in templates):
        raise ValueError('Syllables must contain V and use only C and V')
    bounds = profile.get('syllable_count', [])
    if len(bounds) != 2 or any(type(n) is not int for n in bounds) or not 1 <= bounds[0] <= bounds[1] <= 10:
        raise ValueError('syllable_count must be [minimum, maximum], between 1 and 10')
    if profile.get('stress') not in ('initial', 'penultimate', 'final', 'none'):
        raise ValueError('stress must be initial, penultimate, final, or none')
    forbidden = profile.get('forbidden_sequences', [])
    if not isinstance(forbidden, list) or any(not isinstance(s, str) or not s for s in forbidden):
        raise ValueError('forbidden_sequences must be a list of nonempty IPA strings')
    return profile


def generate(profile, count=20, seed=42):
    if count < 1:
        raise ValueError('count must be positive')
    rng = random.Random(seed)
    rows, seen_ipa, seen_spelling = [], set(), set()
    for _ in range(max(1000, count * 100)):
        syllables, spellings = [], []
        for _ in range(rng.randint(*profile['syllable_count'])):
            sounds = [rng.choice(list(profile['consonants' if c == 'C' else 'vowels']))
                      for c in rng.choice(profile['syllables'])]
            syllables.append(''.join(sounds))
            spellings.append(''.join(profile['consonants'].get(s, profile['vowels'].get(s)) for s in sounds))
        bare = unicodedata.normalize('NFC', ''.join(syllables))
        spelling = ''.join(spellings)
        if bare in seen_ipa or spelling in seen_spelling or any(s in bare for s in profile.get('forbidden_sequences', [])):
            continue
        stress = {'initial': 0, 'penultimate': max(0, len(syllables)-2), 'final': len(syllables)-1, 'none': -1}[profile['stress']]
        ipa = '.'.join(('ˈ' if i == stress else '') + s for i, s in enumerate(syllables))
        rows.append({'spelling': spelling, 'ipa': ipa, 'syllables': '-'.join(spellings), 'meaning': '', 'actor_notes': ''})
        seen_ipa.add(bare)
        seen_spelling.add(spelling)
        if len(rows) == count:
            return rows
    raise ValueError(f'Only {len(rows)} unique words found; reduce count or broaden the profile')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', type=Path, default=ROOT / 'profiles/example.json')
    parser.add_argument('--count', type=int, default=20)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        rows = generate(load_profile(args.profile), args.count, args.seed)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open('w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            print(f'Saved {len(rows)} pronunciations to {args.output}')
        else:
            for row in rows:
                print(f"{row['spelling']}\t/{row['ipa']}/\t{row['syllables']}")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f'Error: {exc}\n')


if __name__ == '__main__':
    main()

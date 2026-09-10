# Fictional-language pronunciation tools

Python tools for designing consistent invented pronunciations for film and games.
The project includes a rule-based pronunciation designer, an experimental ONNX
word generator, source word lists, and Transformer training notebooks.

## Start here: design a pronunciation system

Requires Python 3.10 or newer; no extra packages needed:

```bash
python3 python/pronunciation.py --count 20 --seed 42
python3 python/pronunciation.py --count 50 --output reports/my_lexicon.csv
```

Edit `profiles/example.json` to define:

- Consonants and vowels, each mapped from an IPA sound to its spelling.
- Syllable templates: C means consonant, V means vowel. Repeated templates increase their sampling frequency.
- Minimum and maximum syllable counts.
- Initial, penultimate, final, or no stress.
- Forbidden IPA sequences, checked across syllable boundaries too.

The CSV contains spelling, IPA, syllable breaks, and blank meaning/actor-notes
fields. A fixed seed reproduces output. Generation rejects duplicate spellings
and pronunciations within a batch and stops with an error if it cannot fill the
requested count. It does not check novelty against real languages or previous
exports. IPA dots mark syllable boundaries; ˈ marks primary stress.

`reports/example_lexicon.csv` contains 50 example candidates. The example profile
is a starting point, not a recreation of any existing fictional language.
There is no audio synthesis, grammar, automatic translation, or actor recording
interface yet. Spellings concatenate the configured mappings; they are not an
English pronunciation guide or guaranteed to be uniquely decodable.

## Run the existing learned model in Python

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-model.txt
.venv/bin/python python/model.py --count 20 --seed 42
```

This uses `conlang_model.onnx` and its matching `vocab.json`. Prompts must use the
existing vocabulary. Sampling is numerically stable and bounded by `--max-tokens`.
The model proposes character strings without enforcing the pronunciation profile;
review its output. Its vocabulary contains suspected unconverted source-script
characters. Do not change token IDs without re-exporting the matching model.

The old `python/model.py` ran training immediately and contained unbounded
sampling loops. It is now an inference CLI; the training experiments remain in
`model.ipynb` and `model_v2.ipynb`. The browser prototype remains available via
`python3 -m http.server 8000`, then `http://localhost:8000`. It loads ONNX Runtime
from a CDN and needs internet access.

## Inspect and prepare data

```bash
python3 python/audit_data.py --output reports/data_audit.json
python3 python/get_ja_data.py
```

The Japanese extractor reads all five `data/n1.csv` through `data/n5.csv` files,
uses the reading column, and writes `data/raw/ja_readings.txt`, preserving the
existing `ja.txt`. Review annotations and alternative readings before using it
as a Japanese source list. The shared converter expects `ja.txt`; put a reviewed
copy in a separate raw directory and pass `--raw-dir` for Japanese conversion.

Optional transliteration and training dependencies:

```bash
.venv/bin/python -m pip install -r requirements-training.txt
.venv/bin/python python/preprocess.py --languages ar fi hu ru
.venv/bin/jupyter notebook model_v2.ipynb
```

Run notebooks from the repository root. Preprocessing retains Unicode combining
marks, writes one word per line to per-language IPA files and a combined file,
and reports conversion failures instead of silently skipping them. It refuses
suspected unconverted script characters. This is a contamination check, not a
complete IPA validator. Existing dirty sources can therefore stop conversion
until reviewed. Epitran language support and conversion accuracy need validation
for each selected language, especially Japanese readings and Arabic vowels.

`get_data.py` downloads only when explicitly run, uses consistent language-code
filenames, and refuses replacement unless `--overwrite` is given. No download is
needed for the local data already present. Local `data/` is gitignored, so a fresh
checkout does not include those files.

The v2 notebook blends Arabic, Finnish, Hungarian, and Russian language embeddings.
It is experimental: it has no held-out evaluation or saved checkpoint/export
pipeline. Its language-conditioned architecture is distinct from the existing
browser model. Embedding weights are not guaranteed percentages of audible
features. Notebook path, EOS truncation, and invalid sampling-weight issues have
been fixed; full training still needs evaluation.

## Validation and project notes

```bash
python3 -m unittest discover -s tests -v
node --test tests/generator.test.mjs
```

See `reports/PROJECT_ANALYSIS.txt` for findings and `USER_ACTIONS.txt` for creative
choices and source materials needed next. Source corpora and the existing model
have been preserved.

# IPA Conlang Generator

An experiment in generating invented words by learning and blending the sound patterns of Arabic, Finnish, Hungarian, and Russian.

The project converts source-language word lists to the International Phonetic Alphabet (IPA), trains a language-conditioned character-level Transformer, and samples either from one language or from a weighted mixture of languages. The generated strings are pronunciations rather than words with assigned spelling or meaning.

## How it works

The workflow in [`model_v2.ipynb`](model_v2.ipynb) is:

1. Read one word per line from each raw corpus.
2. Remove URLs and digits, then transliterate each entry to IPA with Epitran.
3. Build a character vocabulary from the combined IPA data, plus `<PAD>`, `<BOS>`, and `<EOS>` tokens.
4. Encode every pronunciation as a next-character prediction sample.
5. Train a causal Transformer conditioned on the source language.
6. Generate a word from one language embedding or a normalized blend of several language embeddings.

Because language embeddings can be mixed before generation, the model can sample pronunciations that lie between the learned phonetic patterns of its training languages.

## Data

The model uses the following files from `data/raw/`:

| Code | Language | File | Entries |
| --- | --- | --- | ---: |
| `ar` | Arabic | `ar.txt` | 5,000 |
| `fi` | Finnish | `fi.txt` | 5,000 |
| `hu` | Hungarian | `hu.txt` | 5,000 |
| `ru` | Russian | `ru.txt` | 5,000 |

Each file is UTF-8 text with one entry per line. `data/raw/ja.txt` is not used by the v2 notebook or described here.

## Model

`CharTransformer` is a compact decoder-style language model built from PyTorch's Transformer encoder components with a causal attention mask.

| Setting | Value |
| --- | ---: |
| Context length | 24 IPA characters |
| Embedding size | 64 |
| Attention heads | 4 |
| Transformer layers | 2 |
| Feed-forward size | 128 |
| Batch size | 32 |
| Optimizer | AdamW |
| Learning rate | `1e-3` |
| Training iterations | 3,000 |

Token, position, and language embeddings are added together before the Transformer. Training uses cross-entropy loss for next-character prediction and ignores padding tokens.

## Requirements

- Python 3
- Jupyter Notebook or JupyterLab
- PyTorch
- Epitran

Install the Python dependencies:

```bash
python -m pip install jupyter torch epitran
```

## Running the notebook

Open `model_v2.ipynb` and run its cells in order:

```bash
jupyter notebook model_v2.ipynb
```

The notebook currently defines its inputs as `ar.txt`, `fi.txt`, `hu.txt`, and `ru.txt`. Before running the data-loading cell from the repository root, change those values to:

```python
lang_files = {
    "ar": "data/raw/ar.txt",
    "fi": "data/raw/fi.txt",
    "hu": "data/raw/hu.txt",
    "ru": "data/raw/ru.txt",
}
```

Training happens in memory. The notebook does not save a checkpoint, so the generation cells must be run in the same session after training.

## Generating pronunciations

Generate from one learned language profile:

```python
generate_word("fi", temperature=0.8, max_len=20)
```

Generate from a blend:

```python
generate_mixed({
    "ar": 0.50,
    "fi": 0.25,
    "ru": 0.25,
})
```

Mixture values are normalized automatically, so they may be given as proportions or arbitrary positive weights. Increasing `temperature` makes sampling more varied; decreasing it makes sampling more conservative. Generation begins with `<BOS>`, stops at `<EOS>` or `max_len`, and prevents `<PAD>` and `<BOS>` from being sampled.

## Current language
Arabic  
Russian  
Finnish  
Hungarian

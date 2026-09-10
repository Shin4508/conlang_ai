"""Generate with the existing ONNX model. Training experiments remain in the notebooks."""
import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def generate(prompt, count=20, temperature=0.8, seed=42, max_tokens=4096,
             model_path=ROOT / 'conlang_model.onnx', vocab_path=ROOT / 'vocab.json'):
    if not math.isfinite(temperature) or temperature <= 0:
        raise ValueError('temperature must be finite and positive')
    if count < 1 or max_tokens < 1:
        raise ValueError('count and max_tokens must be positive')
    vocab = json.loads(Path(vocab_path).read_text(encoding='utf-8'))
    ipa2id, id2ipa = vocab['ipa2id'], vocab['id2ipa']
    if not prompt or any(c not in ipa2id for c in prompt):
        raise ValueError('Prompt must be nonempty and contain only characters in vocab.json')
    if vocab['block_size'] < 1:
        raise ValueError('Invalid context length in vocabulary')
    import numpy as np
    import onnxruntime as ort
    rng = np.random.default_rng(seed)
    session = ort.InferenceSession(str(model_path), providers=['CPUExecutionProvider'])
    context = [ipa2id[c] for c in prompt]
    rows, word, seen = [], [], set()
    for _ in range(max_tokens):
        ids = np.array([context[-vocab['block_size']:]], dtype=np.int64)
        logits = session.run(None, {session.get_inputs()[0].name: ids})[0]
        scores = np.asarray(logits[0, -1], dtype=np.float64)
        if not np.isfinite(scores).all():
            raise ValueError('Model returned nonfinite logits')
        scores = (scores - scores.max()) / temperature
        probabilities = np.exp(scores)
        probabilities /= probabilities.sum()
        token = int(rng.choice(len(probabilities), p=probabilities))
        context.append(token)
        char = id2ipa[str(token)]
        if char.isspace():
            candidate = ''.join(word)
            word = []
            if candidate and candidate not in seen:
                rows.append(candidate)
                seen.add(candidate)
                if len(rows) == count:
                    return rows
        else:
            word.append(char)
    raise ValueError(f'Token limit reached with {len(rows)}/{count} complete unique words; increase --max-tokens')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prompt', default='kaɾa\n')
    parser.add_argument('--count', type=int, default=20)
    parser.add_argument('--temperature', type=float, default=0.8)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--max-tokens', type=int, default=4096)
    args = parser.parse_args()
    try:
        print('\n'.join(generate(args.prompt, args.count, args.temperature, args.seed, args.max_tokens)))
    except ImportError:
        parser.exit(1, 'Install model dependencies: python3 -m pip install -r requirements-model.txt\n')
    except (OSError, ValueError) as exc:
        parser.exit(1, f'Error: {exc}\n')


if __name__ == '__main__':
    main()

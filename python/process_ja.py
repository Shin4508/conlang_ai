"""Convert the Japanese word list using the shared preprocessing pipeline."""
try:
    from .preprocess import main
except ImportError:
    from preprocess import main

if __name__ == '__main__':
    main(['--languages', 'ja'])

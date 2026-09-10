"""Compatibility entry point for the shared preprocessing pipeline."""
try:
    from .preprocess import main, clean_text, convert_to_ipa
except ImportError:
    from preprocess import main, clean_text, convert_to_ipa

convert_file_to_ipa_lines = convert_to_ipa

if __name__ == '__main__':
    main()

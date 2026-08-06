import os
import epitran
import re

converter = epitran.Epitran("jpn-Jpan")


def clean_text(text):
    cleaned_text = re.sub(r"\(.*?\)|（.*?）", "", text)
    cleaned_text = re.sub(r"~", "", text)
    return cleaned_text


def convert_to_ipa(file_path, converter):
    if not os.path.exists(file_path):
        print(f"[警告] ファイルが見つかりません: {file_path}")
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    ipa_lines = []
    for line in lines:
        cleaned = clean_text(line).strip()
        ipa_word = converter.transliterate(cleaned)
        ipa_lines.append(ipa_word)

    return ipa_lines


RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"

lang_files = "ja.txt"

file_path = os.path.join(RAW_DIR, lang_files)
ipa_lines = convert_to_ipa(file_path, converter)
all_lines = []
output_path = os.path.join(PROCESSED_DIR, "ipa_ja.txt")
with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(ipa_lines) + "\n")

import os
import epitran
import re

print("Epitran loading")
converters = {
    "ja": epitran.Epitran("jpn-Jpan"),
    "ru": epitran.Epitran("rus-Cyrl"),
    "ar": epitran.Epitran("ara-Arab"),
    "fi": epitran.Epitran("fin-Latn"),
    "hu": epitran.Epitran("hun-Latn"),
}


def clean_text(text):
    text = re.sub(r"https?://\S+|www\.\S+", "", text)
    text = re.sub(r"\d+", "", text)
    text = re.sub(r"[^\w\s\.,\?!/]", "", text)
    return text


def convert_to_ipa(file_path, converter):
    if not os.path.exists(file_path):
        print(f"[警告] ファイルが見つかりません: {file_path}")
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    ipa_lines = []
    for line in lines:
        cleaned = clean_text(line)
        words = cleaned.strip().split()
        if not words:
            continue

        ipa_words = []
        for word in words:
            try:
                ipa_word = converter.transliterate(word)
                ipa_word = clean_text(ipa_word)
                if ipa_word:
                    ipa_words.append(ipa_word)
            except Exception:
                continue

        if ipa_words:
            ipa_lines.append(" / ".join(ipa_words))

    return ipa_lines


def main():
    RAW_DIR = "data/raw"
    PROCESSED_DIR = "data/processed"

    os.makedirs(PROCESSED_DIR, exist_ok=True)
    lang_files = {
        "ja": "ja.txt",
        "ru": "ru.txt",
        "ar": "ar.txt",
        "fi": "fi.txt",
        "hu": "hu.txt",
    }

    all_dataset_lines = []

    for lang, file_name in lang_files.items():
        file_path = os.path.join(RAW_DIR, file_name)
        ipa_lines = convert_to_ipa(file_path, converters[lang])

        all_dataset_lines.extend(ipa_lines)

    output_path = os.path.join(PROCESSED_DIR, "mixed_ipa_corpus.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(all_dataset_lines))

    print(f"🎉 前処理完了！ 学習データがここに保存されました: {output_path}")


if __name__ == "__main__":
    main()

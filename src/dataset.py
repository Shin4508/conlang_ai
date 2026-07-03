import os
import random
import re
import epitran

# ==========================================
# 1. 各言語のEpitran変換器のロード
# ==========================================
print("Epitranの多言語モデルをロード中...")
converters = {
    "ja": epitran.Epitran('jpn-Jpan'),  # 日本語（フラット・母音）
    "ru": epitran.Epitran('rus-Cyrl'),  # ロシア語（重厚子音クラスタ）
    "ar": epitran.Epitran('ara-Arab'),  # アラビア語（喉奥摩擦）
    "vi": epitran.Epitran('vie-Latn'),  # ベトナム語（縦の声調・トーン）
    "xo": epitran.Epitran('xho-Latn')   # コサ語（アフリカの吸着ノイズ）
}

def clean_text(text):
    """生テキストから不要な数字や記号、URLなどを綺麗に削る"""
    text = re.sub(r'https?://\S+|www\.\S+', '', text) # URL削除
    text = re.sub(r'\d+', '', text)                  # 数字削除
    # アルファベット、アラビア文字、キリル文字、漢字ひらがな、基本的な句読点以外を除去
    # (コサ語やベトナム語の特殊なラテン文字も通すようにしています)
    text = re.sub(r'[^\w\s\.,\?!/]', '', text)
    return text

def convert_file_to_ipa_lines(file_path, converter):
    """ファイルを読み込み、1行(フレーズ)ごとにスラッシュ区切りのIPAに変換する"""
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
                if ipa_word:
                    ipa_words.append(ipa_word)
            except Exception:
                continue
        
        # 単語の区切りをハッキリさせるため、スペース＋スラッシュ＋スペースで結合
        if ipa_words:
            ipa_lines.append(" / ".join(ipa_words))
            
    return ipa_lines

# ==========================================
# 2. メイン実行フェーズ
# ==========================================
def main():
    # パス設定（さっき決めたフォルダ構造に準拠）
    RAW_DIR = "data/raw"
    PROCESSED_DIR = "data/processed"
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    # 各言語のファイル名マッピング
    lang_files = {
        "ja": "japanese.txt",
        "ru": "russian.txt",
        "ar": "arabic.txt",
        "vi": "vietnamese.txt",
        "xo": "xhosa.txt"
    }

    all_dataset_lines = []

    for lang, filename in lang_files.items():
        file_path = os.path.join(RAW_DIR, filename)
        print(f"[{lang.upper()}] データをIPAに変換中...")
        
        ipa_lines = convert_file_to_ipa_lines(file_path, converters[lang])
        print(f" ──> {len(ipa_lines)} 行のIPAテキストを生成しました。")
        
        all_dataset_lines.extend(ipa_lines)

    # ==========================================
    # 3. シャッフル ＆ 結合
    # ==========================================
    # 言語の境界線をなくし、確率的に滑らかにモーフィングさせるためにシャッフル
    print("全データをシャッフルして1つのコーパスに結合しています...")
    random.shuffle(all_dataset_lines)

    output_path = os.path.join(PROCESSED_DIR, "mixed_ipa_corpus.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        # 行の区切りは改行コード「\n」にして、AIに「文の終わり」のリズムも学ばせる
        f.write("\n".join(all_dataset_lines))

    print(f"🎉 前処理完了！ 学習データがここに保存されました: {output_path}")

if __name__ == "__main__":
    main()

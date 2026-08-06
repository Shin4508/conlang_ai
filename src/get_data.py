import urllib.request
import os

# Dataset published to Github: word list that frequently used in movie
BASE_URL = "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/{}/{}_50k.txt"

# 取得する言語のリスト
langs = {
    "ja": ("japanese.txt", "ja"),
    "ru": ("russian.txt", "ru"),
    "ar": ("arabic.txt", "ar"),
    "fi": ("finnish.txt", "fi"),
    "hu": ("hungarian.txt", "hu"),
}

os.makedirs("data/raw", exist_ok=True)

print("🌍 世界5言語の頻出単語リスト（辞書）をダウンロード開始...\n")

for lang_code, (filename, gh_code) in langs.items():
    url = BASE_URL.format(gh_code, gh_code)
    output_path = f"data/raw/{filename}"
    print(f"📥 {filename} を取得中...")

    try:
        # サーバーに弾かれないようにユーザーエージェントを偽装
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as response:
            content = response.read().decode("utf-8").splitlines()

        # 各行は "単語 頻度" の形式になっているので、単語だけを抽出
        # まずは各言語、最も濃厚な上位5000単語を抽出
        words = []
        for line in content[:5000]:
            parts = line.split()
            if parts:
                words.append(parts[0])

        # ファイルに保存
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(words))

        print(f"  ✅ {len(words)}単語を保存しました！")

    except Exception as e:
        print(f"  ❌ エラーが発生しました: {e}")

print("\n🎉 全ての辞書データの準備が完了しました！")

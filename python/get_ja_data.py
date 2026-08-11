import os
import pandas as pd

# 修正3: ループの外でファイルを開く（テキストデータなので文字化け防止にutf-8を指定）
with open("data/raw/ja.txt", "w", encoding="utf-8") as f:
    # 修正1: 4ではなくrange(4)にする
    for i in range(4):
        filename = f"n{i + 1}.csv"
        path = os.path.join("data", filename)

        df = pd.read_csv(path)

        # 修正2: 1番左の列（0列目）を取得する正しい書き方
        df_word = df["expression"]

        # 修正4: pandasのSeriesを直接writeできないので、文字列に変換して書き込む
        text_data = "\n".join(df_word.astype(str))
        f.write(text_data + "\n")

import * as ort from 'onnxruntime-web';

interface VocabData {
  ipa2id: Record<string, number>;
  id2ipa: Record<number, string>;
  block_size: number;
}

export class ConlangGenerator {
  private session: ort.InferenceSession | null = null;
  private ipa2id: Record<string, number> = {};
  private id2ipa: Record<number, string> = {};
  private blockSize: number = 8;

  // 初期化：ONNXモデルとJSON辞書をロード
  async init(modelPath: string, vocabJson: VocabData) {
    this.session = await ort.InferenceSession.create(modelPath);
    this.ipa2id = vocabJson.ipa2id;
    this.id2ipa = vocabJson.id2ipa;
    this.blockSize = vocabJson.block_size;
  }

  // Softmax & Multinomial (温度付きサンプリング)
  private sampleToken(logits: Float32Array, temperature: number = 0.5): number {
    const expProbs: number[] = [];
    let sumExp = 0;

    // Temperature の適用と Softmax 計算
    for (let i = 0; i < logits.length; i++) {
        const expVal = Math.exp(logits[i] / temperature);
        expProbs.push(expVal);
        sumExp += expVal;
    }

    // ガチャ (Multinomial Sampling)
    let rand = Math.random() * sumExp;
    for (let i = 0; i < expProbs.length; i++) {
        rand -= expProbs[i];
        if (rand <= 0) return i;
    }
    return expProbs.length - 1;
  }

  // 1単語生成関数
  async generateNextWord(promptWord: string, temperature: number = 0.5): Promise<string> {
    if (!this.session) throw new Error("Model is not initialized");

    const inputContext: number[] = [];
    for (const char of promptWord) {
      if (char in this.ipa2id) inputContext.push(this.ipa2id[char]);
    }
    if (inputContext.length === 0) return "";

    const generatedIds: number[] = [];

    while (true) {
      // 直近 block_size 分のみ切り出し
      const cond = inputContext.slice(-this.blockSize);
      
      // ONNX 入力 Tensor の作成 [1, cond.length]
      const inputTensor = new ort.Tensor('int64', BigInt64Array.from(cond.map(n => BigInt(n))), [1, cond.length]);
      
      // 推論実行
      const feeds: Record<string, ort.Tensor> = { input: inputTensor };
      const results = await this.session.run(feeds);
      const outputTensor = results.output; // [1, sequence_length, vocab_size]

      // 最後の位置（-1）の Logits を抽出
      const [batch, seqLen, vocabSize] = outputTensor.dims;
      const data = outputTensor.data as Float32Array;
      const lastTokenLogits = data.slice((seqLen - 1) * vocabSize, seqLen * vocabSize);

      // トークン取得
      const nextId = this.sampleToken(lastTokenLogits, temperature);
      const nextChar = this.id2ipa[nextId];

      if (nextChar === '\n' || nextChar === ' ') break;

      generatedIds.push(nextId);
      inputContext.push(nextId);
    }

    return generatedIds.map(id => this.id2ipa[id]).join('');
  }
}

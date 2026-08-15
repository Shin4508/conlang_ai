import * as ort from 'onnxruntime-web';

ort.env.wasm.wasmPaths = 'https://cdn.jsdelivr.net/npm/onnxruntime-web/dist/';

export interface VocabData {
  ipa2id: Record<string, number>;
  id2ipa: Record<string, string>;
  block_size: number;
}

export class ConlangGenerator {
  private session: ort.InferenceSession | null = null;
  private ipa2id: Record<string, number> = {};
  private id2ipa: Record<string, string> = {};
  private blockSize: number = 8;

  async init(modelPath: string, vocabJson: VocabData): Promise<void> {
    this.ipa2id = vocabJson.ipa2id;
    this.id2ipa = vocabJson.id2ipa;
    this.blockSize = vocabJson.block_size;

    this.session = await ort.InferenceSession.create(modelPath, {
      executionProviders: ['wasm'],
    });
  }

  private sampleToken(logits: Float32Array, temperature: number = 0.5): number {
    const expProbs: number[] = [];
    let sumExp = 0;

    for (let i = 0; i < logits.length; i++) {
      const expVal = Math.exp(logits[i] / temperature);
      expProbs.push(expVal);
      sumExp += expVal;
    }

    let rand = Math.random() * sumExp;
    for (let i = 0; i < expProbs.length; i++) {
      rand -= expProbs[i];
      if (rand <= 0) return i;
    }
    return expProbs.length - 1;
  }

  // 1反復分の単語群を生成し、最少出現IPAを含む単語と新規単語リストを返す
  async generateLoop(
    inputText: string,
    temperature: number = 0.5,
    maxLen: number = 11
  ): Promise<{ leastWord: string; newWords: string[] }> {
    if (!this.session) throw new Error("Model is not initialized");

    let newLineCount = 0;
    const inputContext: number[] = [];
    for (const char of inputText) {
      if (char in this.ipa2id) {
        inputContext.push(this.ipa2id[char]);
      }
    }
    if (inputContext.length === 0) return { leastWord: "", newWords: [] };

    const generatedIds: number[] = [];

    while (true) {
      const cond = inputContext.slice(-this.blockSize);
      const bigIntArray = new BigInt64Array(cond.map(n => BigInt(n)));
      const inputTensor = new ort.Tensor('int64', bigIntArray, [1, cond.length]);

      const feeds: Record<string, ort.Tensor> = { input: inputTensor };
      const results = await this.session.run(feeds);

      const outputTensor = results.output as ort.Tensor;
      const dims = outputTensor.dims as readonly number[];
      const seqLen = dims[1];
      const vocabSize = dims[2];

      const data = outputTensor.data as Float32Array;
      const lastTokenLogits = data.slice((seqLen - 1) * vocabSize, seqLen * vocabSize);

      const nextId = this.sampleToken(lastTokenLogits, temperature);
      const nextChar = this.id2ipa[nextId.toString()];

      if (nextChar === '\n' || nextChar === ' ') {
        newLineCount += 1;
        if (newLineCount >= maxLen) {
          break;
        }
      }

      generatedIds.push(nextId);
      inputContext.push(nextId);
    }

    let nextWordStr = generatedIds.map(id => this.id2ipa[id.toString()]).join('');
    if (nextWordStr.startsWith('\n')) {
      nextWordStr = nextWordStr.slice(1);
    }

    const newWords = nextWordStr.split('\n').filter(w => w.trim().length > 0);

    // 使われたIPA記号のユニーク一覧を取得
    const usedIpaSet = new Set<string>(nextWordStr.split('').filter(c => c !== '\n' && c !== ' '));
    const usedIpa = Array.from(usedIpaSet);

    let leastIpa = "";
    let leastCount = Infinity;

    // 最も出現頻度が低いIPAを特定
    for (const ipa of usedIpa) {
      let ipaCount = 0;
      for (const word of newWords) {
        if (word.includes(ipa)) {
          ipaCount += 1;
        }
      }
      if (ipaCount < leastCount) {
        leastCount = ipaCount;
        leastIpa = ipa;
      }
    }

    // 最少IPAを含む単語を選択
    let leastWord = newWords[0] || "";
    for (const word of newWords) {
      if (word.includes(leastIpa)) {
        leastWord = word;
        break;
      }
    }

    return {
      leastWord: leastWord.endsWith('\n') ? leastWord : leastWord + '\n',
      newWords: newWords
    };
  }

  // 100回反復して語彙集を作成するループ（進捗コールバック付き）
  async expandVocabulary(
    initialPrompt: string,
    iterations: number = 100,
    temperature: number = 0.5,
    onProgress?: (current: number, total: number, newlyAdded: string[], currentSeed: string) => void
  ): Promise<string[]> {
    const library: string[] = [];
    let currentSeed = initialPrompt.endsWith('\n') ? initialPrompt : initialPrompt + '\n';

    for (let i = 0; i < iterations; i++) {
      const result = await this.generateLoop(currentSeed, temperature, 11);
      library.push(...result.newWords);
      currentSeed = result.leastWord || initialPrompt;

      if (onProgress) {
        onProgress(i + 1, iterations, result.newWords, currentSeed.trim());
      }
    }

    return library;
  }
}

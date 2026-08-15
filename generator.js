// ONNX Runtime Web の WASM パス設定
if (window.ort) {
  ort.env.wasm.wasmPaths = 'https://cdn.jsdelivr.net/npm/onnxruntime-web/dist/';
}

export class ConlangGenerator {
  constructor() {
    this.session = null;
    this.ipa2id = {};
    this.id2ipa = {};
    this.blockSize = 8;
  }

  async init(modelPath, vocabJson) {
    this.ipa2id = vocabJson.ipa2id;
    this.id2ipa = vocabJson.id2ipa;
    this.blockSize = vocabJson.block_size;

    this.session = await ort.InferenceSession.create(modelPath, {
      executionProviders: ['wasm'],
    });
  }

  sampleToken(logits, temperature = 0.5) {
    const expProbs = [];
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

  async generateLoop(inputText, temperature = 0.5, maxLen = 11) {
    if (!this.session) throw new Error("Model is not initialized");

    let newLineCount = 0;
    const inputContext = [];
    for (const char of inputText) {
      if (char in this.ipa2id) {
        inputContext.push(this.ipa2id[char]);
      }
    }
    if (inputContext.length === 0) return { leastWord: "", newWords: [] };

    const generatedIds = [];

    while (true) {
      const cond = inputContext.slice(-this.blockSize);
      const bigIntArray = new BigInt64Array(cond.map(n => BigInt(n)));
      const inputTensor = new ort.Tensor('int64', bigIntArray, [1, cond.length]);

      const feeds = { input: inputTensor };
      const results = await this.session.run(feeds);

      const outputTensor = results.output;
      const dims = outputTensor.dims;
      const seqLen = dims[1];
      const vocabSize = dims[2];

      const data = outputTensor.data;
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
    const usedIpa = Array.from(new Set(nextWordStr.split('').filter(c => c !== '\n' && c !== ' ')));

    let leastIpa = "";
    let leastCount = Infinity;

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

    let leastWord = newWords[0] || "";
    for (const word of newWords) {
      if (word.includes(leastIpa)) {
        leastWord = word;
        break;
      }
    }

    return {
      leastWord: leastWord.endsWith('\n') ? leastWord : leastWord + '\n',
      newWords: newWords,
    };
  }

  async expandVocabulary(initialPrompt, iterations = 100, temperature = 0.5, onProgress = null) {
    const library = [];
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

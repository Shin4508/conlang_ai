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
    if (!Number.isFinite(temperature) || temperature <= 0 || !logits.length ||
        !Array.from(logits).every(Number.isFinite)) {
      throw new Error("Expected finite logits and a positive temperature");
    }
    const maximum = Math.max(...logits);
    const expProbs = [];
    let sumExp = 0;

    for (let i = 0; i < logits.length; i++) {
      const expVal = Math.exp((logits[i] - maximum) / temperature);
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

    if (!Number.isInteger(maxLen) || maxLen < 1) throw new Error("maxLen must be positive");
    if (!Number.isFinite(temperature) || temperature <= 0) throw new Error("Invalid temperature");
    let newLineCount = 0;
    const inputContext = [];
    for (const char of inputText) {
      if (char in this.ipa2id) {
        inputContext.push(this.ipa2id[char]);
      } else {
        throw new Error(`Unknown prompt character: ${char}`);
      }
    }
    if (inputContext.length === 0) return { leastWord: "", newWords: [] };

    const generatedIds = [];

    const maxTokens = Math.max(256, maxLen * 128);
    let completed = false;
    for (let step = 0; step < maxTokens; step++) {
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
          completed = true;
          break;
        }
      }

      generatedIds.push(nextId);
      inputContext.push(nextId);
    }

    if (!completed) throw new Error("Generation reached token limit; try another seed");

    let nextWordStr = generatedIds.map(id => this.id2ipa[id.toString()]).join('');
    if (nextWordStr.startsWith('\n')) {
      nextWordStr = nextWordStr.slice(1);
    }

    const newWords = nextWordStr.split(/\s+/).filter(w => w.trim().length > 0);
    const usedIpa = Array.from(new Set(Array.from(nextWordStr).filter(c => c !== '\n' && c !== ' ')));

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

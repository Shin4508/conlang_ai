import { ConlangGenerator } from './generator.js';

let currentInput = "";
const generator = new ConlangGenerator();

const displayEl = document.getElementById('input-display');
const keyboardEl = document.getElementById('keyboard');
const outputEl = document.getElementById('output');
const statusBarEl = document.getElementById('status-bar');
const libCountEl = document.getElementById('lib-count');
const btnSingle = document.getElementById('btn-single');
const btnLoop = document.getElementById('btn-loop');
const btnClear = document.getElementById('btn-clear');
const btnBackspace = document.getElementById('btn-backspace');

function updateDisplay() {
  displayEl.textContent = `/ ${currentInput}`;
}

async function initApp() {
  statusBarEl.textContent = "辞書・モデルを読み込み中...";

  try {
    const vocabRes = await fetch('./vocab.json');
    if (!vocabRes.ok) throw new Error(`vocab.json 取得失敗 (Status: ${vocabRes.status})`);
    const vocabJson = await vocabRes.json();

    await generator.init('./conlang_model.onnx', vocabJson);

    // キーボード作成
    const ipaList = Object.keys(vocabJson.ipa2id).filter(char => char !== '\n' && char !== ' ');
    keyboardEl.innerHTML = '';
    ipaList.forEach(ipaChar => {
      const btn = document.createElement('button');
      btn.className = 'key-btn';
      btn.textContent = ipaChar;
      btn.addEventListener('click', () => {
        currentInput += ipaChar;
        updateDisplay();
      });
      keyboardEl.appendChild(btn);
    });

    statusBarEl.textContent = "✅ 準備完了！IPAボタンを押してシード単語を入力してください。";
  } catch (err) {
    console.error(err);
    statusBarEl.textContent = `❌ 初期化エラー: ${err.message || err}`;
  }
}

btnBackspace.addEventListener('click', () => {
  currentInput = currentInput.slice(0, -1);
  updateDisplay();
});

btnClear.addEventListener('click', () => {
  currentInput = "";
  updateDisplay();
});

// 1回生成
btnSingle.addEventListener('click', async () => {
  if (!currentInput) return alert("IPA記号を入力してください！");

  statusBarEl.textContent = "🧠 生成中...";
  outputEl.textContent = "";

  try {
    const result = await generator.generateLoop(`${currentInput}\n`, 0.5, 2);
    outputEl.textContent = result.newWords.join('\n');
    libCountEl.textContent = result.newWords.length.toString();
    statusBarEl.textContent = "生成完了";
  } catch (err) {
    statusBarEl.textContent = `❌ 生成エラー: ${err.message}`;
  }
});

// 100回ループ探索
btnLoop.addEventListener('click', async () => {
  if (!currentInput) return alert("開始用のシード単語を入力してください！");

  outputEl.textContent = "";
  const allLibrary = [];

  btnLoop.setAttribute('disabled', 'true');
  btnSingle.setAttribute('disabled', 'true');

  try {
    await generator.expandVocabulary(
      currentInput,
      100,
      0.5,
      (step, total, newWords, seed) => {
        allLibrary.push(...newWords);
        statusBarEl.textContent = `🔄 探索中... [${step}/${total}] 次のシード音素: /${seed}/`;
        libCountEl.textContent = allLibrary.length.toString();
        outputEl.textContent = allLibrary.join('\n');
        outputEl.scrollTop = outputEl.scrollHeight;
      }
    );

    statusBarEl.textContent = `🎉 100回の語彙探索完了！ 合計 ${allLibrary.length} 単語生成されました。`;
  } catch (err) {
    statusBarEl.textContent = `❌ ループエラー: ${err.message}`;
  } finally {
    btnLoop.removeAttribute('disabled');
    btnSingle.removeAttribute('disabled');
  }
});

initApp();

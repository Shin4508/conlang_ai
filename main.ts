import { ConlangGenerator } from './generator';

let currentInput = "";
const generator = new ConlangGenerator();

const displayEl = document.getElementById('input-display')!;
const keyboardEl = document.getElementById('keyboard')!;
const outputEl = document.getElementById('output')!;
const statusBarEl = document.getElementById('status-bar')!;
const libCountEl = document.getElementById('lib-count')!;
const btnSingle = document.getElementById('btn-single')!;
const btnLoop = document.getElementById('btn-loop')!;
const btnClear = document.getElementById('btn-clear')!;
const btnBackspace = document.getElementById('btn-backspace')!;

async function initApp() {
  statusBarEl.textContent = "辞書・モデルを読み込み中...";

  try {
    const vocabRes = await fetch('/vocab.json');
    if (!vocabRes.ok) throw new Error(`vocab.json 取得失敗 (Status: ${vocabRes.status})`);
    const vocabJson = await vocabRes.json();

    await generator.init('/conlang_model.onnx', vocabJson);

    // キーボード作成
    const ipaList = Object.keys(vocabJson.ipa2id).filter(char => char !== '\n' && char !== ' ');
    keyboardEl.innerHTML = '';
    ipaList.forEach(ipaChar => {
      const btn = document.createElement('button');
      btn.className = 'key-btn';
      btn.textContent = ipaChar;
      btn.addEventListener('click', () => {
        currentInput += ipaChar;
        displayEl.textContent = `/ ${currentInput}`;
      });
      keyboardEl.appendChild(btn);
    });

    statusBarEl.textContent = "✅ 準備完了！IPAボタンを押してシード単語を入力してください。";
  } catch (err) {
    statusBarEl.textContent = `❌ 初期化エラー: ${err}`;
  }
}

// 1文字削除・クリア
btnBackspace.addEventListener('click', () => {
  currentInput = currentInput.slice(0, -1);
  displayEl.textContent = `/ ${currentInput}`;
});

btnClear.addEventListener('click', () => {
  currentInput = "";
  displayEl.textContent = "/ ";
});

// 1. 通常の1回生成
btnSingle.addEventListener('click', async () => {
  if (!currentInput) return alert("IPA記号を入力してください！");

  statusBarEl.textContent = "🧠 AI生成中...";
  outputEl.textContent = "";

  const result = await generator.generateLoop(`${currentInput}\n`, 0.5, 2);
  outputEl.textContent = result.newWords.join('\n');
  libCountEl.textContent = result.newWords.length.toString();
  statusBarEl.textContent = "生成完了";
});

// 2. 100反復探索ループ (Pythonのgenerate_loop logic)
btnLoop.addEventListener('click', async () => {
  if (!currentInput) return alert("開始用のシード単語を入力してください！");

  outputEl.textContent = "";
  const allLibrary: string[] = [];

  btnLoop.setAttribute('disabled', 'true');
  btnSingle.setAttribute('disabled', 'true');

  await generator.expandVocabulary(
    currentInput,
    100,
    0.5,
    (step, total, newWords, seed) => {
      allLibrary.push(...newWords);
      statusBarEl.textContent = `🔄 探索中... [${step}/${total}] 次のシード音素: /${seed}/`;
      libCountEl.textContent = allLibrary.length.toString();
      
      // 生成された単語を随時下部に追加表示
      outputEl.textContent = allLibrary.join('\n');
      outputEl.scrollTop = outputEl.scrollHeight;
    }
  );

  statusBarEl.textContent = `🎉 100回の語彙探索完了！ 合計 ${allLibrary.length} 単語生成されました。`;
  btnLoop.removeAttribute('disabled');
  btnSingle.removeAttribute('disabled');
});

initApp();

import { ConlangGenerator } from './generator';

let currentInput = "";
const generator = new ConlangGenerator();

// HTML要素の取得
const displayEl = document.getElementById('input-display')!;
const keyboardEl = document.getElementById('keyboard')!;
const outputEl = document.getElementById('output')!;
const btnEnter = document.getElementById('btn-enter')!;
const btnClear = document.getElementById('btn-clear')!;
const btnBackspace = document.getElementById('btn-backspace')!;

async function initApp() {
  outputEl.textContent = "モデルを読み込み中...";
  
  // 1. vocab.json と ONNX モデルのロード
  const vocabRes = await fetch('/vocab.json');
  const vocabJson = await vocabRes.json();
  
  await generator.init('/conlang_model.onnx', vocabJson);
  outputEl.textContent = "準備完了！IPAボタンを押して単語を作成してください。";

  // 2. vocab.json の学習済みIPAからキーボードボタンを自動生成
  const ipaList = Object.keys(vocabJson.ipa2id).filter(char => char !== '\n' && char !== ' ');

  ipaList.forEach(ipaChar => {
    const btn = document.createElement('button');
    btn.className = 'key-btn';
    btn.textContent = ipaChar;
    
    // ぽちぽち押した時の処理
    btn.addEventListener('click', () => {
      currentInput += ipaChar;
      updateDisplay();
    });
    
    keyboardEl.appendChild(btn);
  });
}

// ディスプレイ表示の更新
function updateDisplay() {
  displayEl.textContent = `/ ${currentInput}`;
}

// 1文字削除
btnBackspace.addEventListener('click', () => {
  currentInput = currentInput.slice(0, -1);
  updateDisplay();
});

// クリア
btnClear.addEventListener('click', () => {
  currentInput = "";
  updateDisplay();
});

// ⏎ Enter を押して AI に推論させる処理
btnEnter.addEventListener('click', async () => {
  if (!currentInput) {
    alert("IPA記号を1文字以上入力してください！");
    return;
  }

  outputEl.textContent = "🧠 AIが思考中...";
  
  try {
    // ユーザーが作った単語 + 改行('\n') をプロンプトにして生成
    const prompt = `${currentInput}\n`;
    const resultWord = await generator.generateNextWord(prompt, 0.5);
    
    outputEl.textContent = `入力: /${currentInput}/\n生成: /${resultWord}/`;
  } catch (e) {
    outputEl.textContent = `❌ エラーが発生しました: ${e}`;
  }
});

// アプリ起動
initApp();

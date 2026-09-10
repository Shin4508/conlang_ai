import { readFile } from 'node:fs/promises';
import test from 'node:test';
import assert from 'node:assert/strict';
globalThis.window = {};
globalThis.ort = { Tensor: class {} };
const source = await readFile(new URL('../generator.js', import.meta.url), 'utf8');
const { ConlangGenerator } = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
test('stable sampling and invalid temperatures', () => {
  const g = new ConlangGenerator();
  assert.equal(g.sampleToken([10000, -10000]), 0);
  for (const t of [0, -1, NaN, Infinity]) assert.throws(() => g.sampleToken([1, 2], t));
});
test('model that never emits a boundary stops', async () => {
  const g = new ConlangGenerator();
  g.ipa2id = { a: 0 }; g.id2ipa = { 0: 'a' };
  let calls = 0;
  g.session = { run: async () => { calls++; return { output: { dims: [1, 1, 1], data: [1] } }; } };
  await assert.rejects(g.generateLoop('a', 0.5, 1), /token limit/);
  assert.equal(calls, 256);
  await assert.rejects(g.generateLoop('z'), /Unknown prompt/);
});

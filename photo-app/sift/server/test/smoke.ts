// スモークテスト: モックライブラリで検出・判断・削除の全パイプラインを検証する。
// 実行: npm test(sift ルート)/ npm run test(server ワークスペース)
import assert from 'node:assert';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { openDb, setSetting } from '../src/db';
import { createMockImmich } from '../src/immich/mock';
import { runFullScan } from '../src/services/analyze';
import { applyDecisions, keepBest, undoLast } from '../src/services/decisions';
import { getQueues } from '../src/services/queues';
import { commitTrash } from '../src/services/trash';

const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'sift-test-'));
const db = openDb(path.join(dir, 'test.db'));
const immich = createMockImmich();

const results: string[] = [];
function ok(name: string, cond: boolean, detail = '') {
  assert.ok(cond, `${name} ${detail}`);
  results.push(`✓ ${name}`);
}

// ① フルスキャン: 全カテゴリの検出数がモックの正解と一致(誤検出ゼロ)
const r = await runFullScan(db, immich);
ok('スキャン件数', r.scanned === 98, `got ${r.scanned}`);
ok('スクショ検出', r.screenshots === 24, `got ${r.screenshots}`);
ok('画面収録検出', r.screenRecordings === 3, `got ${r.screenRecordings}`);
ok('大きい動画検出', r.largeVideos === 2, `got ${r.largeVideos}`);
ok('メモ写真検出', r.memo === 8, `got ${r.memo}`);
ok('ぼやけ検出', r.blurry === 5, `got ${r.blurry}`);
ok('RAWペア検出', r.rawPairs === 2, `got ${r.rawPairs}`);
ok('重複グループ', r.duplicateGroups === 5, `got ${r.duplicateGroups}`);
ok('連写グループ', r.burstGroups === 2, `got ${r.burstGroups}`);
ok('類似グループ', r.similarGroups === 3, `got ${r.similarGroups}`);

// ② RAWペア連動: JPG を削除予定にすると DNG も連動し、Undo で両方戻る
await applyDecisions(db, immich, ['mock-raw-0-jpg'], 'trash_pending');
const pairDec = (id: string) =>
  (db.prepare(`SELECT decision FROM asset_state WHERE asset_id=?`).get(id) as { decision: string | null }).decision;
ok('RAWペア連動(JPG→DNG)', pairDec('mock-raw-0-dng') === 'trash_pending');
await undoLast(db, immich);
ok('RAWペア連動のUndo', pairDec('mock-raw-0-jpg') === null && pairDec('mock-raw-0-dng') === null);

// ③ keep-best のお気に入り保護: お気に入りメンバーは一括削除予定に入らない
db.prepare(`UPDATE asset_state SET is_favorite=1 WHERE asset_id='mock-dup-1-0'`).run();
const dupGroup = db.prepare(`SELECT group_id g FROM asset_state WHERE asset_id='mock-dup-1-0'`).get() as { g: number };
keepBest(db, dupGroup.g); // ベストは mock-dup-1-2(最大サイズ)
ok('お気に入り保護', pairDec('mock-dup-1-0') === null, 'favorite must stay undecided');
ok('keep-best 実行', pairDec('mock-dup-1-1') === 'trash_pending');
db.prepare(`UPDATE asset_state SET is_favorite=0 WHERE asset_id='mock-dup-1-0'`).run();

// ④ F-10 自動ルール: min_age を大きくするとスクショ候補が消える
setSetting(db, 'screenshot_min_age_days', '3650');
const r2 = await runFullScan(db, immich);
ok('スクショ経過日数ルール', r2.screenshots === 0, `got ${r2.screenshots}`);
setSetting(db, 'screenshot_min_age_days', '0');
await runFullScan(db, immich);

// ⑤ コミット → Immich ゴミ箱 → 一括復元(スクショ2枚+RAWペアを追加で削除予定に)
await applyDecisions(db, immich, ['mock-shot-0', 'mock-shot-1', 'mock-raw-0-jpg'], 'trash_pending');
const before = getQueues(db).trashPending;
ok('削除予定が溜まっている', before.count >= 3, `got ${before.count}`);
const c = await commitTrash(db, immich);
ok('ゴミ箱へ移動', c.moved === before.count && c.bytes === before.bytes);
ok('コミット後は削除予定ゼロ', getQueues(db).trashPending.count === 0);
const u = await undoLast(db, immich);
ok('コミットの一括復元', u.undone === 'trash_commit' && getQueues(db).trashPending.count === before.count);

console.log(results.join('\n'));
console.log(`\n全 ${results.length} 件のテストに合格 🎉`);

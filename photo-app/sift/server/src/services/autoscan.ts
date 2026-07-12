import { config } from '../config';
import { getSetting, setSetting, type Db } from '../db';
import type { ImmichClient } from '../immich/types';
import { runFullScanOnce } from './analyze';

// F-10 自動ルール: 夜間の自動スキャン(SPEC §11 の夜間バッチ)。
// サーバー常駐プロセス内のタイマーで実現するので launchd の追加設定は不要。
// auto_scan_hour(0-23)に一致した時間帯に1日1回だけ実行する(-1 で無効)。

const MIN_INTERVAL_MS = 20 * 3600 * 1000; // 同日二重実行の防止

export async function maybeAutoScan(db: Db, immich: ImmichClient, now: Date = new Date()): Promise<boolean> {
  const hour = Number(getSetting(db, 'auto_scan_hour', '3'));
  if (hour < 0 || hour > 23 || now.getHours() !== hour) return false;
  const last = Number(getSetting(db, 'last_auto_scan', '0'));
  if (now.getTime() - last < MIN_INTERVAL_MS) return false;

  setSetting(db, 'last_auto_scan', String(now.getTime()));
  await backupDb(db); // SPEC §9: スキャン前に判断履歴をバックアップ
  const r = await runFullScanOnce(db, immich);
  console.log(
    `[自動スキャン] 完了: ${r.scanned}枚 / スクショ${r.screenshots} メモ${r.memo} ぼやけ${r.blurry} / ` +
      `重複${r.duplicateGroups} 連写${r.burstGroups} 類似${r.similarGroups}組`
  );
  return true;
}

export async function backupDb(db: Db): Promise<void> {
  try {
    await db.backup(`${config.dbPath}.bak`);
  } catch (e) {
    console.warn('DBバックアップ失敗:', (e as Error).message);
  }
}

export function startAutoScanTimer(db: Db, immich: ImmichClient): void {
  setInterval(() => {
    maybeAutoScan(db, immich).catch((e) => console.error('自動スキャン失敗:', (e as Error).message));
  }, 10 * 60 * 1000);
}

import { getSetting, type Db } from '../db';
import type { ImmichAsset, ImmichClient } from '../immich/types';

// SPEC §6.1 スクリーンショット検出(Phase 1 はメタデータシグナルのみ。CLIP は Phase 2)
const SCREENSHOT_NAME_RE = /(screen[ _-]?shot|screenshot|スクリーンショット|スクショ)/i;
// v1.1: 画面収録(スクショの動画版)。iOS は RPReplay_Final*.MP4
const SCREEN_RECORDING_RE = /(screen[ _-]?record|rpreplay|画面収録)/i;
// v1.1: RAW 拡張子(RAW+JPEG ペア検出用。SPEC §9・§10)
export const RAW_FILE_RE = /\.(dng|raw|cr2|cr3|crw|nef|nrw|arw|srf|sr2|orf|rw2|raf|pef)$/i;

// 主要スマホの画面解像度(設定 device_resolutions で上書き可能)
export const DEFAULT_RESOLUTIONS = [
  '1179x2556', // iPhone 14 Pro / 15 / 15 Pro / 16
  '1170x2532', // iPhone 12 / 13 / 14
  '1290x2796', // iPhone 15 Pro Max / 16 Plus
  '1206x2622', // iPhone 16 Pro
  '1320x2868', // iPhone 16 Pro Max
  '1125x2436', // iPhone X / XS / 11 Pro
  '1080x2340',
  '1080x2400',
  '1440x3200',
  '1080x1920',
];

export interface ScanResult {
  scanned: number;
  screenshots: number;
  screenRecordings: number;
  largeVideos: number;
  rawPairs: number;
  duplicateGroups: number;
}

export function screenshotScore(a: ImmichAsset, resolutions: Set<string>): number {
  let s = 0;
  if (SCREENSHOT_NAME_RE.test(a.originalFileName)) s += 0.5; // ファイル名(高)
  const exif = a.exifInfo;
  if (!exif?.make && !exif?.model) s += 0.2; // カメラ情報なし(中)
  const isPng = a.originalMimeType === 'image/png' || /\.png$/i.test(a.originalFileName);
  if (isPng) s += 0.15; // PNG(形式シグナルの一部)
  const w = exif?.exifImageWidth;
  const h = exif?.exifImageHeight;
  if (w && h && (resolutions.has(`${w}x${h}`) || resolutions.has(`${h}x${w}`))) s += 0.35; // 画面解像度一致(高)
  return Math.min(1, s);
}

async function importDuplicates(db: Db, immich: ImmichClient): Promise<number> {
  const groups = await immich.getDuplicates();
  const findGroup = db.prepare(`SELECT id FROM groups WHERE immich_ref = ?`);
  const insGroup = db.prepare(`INSERT INTO groups(kind, immich_ref, best_asset_id) VALUES('duplicate', ?, ?)`);
  const updBest = db.prepare(`UPDATE groups SET best_asset_id = ? WHERE id = ?`);
  const setMember = db.prepare(`UPDATE asset_state SET group_id = ? WHERE asset_id = ?`);

  const tx = db.transaction(() => {
    for (const g of groups) {
      if (!g.assets?.length) continue;
      const best = pickBest(g.assets);
      const row = findGroup.get(g.duplicateId) as { id: number } | undefined;
      let id: number;
      if (row) {
        id = row.id;
        updBest.run(best.id, id);
      } else {
        id = Number(insGroup.run(g.duplicateId, best.id).lastInsertRowid);
      }
      for (const a of g.assets) setMember.run(id, a.id);
    }
  });
  tx();
  return groups.length;
}

// 残す1枚の既定 = お気に入り > ファイルサイズ最大(Apple写真の「結合」に倣う。SPEC S-3)
function pickBest(assets: ImmichAsset[]): ImmichAsset {
  return [...assets].sort(
    (x, y) =>
      Number(y.isFavorite) - Number(x.isFavorite) ||
      (y.exifInfo?.fileSizeInByte ?? 0) - (x.exifInfo?.fileSizeInByte ?? 0)
  )[0];
}

// SPEC §9・§10: RAW+JPEG ペア(同じベース名・同時刻)を検出して相互リンクする。
// 判断(削除予定・残す等)はペア両方に適用され、片割れだけ消えることを防ぐ。
function detectRawPairs(db: Db, assets: ImmichAsset[]): number {
  const byKey = new Map<string, ImmichAsset[]>();
  for (const a of assets) {
    if (a.type !== 'IMAGE') continue;
    const base = a.originalFileName.replace(/\.[^.]+$/, '').toLowerCase();
    const key = `${base}|${a.localDateTime ?? a.fileCreatedAt}`;
    byKey.set(key, [...(byKey.get(key) ?? []), a]);
  }
  const setPair = db.prepare(`UPDATE asset_state SET pair_asset_id = ? WHERE asset_id = ?`);
  let pairs = 0;
  const tx = db.transaction(() => {
    db.prepare(`UPDATE asset_state SET pair_asset_id = NULL`).run();
    for (const group of byKey.values()) {
      if (group.length !== 2) continue;
      const raws = group.filter((a) => RAW_FILE_RE.test(a.originalFileName));
      if (raws.length !== 1) continue; // RAW 1枚 + 現像/JPEG 1枚 のみペアとみなす
      setPair.run(group[1].id, group[0].id);
      setPair.run(group[0].id, group[1].id);
      pairs++;
    }
  });
  tx();
  return pairs;
}

export async function runScan(db: Db, immich: ImmichClient): Promise<ScanResult> {
  const resolutions = new Set<string>(
    JSON.parse(getSetting(db, 'device_resolutions', JSON.stringify(DEFAULT_RESOLUTIONS))) as string[]
  );
  const threshold = Number(getSetting(db, 'screenshot_threshold', '0.5'));
  // F-10 自動ルール: 撮影から N 日経過したスクショだけ候補に入れる(0 = 即候補)
  const minAgeDays = Number(getSetting(db, 'screenshot_min_age_days', '0'));
  // v1.1: このサイズ以上の動画を「大きい動画」候補に
  const videoLargeBytes = Number(getSetting(db, 'video_large_mb', '200')) * 1_000_000;
  const now = Date.now();

  const assets = await immich.fetchAllAssets();
  const upsert = db.prepare(`
    INSERT INTO asset_state (asset_id, category, score, file_name, taken_at, size_bytes, width, height, is_favorite, mime, camera, type, duration)
    VALUES (@asset_id, @category, @score, @file_name, @taken_at, @size_bytes, @width, @height, @is_favorite, @mime, @camera, @type, @duration)
    ON CONFLICT(asset_id) DO UPDATE SET
      category = excluded.category,
      score = excluded.score,
      file_name = excluded.file_name,
      taken_at = excluded.taken_at,
      size_bytes = excluded.size_bytes,
      width = excluded.width,
      height = excluded.height,
      is_favorite = excluded.is_favorite,
      mime = excluded.mime,
      camera = excluded.camera,
      type = excluded.type,
      duration = excluded.duration
  `); // decision / group_id には触らない(ユーザーの判断を上書きしない)

  let screenshots = 0;
  let screenRecordings = 0;
  let largeVideos = 0;
  const tx = db.transaction((rows: ImmichAsset[]) => {
    for (const a of rows) {
      const size = a.exifInfo?.fileSizeInByte ?? 0;
      let category = 'none';
      let score = 0;
      if (a.type === 'VIDEO') {
        if (!a.isFavorite && SCREEN_RECORDING_RE.test(a.originalFileName)) {
          category = 'screen_recording';
          score = 0.9;
          screenRecordings++;
        } else if (!a.isFavorite && size >= videoLargeBytes) {
          category = 'video_large';
          score = Math.min(1, size / (videoLargeBytes * 5)); // 大きいほど先頭に
          largeVideos++;
        }
      } else {
        score = screenshotScore(a, resolutions);
        const takenAt = a.localDateTime ?? a.fileCreatedAt;
        const ageDays = takenAt ? (now - Date.parse(takenAt)) / 86_400_000 : Number.POSITIVE_INFINITY;
        // お気に入りはセーフリスト(SPEC §6.4)— 候補に入れない
        if (!a.isFavorite && score >= threshold && ageDays >= minAgeDays) {
          category = 'screenshot';
          screenshots++;
        }
      }
      upsert.run({
        asset_id: a.id,
        category,
        score,
        file_name: a.originalFileName,
        taken_at: a.localDateTime ?? a.fileCreatedAt,
        size_bytes: size,
        width: a.exifInfo?.exifImageWidth ?? null,
        height: a.exifInfo?.exifImageHeight ?? null,
        is_favorite: a.isFavorite ? 1 : 0,
        mime: a.originalMimeType ?? null,
        camera: [a.exifInfo?.make, a.exifInfo?.model].filter(Boolean).join(' ') || null,
        type: a.type,
        duration: a.duration ?? null,
      });
    }
  });
  tx(assets);

  const rawPairs = detectRawPairs(db, assets);
  const duplicateGroups = await importDuplicates(db, immich);
  return { scanned: assets.length, screenshots, screenRecordings, largeVideos, rawPairs, duplicateGroups };
}

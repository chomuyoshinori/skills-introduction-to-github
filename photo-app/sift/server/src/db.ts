import Database from 'better-sqlite3';
import { config } from './config';

// Sift は写真実体・メタデータの複製を持たない(SPEC §4)。
// asset_state の file_name / size_bytes 等はキュー表示用のキャッシュで、スキャンごとに上書きされる。
const SCHEMA = `
CREATE TABLE IF NOT EXISTS asset_state(
  asset_id   TEXT PRIMARY KEY,
  category   TEXT NOT NULL DEFAULT 'none',
  score      REAL NOT NULL DEFAULT 0,
  decision   TEXT,
  decided_at TEXT,
  group_id   INTEGER,
  file_name  TEXT,
  taken_at   TEXT,
  size_bytes INTEGER NOT NULL DEFAULT 0,
  width      INTEGER,
  height     INTEGER,
  is_favorite INTEGER NOT NULL DEFAULT 0,
  mime       TEXT
);
CREATE INDEX IF NOT EXISTS idx_asset_state_queue ON asset_state(category, decision);
CREATE INDEX IF NOT EXISTS idx_asset_state_group ON asset_state(group_id);

CREATE TABLE IF NOT EXISTS groups(
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  kind          TEXT NOT NULL,
  immich_ref    TEXT UNIQUE,
  best_asset_id TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS undo_log(
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  action_json TEXT NOT NULL,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS settings(
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
`;

export type Db = Database.Database;

export function openDb(dbPath: string = config.dbPath): Db {
  const db = new Database(dbPath);
  db.pragma('journal_mode = WAL');
  db.exec(SCHEMA);
  // Phase 2 で追加した列(既存DBにも適用できるよう ALTER で足す)
  ensureColumn(db, 'asset_state', 'phash', 'phash TEXT');
  ensureColumn(db, 'asset_state', 'sharpness', 'sharpness REAL');
  ensureColumn(db, 'asset_state', 'doc_like', 'doc_like INTEGER NOT NULL DEFAULT 0');
  ensureColumn(db, 'asset_state', 'memo_clip', 'memo_clip INTEGER NOT NULL DEFAULT 0');
  ensureColumn(db, 'asset_state', 'camera', 'camera TEXT');
  // v1.1(レビュー改修)で追加した列
  ensureColumn(db, 'asset_state', 'type', "type TEXT NOT NULL DEFAULT 'IMAGE'");
  ensureColumn(db, 'asset_state', 'duration', 'duration TEXT');
  ensureColumn(db, 'asset_state', 'pair_asset_id', 'pair_asset_id TEXT');
  return db;
}

function ensureColumn(db: Db, table: string, name: string, ddl: string): void {
  const cols = db.prepare(`PRAGMA table_info(${table})`).all() as { name: string }[];
  if (!cols.some((c) => c.name === name)) db.exec(`ALTER TABLE ${table} ADD COLUMN ${ddl}`);
}

export function getSetting(db: Db, key: string, fallback: string): string {
  const row = db.prepare(`SELECT value FROM settings WHERE key = ?`).get(key) as
    | { value: string }
    | undefined;
  return row?.value ?? fallback;
}

export function setSetting(db: Db, key: string, value: string): void {
  db.prepare(
    `INSERT INTO settings(key, value) VALUES(?, ?)
     ON CONFLICT(key) DO UPDATE SET value = excluded.value`
  ).run(key, value);
}

export function pushUndo(db: Db, action: object): void {
  db.prepare(`INSERT INTO undo_log(action_json) VALUES(?)`).run(JSON.stringify(action));
}

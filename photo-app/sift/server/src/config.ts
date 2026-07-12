import fs from 'node:fs';
import path from 'node:path';

// .env を server/ と sift ルートの順で読む(既に環境変数にある値が優先)
function loadDotEnv() {
  for (const p of [path.resolve(process.cwd(), '.env'), path.resolve(process.cwd(), '../.env')]) {
    if (!fs.existsSync(p)) continue;
    for (const line of fs.readFileSync(p, 'utf8').split('\n')) {
      if (line.trim().startsWith('#')) continue;
      const m = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$/);
      if (!m) continue;
      if (process.env[m[1]] === undefined) {
        process.env[m[1]] = m[2].replace(/^["']|["']$/g, '');
      }
    }
  }
}
loadDotEnv();

export const config = {
  port: Number(process.env.PORT || 8787),
  dbPath: process.env.SIFT_DB || path.resolve(process.cwd(), 'sift.db'),
  immichUrl: (process.env.IMMICH_URL || 'http://localhost:2283').replace(/\/+$/, ''),
  immichApiKey: process.env.IMMICH_API_KEY || '',
  mock: process.env.SIFT_MOCK === '1',
  // 簡易PINロック(SPEC §11)。未設定なら認証なし(Tailscale内のみでの利用が前提)
  pin: process.env.SIFT_PIN || '',
};

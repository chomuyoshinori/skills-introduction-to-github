export interface ImmichExif {
  make?: string | null;
  model?: string | null;
  fileSizeInByte?: number | null;
  exifImageWidth?: number | null;
  exifImageHeight?: number | null;
}

export interface ImmichAsset {
  id: string;
  originalFileName: string;
  originalMimeType?: string;
  fileCreatedAt: string;
  localDateTime?: string;
  isFavorite: boolean;
  type: string; // IMAGE | VIDEO
  duration?: string | null; // 動画のみ "HH:MM:SS.mmm"
  exifInfo?: ImmichExif | null;
}

export interface DuplicateGroup {
  duplicateId: string;
  assets: ImmichAsset[];
}

export interface Thumb {
  contentType: string;
  body: ArrayBuffer;
}

export interface ImmichClient {
  readonly mock: boolean;
  ping(): Promise<boolean>;
  /** 全画像アセットを取得(ゴミ箱内は含まない) */
  fetchAllAssets(): Promise<ImmichAsset[]>;
  getDuplicates(): Promise<DuplicateGroup[]>;
  /** ゴミ箱へ移動(完全削除はしない) */
  trashAssets(ids: string[]): Promise<void>;
  restoreAssets(ids: string[]): Promise<void>;
  setFavorite(id: string, isFavorite: boolean): Promise<void>;
  getThumbnail(id: string, size: 'thumbnail' | 'preview'): Promise<Thumb>;
  /** CLIP スマート検索。ヒットしたアセットIDを返す(Immich の ML を利用) */
  smartSearch(query: string): Promise<string[]>;
}

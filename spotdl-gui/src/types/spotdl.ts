// Audio Providers
export type AudioProvider =
  | 'youtube'
  | 'youtube-music'
  | 'slider-kz'
  | 'soundcloud'
  | 'bandcamp'
  | 'piped';

// Lyrics Providers
export type LyricsProvider =
  | 'genius'
  | 'musixmatch'
  | 'azlyrics'
  | 'synced';

// Audio Formats
export type AudioFormat =
  | 'mp3'
  | 'flac'
  | 'ogg'
  | 'opus'
  | 'm4a'
  | 'wav';

// Bitrate options
export type Bitrate =
  | 'auto'
  | 'disable'
  | '8k' | '16k' | '24k' | '32k' | '40k' | '48k'
  | '64k' | '80k' | '96k' | '112k' | '128k' | '160k'
  | '192k' | '224k' | '256k' | '320k'
  | '0' | '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9'; // VBR

// Overwrite modes
export type OverwriteMode = 'skip' | 'metadata' | 'force';

// Album types
export type AlbumType = 'single' | 'album' | 'compilation';

// Operation types
export type Operation = 'download' | 'save' | 'web' | 'sync' | 'meta' | 'url';

// Download status
export type DownloadStatus =
  | 'queued'
  | 'downloading'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'paused';

// Download item interface
export interface DownloadItem {
  id: string;
  query: string;
  title?: string;
  artist?: string;
  album?: string;
  coverUrl?: string;
  status: DownloadStatus;
  progress: number;
  error?: string;
  startTime?: Date;
  endTime?: Date;
}

// Main download options
export interface DownloadOptions {
  // Query
  query: string;

  // Providers
  audioProviders: AudioProvider[];
  lyricsProviders: LyricsProvider[];

  // Audio settings
  format: AudioFormat;
  bitrate: Bitrate;
  threads: number;

  // Output settings
  output: string;
  overwrite: OverwriteMode;

  // Advanced options
  preload: boolean;
  sponsorBlock: boolean;
  skipExplicit: boolean;
  fetchAlbums: boolean;
  playlistNumbering: boolean;
  generateLrc: boolean;

  // Filters
  dontFilterResults: boolean;
  onlyVerifiedResults: boolean;
  albumType?: AlbumType;

  // M3U
  m3u?: string;

  // Additional options
  addUnavailable: boolean;
  printErrors: boolean;
}

// Spotify authentication
export interface SpotifyAuth {
  clientId?: string;
  clientSecret?: string;
  authToken?: string;
  userAuth: boolean;
}

// Download queue state
export interface QueueState {
  items: DownloadItem[];
  addItem: (item: Omit<DownloadItem, 'id' | 'status' | 'progress'>) => void;
  removeItem: (id: string) => void;
  updateItem: (id: string, updates: Partial<DownloadItem>) => void;
  clearCompleted: () => void;
  clearAll: () => void;
}

// Settings state
export interface SettingsState {
  downloadOptions: DownloadOptions;
  spotifyAuth: SpotifyAuth;
  updateDownloadOptions: (options: Partial<DownloadOptions>) => void;
  updateSpotifyAuth: (auth: Partial<SpotifyAuth>) => void;
  resetToDefaults: () => void;
}

// API Response types
export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface DownloadResponse {
  downloadId: string;
  message: string;
}

export interface ProgressUpdate {
  id: string;
  progress: number;
  status: DownloadStatus;
  currentFile?: string;
  error?: string;
}

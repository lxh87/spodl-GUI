import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { SettingsState, DownloadOptions, SpotifyAuth } from '../types/spotdl';

const defaultDownloadOptions: DownloadOptions = {
  query: '',
  audioProviders: ['youtube-music', 'youtube'],
  lyricsProviders: ['genius', 'musixmatch'],
  format: 'mp3',
  bitrate: '320k',
  threads: 4,
  output: '{artists} - {title}.{output-ext}',
  overwrite: 'skip',
  preload: false,
  sponsorBlock: false,
  skipExplicit: false,
  fetchAlbums: false,
  playlistNumbering: false,
  generateLrc: false,
  dontFilterResults: false,
  onlyVerifiedResults: false,
  addUnavailable: false,
  printErrors: true,
};

const defaultSpotifyAuth: SpotifyAuth = {
  userAuth: false,
};

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      downloadOptions: defaultDownloadOptions,
      spotifyAuth: defaultSpotifyAuth,

      updateDownloadOptions: (options) =>
        set((state) => ({
          downloadOptions: { ...state.downloadOptions, ...options },
        })),

      updateSpotifyAuth: (auth) =>
        set((state) => ({
          spotifyAuth: { ...state.spotifyAuth, ...auth },
        })),

      resetToDefaults: () =>
        set({
          downloadOptions: defaultDownloadOptions,
          spotifyAuth: defaultSpotifyAuth,
        }),
    }),
    {
      name: 'spotdl-settings',
    }
  )
);

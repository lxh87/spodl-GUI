import { useState } from 'react';
import { useSettingsStore } from '../store/settingsStore';
import { useQueueStore } from '../store/queueStore';
import SearchInput from '../components/download/SearchInput';
import ProviderSelector from '../components/download/ProviderSelector';
import QualitySettings from '../components/download/QualitySettings';
import { spotdlApi } from '../services/api';
import { ChevronDown, ChevronUp } from 'lucide-react';

const DownloadPage = () => {
  const { downloadOptions, updateDownloadOptions } = useSettingsStore();
  const { addItem } = useQueueStore();
  const [loading, setLoading] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleSearch = async (query: string) => {
    setLoading(true);

    // Add to queue immediately
    addItem({
      query,
      title: query,
    });

    try {
      // Call the download API
      const result = await spotdlApi.download({
        ...downloadOptions,
        query,
      });

      if (result.success) {
        console.log('Download started:', result.data);
      } else {
        console.error('Download failed:', result.error);
      }
    } catch (error) {
      console.error('Error starting download:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold text-foreground mb-2">Download Music</h2>
        <p className="text-muted-foreground">
          Paste a Spotify or YouTube URL to get started
        </p>
      </div>

      {/* Search Input */}
      <div className="bg-card border border-border rounded-lg p-6">
        <SearchInput onSearch={handleSearch} loading={loading} />
      </div>

      {/* Provider Selection */}
      <div className="bg-card border border-border rounded-lg p-6">
        <ProviderSelector
          audioProviders={downloadOptions.audioProviders}
          lyricsProviders={downloadOptions.lyricsProviders}
          onAudioProvidersChange={(providers) =>
            updateDownloadOptions({ audioProviders: providers })
          }
          onLyricsProvidersChange={(providers) =>
            updateDownloadOptions({ lyricsProviders: providers })
          }
        />
      </div>

      {/* Quality Settings */}
      <div className="bg-card border border-border rounded-lg p-6">
        <QualitySettings
          format={downloadOptions.format}
          bitrate={downloadOptions.bitrate}
          threads={downloadOptions.threads}
          outputTemplate={downloadOptions.output}
          onFormatChange={(format) => updateDownloadOptions({ format })}
          onBitrateChange={(bitrate) => updateDownloadOptions({ bitrate })}
          onThreadsChange={(threads) => updateDownloadOptions({ threads })}
          onOutputTemplateChange={(output) => updateDownloadOptions({ output })}
        />
      </div>

      {/* Advanced Options (Collapsible) */}
      <div className="bg-card border border-border rounded-lg p-6">
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center justify-between w-full text-left"
        >
          <h3 className="font-semibold text-foreground">Advanced Options</h3>
          {showAdvanced ? (
            <ChevronUp className="w-5 h-5 text-muted-foreground" />
          ) : (
            <ChevronDown className="w-5 h-5 text-muted-foreground" />
          )}
        </button>

        {showAdvanced && (
          <div className="mt-4 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={downloadOptions.preload}
                  onChange={(e) => updateDownloadOptions({ preload: e.target.checked })}
                  className="w-4 h-4 rounded border-input"
                />
                <span className="text-sm text-foreground">Preload URLs</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={downloadOptions.sponsorBlock}
                  onChange={(e) => updateDownloadOptions({ sponsorBlock: e.target.checked })}
                  className="w-4 h-4 rounded border-input"
                />
                <span className="text-sm text-foreground">Skip Sponsor Segments</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={downloadOptions.skipExplicit}
                  onChange={(e) => updateDownloadOptions({ skipExplicit: e.target.checked })}
                  className="w-4 h-4 rounded border-input"
                />
                <span className="text-sm text-foreground">Skip Explicit Songs</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={downloadOptions.fetchAlbums}
                  onChange={(e) => updateDownloadOptions({ fetchAlbums: e.target.checked })}
                  className="w-4 h-4 rounded border-input"
                />
                <span className="text-sm text-foreground">Fetch All Albums</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={downloadOptions.playlistNumbering}
                  onChange={(e) =>
                    updateDownloadOptions({ playlistNumbering: e.target.checked })
                  }
                  className="w-4 h-4 rounded border-input"
                />
                <span className="text-sm text-foreground">Playlist Numbering</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={downloadOptions.generateLrc}
                  onChange={(e) => updateDownloadOptions({ generateLrc: e.target.checked })}
                  className="w-4 h-4 rounded border-input"
                />
                <span className="text-sm text-foreground">Generate LRC Files</span>
              </label>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DownloadPage;

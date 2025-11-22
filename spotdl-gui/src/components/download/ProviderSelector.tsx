import { Music, Type } from 'lucide-react';
import type { AudioProvider, LyricsProvider } from '../../types/spotdl';
import { cn } from '../../lib/utils';

interface ProviderSelectorProps {
  audioProviders: AudioProvider[];
  lyricsProviders: LyricsProvider[];
  onAudioProvidersChange: (providers: AudioProvider[]) => void;
  onLyricsProvidersChange: (providers: LyricsProvider[]) => void;
}

const ProviderSelector = ({
  audioProviders,
  lyricsProviders,
  onAudioProvidersChange,
  onLyricsProvidersChange,
}: ProviderSelectorProps) => {
  const availableAudioProviders: AudioProvider[] = [
    'youtube-music',
    'youtube',
    'slider-kz',
    'soundcloud',
    'bandcamp',
    'piped',
  ];

  const availableLyricsProviders: LyricsProvider[] = [
    'genius',
    'musixmatch',
    'azlyrics',
    'synced',
  ];

  const toggleAudioProvider = (provider: AudioProvider) => {
    if (audioProviders.includes(provider)) {
      onAudioProvidersChange(audioProviders.filter((p) => p !== provider));
    } else {
      onAudioProvidersChange([...audioProviders, provider]);
    }
  };

  const toggleLyricsProvider = (provider: LyricsProvider) => {
    if (lyricsProviders.includes(provider)) {
      onLyricsProvidersChange(lyricsProviders.filter((p) => p !== provider));
    } else {
      onLyricsProvidersChange([...lyricsProviders, provider]);
    }
  };

  return (
    <div className="space-y-6">
      {/* Audio Providers */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <Music className="w-5 h-5 text-primary" />
          <h3 className="font-semibold text-foreground">Audio Providers</h3>
        </div>
        <p className="text-sm text-muted-foreground mb-3">
          Select providers in order of preference (first selected = primary)
        </p>
        <div className="flex flex-wrap gap-2">
          {availableAudioProviders.map((provider) => {
            const isSelected = audioProviders.includes(provider);
            const priority = audioProviders.indexOf(provider);
            return (
              <button
                key={provider}
                onClick={() => toggleAudioProvider(provider)}
                className={cn(
                  'px-4 py-2 rounded-md font-medium transition-all relative',
                  isSelected
                    ? 'bg-primary text-primary-foreground shadow-md'
                    : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                )}
              >
                {isSelected && priority >= 0 && (
                  <span className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-accent text-accent-foreground text-xs flex items-center justify-center font-bold">
                    {priority + 1}
                  </span>
                )}
                {provider}
              </button>
            );
          })}
        </div>
      </div>

      {/* Lyrics Providers */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <Type className="w-5 h-5 text-primary" />
          <h3 className="font-semibold text-foreground">Lyrics Providers</h3>
        </div>
        <p className="text-sm text-muted-foreground mb-3">
          Select providers in order of preference
        </p>
        <div className="flex flex-wrap gap-2">
          {availableLyricsProviders.map((provider) => {
            const isSelected = lyricsProviders.includes(provider);
            const priority = lyricsProviders.indexOf(provider);
            return (
              <button
                key={provider}
                onClick={() => toggleLyricsProvider(provider)}
                className={cn(
                  'px-4 py-2 rounded-md font-medium transition-all relative',
                  isSelected
                    ? 'bg-primary text-primary-foreground shadow-md'
                    : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                )}
              >
                {isSelected && priority >= 0 && (
                  <span className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-accent text-accent-foreground text-xs flex items-center justify-center font-bold">
                    {priority + 1}
                  </span>
                )}
                {provider}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default ProviderSelector;

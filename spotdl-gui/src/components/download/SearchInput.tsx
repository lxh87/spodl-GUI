import { useState } from 'react';
import { Search, Download } from 'lucide-react';
import Input from '../common/Input';
import Button from '../common/Button';

interface SearchInputProps {
  onSearch: (query: string) => void;
  loading?: boolean;
}

const SearchInput = ({ onSearch, loading = false }: SearchInputProps) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim());
    }
  };

  const quickOptions = [
    { label: 'Liked Songs', value: 'saved' },
    { label: 'All Playlists', value: 'all-user-playlists' },
    { label: 'Created Playlists', value: 'all-saved-playlists' },
    { label: 'Followed Artists', value: 'all-user-followed-artists' },
    { label: 'Saved Albums', value: 'all-user-saved-albums' },
  ];

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Paste Spotify/YouTube URL or search query..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="pl-10"
            disabled={loading}
          />
        </div>
        <Button type="submit" disabled={loading || !query.trim()} className="gap-2">
          <Download className="w-4 h-4" />
          Download
        </Button>
      </form>

      <div className="flex flex-wrap gap-2">
        <span className="text-sm text-muted-foreground self-center">Quick select:</span>
        {quickOptions.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => setQuery(option.value)}
            className="px-3 py-1 text-sm rounded-md bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors"
          >
            {option.label}
          </button>
        ))}
      </div>

      <div className="text-xs text-muted-foreground space-y-1 bg-muted/30 p-3 rounded-md">
        <p><strong>Supported formats:</strong></p>
        <ul className="list-disc list-inside space-y-1 ml-2">
          <li>Spotify URLs: Track, Album, Playlist, Artist</li>
          <li>YouTube URLs: Video, Playlist</li>
          <li>Search: Use prefixes like <code className="bg-muted px-1 rounded">album:</code>, <code className="bg-muted px-1 rounded">playlist:</code>, <code className="bg-muted px-1 rounded">artist:</code></li>
          <li>Manual match: <code className="bg-muted px-1 rounded">YouTubeURL|SpotifyURL</code></li>
        </ul>
      </div>
    </div>
  );
};

export default SearchInput;

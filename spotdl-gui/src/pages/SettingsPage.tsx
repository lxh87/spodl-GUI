import { useState } from 'react';
import { useSettingsStore } from '../store/settingsStore';
import Input from '../components/common/Input';
import Button from '../components/common/Button';
import { Save, RotateCcw } from 'lucide-react';

const SettingsPage = () => {
  const { spotifyAuth, updateSpotifyAuth, resetToDefaults } = useSettingsStore();
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    // Settings are automatically saved via Zustand persist middleware
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleReset = () => {
    if (confirm('Are you sure you want to reset all settings to defaults?')) {
      resetToDefaults();
    }
  };

  return (
    <div className="space-y-8 max-w-3xl">
      <div>
        <h2 className="text-3xl font-bold text-foreground mb-2">Settings</h2>
        <p className="text-muted-foreground">
          Configure your SpotDL preferences
        </p>
      </div>

      {/* Spotify Authentication */}
      <div className="bg-card border border-border rounded-lg p-6">
        <h3 className="text-xl font-semibold text-foreground mb-4">Spotify Authentication</h3>
        <div className="space-y-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={spotifyAuth.userAuth}
              onChange={(e) => updateSpotifyAuth({ userAuth: e.target.checked })}
              className="w-4 h-4 rounded border-input"
            />
            <span className="text-sm text-foreground">
              Use OAuth (Login to Spotify)
            </span>
          </label>

          {!spotifyAuth.userAuth && (
            <>
              <Input
                label="Client ID"
                type="text"
                value={spotifyAuth.clientId || ''}
                onChange={(e) => updateSpotifyAuth({ clientId: e.target.value })}
                placeholder="Your Spotify Client ID"
              />

              <Input
                label="Client Secret"
                type="password"
                value={spotifyAuth.clientSecret || ''}
                onChange={(e) => updateSpotifyAuth({ clientSecret: e.target.value })}
                placeholder="Your Spotify Client Secret"
              />

              <div className="text-xs text-muted-foreground bg-muted/30 p-3 rounded-md">
                <p className="mb-2"><strong>How to get credentials:</strong></p>
                <ol className="list-decimal list-inside space-y-1 ml-2">
                  <li>Go to <a href="https://developer.spotify.com/dashboard" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">Spotify Developer Dashboard</a></li>
                  <li>Create a new app</li>
                  <li>Copy the Client ID and Client Secret</li>
                  <li>Paste them above</li>
                </ol>
              </div>
            </>
          )}

          <Input
            label="Authorization Token (Optional)"
            type="password"
            value={spotifyAuth.authToken || ''}
            onChange={(e) => updateSpotifyAuth({ authToken: e.target.value })}
            placeholder="Direct auth token"
          />
        </div>
      </div>

      {/* Save/Reset Actions */}
      <div className="flex gap-4">
        <Button onClick={handleSave} className="gap-2">
          <Save className="w-4 h-4" />
          {saved ? 'Saved!' : 'Save Settings'}
        </Button>
        <Button onClick={handleReset} variant="destructive" className="gap-2">
          <RotateCcw className="w-4 h-4" />
          Reset to Defaults
        </Button>
      </div>

      {/* API Configuration Info */}
      <div className="bg-card border border-border rounded-lg p-6">
        <h3 className="text-xl font-semibold text-foreground mb-4">Backend Configuration</h3>
        <div className="space-y-4">
          <div className="text-sm text-muted-foreground bg-muted/30 p-4 rounded-md">
            <p className="mb-2"><strong>Backend API URL:</strong></p>
            <code className="bg-muted px-2 py-1 rounded">
              {import.meta.env.VITE_API_URL || 'http://localhost:8800/api'}
            </code>
            <p className="mt-3 mb-2"><strong>To change the backend URL:</strong></p>
            <ol className="list-decimal list-inside space-y-1 ml-2">
              <li>Create a <code className="bg-muted px-1 rounded">.env</code> file in the project root</li>
              <li>Add: <code className="bg-muted px-1 rounded">VITE_API_URL=your_backend_url</code></li>
              <li>Restart the development server</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;

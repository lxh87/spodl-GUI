import { Settings2 } from 'lucide-react';
import type { AudioFormat, Bitrate } from '../../types/spotdl';
import Select from '../common/Select';
import Input from '../common/Input';

interface QualitySettingsProps {
  format: AudioFormat;
  bitrate: Bitrate;
  threads: number;
  outputTemplate: string;
  onFormatChange: (format: AudioFormat) => void;
  onBitrateChange: (bitrate: Bitrate) => void;
  onThreadsChange: (threads: number) => void;
  onOutputTemplateChange: (template: string) => void;
}

const QualitySettings = ({
  format,
  bitrate,
  threads,
  outputTemplate,
  onFormatChange,
  onBitrateChange,
  onThreadsChange,
  onOutputTemplateChange,
}: QualitySettingsProps) => {
  const formatOptions: { value: AudioFormat; label: string }[] = [
    { value: 'mp3', label: 'MP3' },
    { value: 'flac', label: 'FLAC (Lossless)' },
    { value: 'ogg', label: 'OGG Vorbis' },
    { value: 'opus', label: 'Opus' },
    { value: 'm4a', label: 'M4A (AAC)' },
    { value: 'wav', label: 'WAV (Uncompressed)' },
  ];

  const bitrateOptions: { value: Bitrate; label: string }[] = [
    { value: 'auto', label: 'Auto (Match Source)' },
    { value: 'disable', label: 'Disable' },
    { value: '320k', label: '320 kbps (Best Quality)' },
    { value: '256k', label: '256 kbps' },
    { value: '192k', label: '192 kbps' },
    { value: '128k', label: '128 kbps' },
    { value: '96k', label: '96 kbps' },
    { value: '64k', label: '64 kbps' },
    { value: '0', label: 'VBR 0 (Best Quality)' },
    { value: '2', label: 'VBR 2 (High Quality)' },
    { value: '4', label: 'VBR 4 (Medium Quality)' },
    { value: '6', label: 'VBR 6 (Standard Quality)' },
  ];

  const templateVariables = [
    '{title}', '{artist}', '{artists}', '{album}', '{album-artist}',
    '{genre}', '{year}', '{track-number}', '{disc-number}', '{output-ext}'
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 mb-4">
        <Settings2 className="w-5 h-5 text-primary" />
        <h3 className="font-semibold text-foreground">Quality & Output Settings</h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Select
          label="Audio Format"
          options={formatOptions}
          value={format}
          onChange={(e) => onFormatChange(e.target.value as AudioFormat)}
        />

        <Select
          label="Bitrate"
          options={bitrateOptions}
          value={bitrate}
          onChange={(e) => onBitrateChange(e.target.value as Bitrate)}
        />

        <Input
          label="Concurrent Downloads (Threads)"
          type="number"
          min={1}
          max={16}
          value={threads}
          onChange={(e) => onThreadsChange(parseInt(e.target.value) || 1)}
        />
      </div>

      <div>
        <Input
          label="Output Filename Template"
          type="text"
          value={outputTemplate}
          onChange={(e) => onOutputTemplateChange(e.target.value)}
          placeholder="{artists} - {title}.{output-ext}"
        />
        <div className="mt-2 text-xs text-muted-foreground">
          <p className="mb-2">Available variables:</p>
          <div className="flex flex-wrap gap-2">
            {templateVariables.map((variable) => (
              <button
                key={variable}
                onClick={() => {
                  onOutputTemplateChange(outputTemplate + variable);
                }}
                className="px-2 py-1 bg-muted rounded text-muted-foreground hover:bg-muted/80 transition-colors font-mono"
              >
                {variable}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="text-xs text-muted-foreground bg-muted/30 p-3 rounded-md">
        <p><strong>Example outputs:</strong></p>
        <ul className="list-disc list-inside mt-1 space-y-1 ml-2">
          <li><code className="bg-muted px-1 rounded">{'{artists} - {title}.{output-ext}'}</code> → "Artist Name - Song Title.mp3"</li>
          <li><code className="bg-muted px-1 rounded">{'{album}/{track-number} - {title}.{output-ext}'}</code> → "Album Name/01 - Song Title.mp3"</li>
        </ul>
      </div>
    </div>
  );
};

export default QualitySettings;

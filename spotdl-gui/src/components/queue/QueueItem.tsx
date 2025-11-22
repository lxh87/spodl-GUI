import { Music, X, Pause, CheckCircle2, AlertCircle, Clock } from 'lucide-react';
import type { DownloadItem } from '../../types/spotdl';
import Button from '../common/Button';
import { cn } from '../../lib/utils';

interface QueueItemProps {
  item: DownloadItem;
  onRemove: (id: string) => void;
}

const QueueItem = ({ item, onRemove }: QueueItemProps) => {
  const getStatusIcon = () => {
    switch (item.status) {
      case 'completed':
        return <CheckCircle2 className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-destructive" />;
      case 'downloading':
      case 'processing':
        return <Music className="w-5 h-5 text-primary animate-pulse" />;
      case 'paused':
        return <Pause className="w-5 h-5 text-muted-foreground" />;
      default:
        return <Clock className="w-5 h-5 text-muted-foreground" />;
    }
  };

  const getStatusColor = () => {
    switch (item.status) {
      case 'completed':
        return 'bg-green-500';
      case 'failed':
        return 'bg-destructive';
      case 'downloading':
      case 'processing':
        return 'bg-primary';
      case 'paused':
        return 'bg-muted-foreground';
      default:
        return 'bg-muted';
    }
  };

  const getStatusText = () => {
    switch (item.status) {
      case 'completed':
        return 'Completed';
      case 'failed':
        return 'Failed';
      case 'downloading':
        return 'Downloading';
      case 'processing':
        return 'Processing';
      case 'paused':
        return 'Paused';
      default:
        return 'Queued';
    }
  };

  return (
    <div className="border border-border rounded-lg p-4 bg-card">
      <div className="flex items-start gap-4">
        {/* Album Art or Icon */}
        <div className="w-16 h-16 rounded bg-secondary flex items-center justify-center flex-shrink-0">
          {item.coverUrl ? (
            <img
              src={item.coverUrl}
              alt={item.title || 'Album cover'}
              className="w-full h-full rounded object-cover"
            />
          ) : (
            <Music className="w-8 h-8 text-muted-foreground" />
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <h4 className="font-semibold text-foreground truncate">
                {item.title || item.query}
              </h4>
              {item.artist && (
                <p className="text-sm text-muted-foreground truncate">{item.artist}</p>
              )}
              {item.album && (
                <p className="text-xs text-muted-foreground truncate">{item.album}</p>
              )}
            </div>

            {/* Status Icon */}
            <div className="flex items-center gap-2">
              {getStatusIcon()}
              <Button
                variant="ghost"
                size="icon"
                onClick={() => onRemove(item.id)}
                className="h-8 w-8"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* Progress Bar */}
          {(item.status === 'downloading' || item.status === 'processing') && (
            <div className="mt-3">
              <div className="flex items-center justify-between text-xs mb-1">
                <span className="text-muted-foreground">{getStatusText()}</span>
                <span className="text-muted-foreground">{Math.round(item.progress)}%</span>
              </div>
              <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className={cn('h-full transition-all duration-300', getStatusColor())}
                  style={{ width: `${item.progress}%` }}
                />
              </div>
            </div>
          )}

          {/* Status Text for other states */}
          {item.status !== 'downloading' && item.status !== 'processing' && (
            <div className="mt-2">
              <span className={cn(
                'text-xs px-2 py-1 rounded-full',
                item.status === 'completed' && 'bg-green-500/10 text-green-500',
                item.status === 'failed' && 'bg-destructive/10 text-destructive',
                item.status === 'queued' && 'bg-muted text-muted-foreground',
                item.status === 'paused' && 'bg-muted text-muted-foreground'
              )}>
                {getStatusText()}
              </span>
            </div>
          )}

          {/* Error Message */}
          {item.error && (
            <div className="mt-2 text-xs text-destructive bg-destructive/10 p-2 rounded">
              {item.error}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default QueueItem;

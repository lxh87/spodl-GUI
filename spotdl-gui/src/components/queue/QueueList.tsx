import { Trash2, CheckCircle } from 'lucide-react';
import { useQueueStore } from '../../store/queueStore';
import QueueItem from './QueueItem';
import Button from '../common/Button';

const QueueList = () => {
  const { items, removeItem, clearCompleted, clearAll } = useQueueStore();

  const hasCompleted = items.some((item) => item.status === 'completed');
  const hasItems = items.length > 0;

  return (
    <div className="space-y-4">
      {/* Header with actions */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Download Queue</h2>
          <p className="text-sm text-muted-foreground">
            {items.length} {items.length === 1 ? 'item' : 'items'} in queue
          </p>
        </div>

        {hasItems && (
          <div className="flex gap-2">
            {hasCompleted && (
              <Button
                variant="outline"
                size="sm"
                onClick={clearCompleted}
                className="gap-2"
              >
                <CheckCircle className="w-4 h-4" />
                Clear Completed
              </Button>
            )}
            <Button
              variant="destructive"
              size="sm"
              onClick={clearAll}
              className="gap-2"
            >
              <Trash2 className="w-4 h-4" />
              Clear All
            </Button>
          </div>
        )}
      </div>

      {/* Queue Items */}
      {hasItems ? (
        <div className="space-y-3">
          {items.map((item) => (
            <QueueItem
              key={item.id}
              item={item}
              onRemove={removeItem}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-16 text-muted-foreground">
          <Music className="w-16 h-16 mx-auto mb-4 opacity-20" />
          <p className="text-lg font-medium">No downloads in queue</p>
          <p className="text-sm mt-2">Start downloading music to see them here</p>
        </div>
      )}
    </div>
  );
};

// Import for the empty state icon
import { Music } from 'lucide-react';

export default QueueList;

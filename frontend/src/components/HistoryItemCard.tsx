import React from 'react';
import { CheckCircle2, AlertCircle, Trash2 } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import type { HistoryItem } from '../types/history';
import { formatHistoryTime, formatDuration } from '../utils/history';
import { useTranslation } from '../lib/i18n-context';

interface HistoryItemCardProps {
  item: HistoryItem;
  onSelect: (item: HistoryItem) => void;
  onDelete: (itemId: string) => void;
}

export function HistoryItemCard({
  item,
  onSelect,
  onDelete,
}: HistoryItemCardProps) {
  const t = useTranslation();

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation(); // 阻止冒泡，避免触发 onSelect
    if (confirm(t.history.deleteConfirm)) {
      onDelete(item.id);
    }
  };

  return (
    <Card
      className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors cursor-pointer group"
      onClick={() => onSelect(item)}
    >
      <div className="p-3 space-y-2">
        {/* Task Text */}
        <p className="text-sm font-medium text-slate-900 dark:text-slate-100 line-clamp-2">
          {item.taskText}
        </p>

        {/* Metadata Row */}
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
            <span>{formatHistoryTime(item.startTime)}</span>
            <span>•</span>
            <span>
              {item.steps} {item.steps === 1 ? 'step' : 'steps'}
            </span>
            <span>•</span>
            <span>{formatDuration(item.duration)}</span>
          </div>

          <div className="flex items-center gap-2">
            {/* Status Badge */}
            <Badge
              variant={item.success ? 'success' : 'destructive'}
              className="shrink-0"
            >
              {item.success ? (
                <>
                  <CheckCircle2 className="w-3 h-3 mr-1" />
                  {t.history.success}
                </>
              ) : (
                <>
                  <AlertCircle className="w-3 h-3 mr-1" />
                  {t.history.failed}
                </>
              )}
            </Badge>

            {/* Delete Button */}
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity text-slate-400 hover:text-red-500 dark:text-slate-500 dark:hover:text-red-400"
              onClick={handleDelete}
              title={t.history.deleteItem}
            >
              <Trash2 className="w-3 h-3" />
            </Button>
          </div>
        </div>
      </div>
    </Card>
  );
}

import type { HistoryItem } from '../types/history';

const MAX_HISTORY_ITEMS = 100;
const FALLBACK_HISTORY_ITEMS = 20; // 当 localStorage 满时降级到的数量

/**
 * 从 Message 对象创建 HistoryItem
 */
export function createHistoryItem(
  deviceId: string,
  deviceName: string,
  userMessage: {
    content: string;
    timestamp: Date;
  },
  agentMessage: {
    content: string;
    timestamp: Date;
    success?: boolean;
    steps?: number;
    thinking?: string[];
    actions?: Record<string, unknown>[];
  }
): HistoryItem {
  return {
    id: Date.now().toString(),
    deviceId: deviceId || 'unknown',
    deviceName: deviceName || 'Unknown Device',
    taskText: userMessage?.content || 'No task description',
    success: agentMessage?.success ?? false,
    steps: agentMessage?.steps ?? 0,
    startTime: userMessage?.timestamp || new Date(),
    endTime: agentMessage?.timestamp || new Date(),
    duration:
      (agentMessage?.timestamp?.getTime() || Date.now()) -
      (userMessage?.timestamp?.getTime() || Date.now()),
    thinking: agentMessage?.thinking ?? [],
    actions: agentMessage?.actions ?? [],
    finalMessage: agentMessage?.content || 'No result message',
    errorMessage:
      agentMessage?.success === false
        ? agentMessage?.content || 'Unknown error'
        : undefined,
  };
}

/**
 * 保存历史记录项到 localStorage
 */
export function saveHistoryItem(deviceId: string, item: HistoryItem): void {
  try {
    const key = `history-${deviceId}`;
    const stored = localStorage.getItem(key);
    const history: HistoryItem[] = stored ? JSON.parse(stored) : [];

    // 添加新项到开头（最新的在前）
    history.unshift(item);

    // 限制最多 100 条
    const limited = history.slice(0, MAX_HISTORY_ITEMS);

    localStorage.setItem(key, JSON.stringify(limited));
  } catch (error) {
    // localStorage quota exceeded
    if (error instanceof Error && error.name === 'QuotaExceededError') {
      console.warn('localStorage quota exceeded, clearing old history');
      try {
        const key = `history-${deviceId}`;
        const stored = localStorage.getItem(key);
        const history: HistoryItem[] = stored ? JSON.parse(stored) : [];

        // 降级到只保留最近 20 条
        const reduced = history.slice(0, FALLBACK_HISTORY_ITEMS);
        reduced.unshift(item);
        localStorage.setItem(key, JSON.stringify(reduced));
      } catch (retryError) {
        console.error(
          'Failed to save history even after reduction:',
          retryError
        );
      }
    } else {
      console.warn('Failed to save history:', error);
    }
  }
}

/**
 * 从 localStorage 加载历史记录
 */
export function loadHistoryItems(deviceId: string): HistoryItem[] {
  try {
    const key = `history-${deviceId}`;
    const stored = localStorage.getItem(key);
    if (!stored) return [];

    const parsed = JSON.parse(stored) as Array<
      Omit<HistoryItem, 'startTime' | 'endTime'> & {
        startTime: string;
        endTime: string;
      }
    >;

    // 将日期字符串转回 Date 对象
    return parsed.map(item => ({
      ...item,
      startTime: new Date(item.startTime),
      endTime: new Date(item.endTime),
    }));
  } catch (error) {
    console.warn('Failed to load history:', error);
    return [];
  }
}

/**
 * 删除单条历史记录
 */
export function deleteHistoryItem(deviceId: string, itemId: string): void {
  try {
    const key = `history-${deviceId}`;
    const stored = localStorage.getItem(key);
    if (!stored) return;

    const history: HistoryItem[] = JSON.parse(stored);
    const filtered = history.filter(item => item.id !== itemId);

    localStorage.setItem(key, JSON.stringify(filtered));
  } catch (error) {
    console.warn('Failed to delete history item:', error);
  }
}

/**
 * 清空设备的所有历史记录
 */
export function clearHistory(deviceId: string): void {
  try {
    const key = `history-${deviceId}`;
    localStorage.removeItem(key);
  } catch (error) {
    console.warn('Failed to clear history:', error);
  }
}

/**
 * 格式化时间显示（相对时间或绝对时间）
 */
export function formatHistoryTime(timestamp: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - timestamp.getTime();
  const diffMinutes = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMinutes < 1) return 'Just now';
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  // 绝对时间
  return timestamp.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * 格式化执行时长
 */
export function formatDuration(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;

  if (minutes === 0) {
    return `${seconds}s`;
  }
  return `${minutes}m ${seconds}s`;
}

/**
 * 按日期分组历史记录
 */
export function groupHistoryByDate(items: HistoryItem[]): {
  today: HistoryItem[];
  yesterday: HistoryItem[];
  earlier: HistoryItem[];
} {
  const now = new Date();
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterdayStart = new Date(todayStart);
  yesterdayStart.setDate(yesterdayStart.getDate() - 1);

  return items.reduce(
    (groups, item) => {
      const itemDate = new Date(item.startTime);
      if (itemDate >= todayStart) {
        groups.today.push(item);
      } else if (itemDate >= yesterdayStart) {
        groups.yesterday.push(item);
      } else {
        groups.earlier.push(item);
      }
      return groups;
    },
    {
      today: [] as HistoryItem[],
      yesterday: [] as HistoryItem[],
      earlier: [] as HistoryItem[],
    }
  );
}

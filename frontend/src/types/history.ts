export interface HistoryItem {
  id: string; // 唯一标识符
  deviceId: string; // 设备 ID
  deviceName: string; // 设备名称（显示用）
  taskText: string; // 用户任务描述
  success: boolean; // 执行成功/失败
  steps: number; // 总步数
  startTime: Date; // 开始时间
  endTime: Date; // 结束时间
  duration: number; // 执行时长（毫秒）

  // 详情数据（展开时显示）
  thinking: string[]; // 每步的思考过程
  actions: Record<string, unknown>[]; // 每步的执行动作
  finalMessage: string; // 最终结果消息
  errorMessage?: string; // 错误信息（失败时）
}

export interface DeviceHistory {
  deviceId: string;
  items: HistoryItem[];
  lastUpdated: Date;
}

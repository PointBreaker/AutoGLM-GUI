# 开发日志

## [2025-12-29] Bug 修复 - 设备列表布局与导入错误

### 问题发现

1. **左侧设备名被按钮遮挡**
   - 问题：设备卡片中的操作按钮（WiFi、断开、删除）占用过多空间，导致设备名显示为 "192.16..." 被截断
   - 影响：用户无法看到完整的设备名称

2. **后端导入错误**
   - 问题：`devices.py` 中导入了不存在的 `run_adb_command` 函数
   - 错误信息：`ImportError: cannot import name 'run_adb_command' from 'AutoGLM_GUI.platform_utils'`
   - 影响：断开所有连接功能无法使用

### 修复内容

1. **DeviceCard 布局优化**
   - 将操作按钮（WiFi 连接、断开 WiFi、断开所有、删除）默认隐藏
   - 鼠标悬停时才显示操作按钮 (`opacity-0 group-hover:opacity-100`)
   - 缩小按钮尺寸 (`h-7 w-7`)
   - Agent 状态徽章更紧凑，只显示图标不显示文字
   - 设备名区域使用 `flex-1 min-w-0` 确保可以正确截断

2. **修复后端导入**
   - 将 `run_adb_command` 改为 `run_cmd_silently_sync`
   - 这是 `platform_utils.py` 中实际存在的函数

### 技术要点

1. **CSS Flexbox 布局优化**
   ```tsx
   {/* 设备信息区域 - 可伸缩 */}
   <div className="flex-1 min-w-0 flex flex-col justify-center gap-0.5">
     <span className="truncate">...</span>
   </div>

   {/* 按钮区域 - 固定宽度，悬停显示 */}
   <div className="flex items-center gap-1 flex-shrink-0">
     <div className="opacity-0 group-hover:opacity-100 transition-opacity">
       {/* 操作按钮 */}
     </div>
   </div>
   ```

2. **正确的函数调用**
   ```python
   # 错误
   from AutoGLM_GUI.platform_utils import run_adb_command
   run_adb_command([...], timeout=5)

   # 正确
   from AutoGLM_GUI.platform_utils import run_cmd_silently_sync
   run_cmd_silently_sync([...], timeout=5)
   ```

### 文件变更

**修改文件:**
- `frontend/src/components/DeviceCard.tsx`: 布局优化，按钮悬停显示
- `AutoGLM_GUI/api/devices.py`: 修复导入错误

### 测试状态

- [x] 后端导入错误修复
- [x] 前端布局优化完成
- [ ] 功能测试

---

## [2025-12-29] Bug 修复 - DeviceManager 缺失方法与属性访问错误

### 问题发现

1. **`get_device_by_serial` 方法缺失**
   - 问题：`devices.py` 中的 `delete_device` 和 `disconnect_all_connections` 函数调用了 `device_manager.get_device_by_serial(serial)`，但该方法未实现
   - 影响：删除设备和断开所有连接功能会抛出 AttributeError

2. **属性访问错误**
   - 问题：`devices.py` 中使用 `device.device_id` 访问设备 ID，但 ManagedDevice 类中应使用 `primary_device_id`
   - 问题：`device.connection_type` 返回的是 ConnectionType 枚举，需要用 `.value` 获取字符串值

### 修复内容

1. **在 DeviceManager 中添加 `get_device_by_serial` 方法**
   - 新增 `device_manager.py:324-334` 行
   - 通过硬件序列号查找设备

2. **修复 `devices.py` 中的属性访问**
   - `delete_device` 函数：
     - `device.device_id` → `device.primary_device_id`
     - `device.connection_type == "wifi"` → `device.connection_type.value == "wifi"`
   - `disconnect_all_connections` 函数：
     - 同样的属性访问修复
     - 循环中 `d.connection_type in ("wifi", "remote")` → `d.connection_type.value in ("wifi", "remote")`
     - `d.device_id` → `d.primary_device_id`

### 文件变更

**修改文件:**
- `AutoGLM_GUI/device_manager.py`: 添加 `get_device_by_serial()` 方法
- `AutoGLM_GUI/api/devices.py`: 修复 `delete_device` 和 `disconnect_all_connections` 中的属性访问

### 测试状态

- [x] 代码修改完成
- [ ] 功能测试

---

## [2025-12-29] Bug 修复 - 设备名显示与重命名功能

### 修复内容

1. **左侧设备列表缺少设备名**
   - 问题：WiFi 连接的设备显示 IP 地址而非设备型号
   - 原因：`adb devices -l` 输出中 WiFi 设备可能不包含 model 信息
   - 修复：添加 `get_device_model()` 函数，通过 `adb shell getprop ro.product.model` 获取设备型号作为回退

2. **聊天界面双击重命名不生效**
   - 问题：双击设备名修改后点击确认，名称不变
   - 原因：`chat.tsx` 中 `loadDevices()` 未被 await，导致状态未及时更新
   - 修复：在 `onRename` 回调中添加 `await loadDevices()`

3. **类似问题修复**
   - DeviceSidebar.tsx 中 `onDisconnectAll`、`onRename`、`onDelete` 回调的 `onRefreshDevices?.()` 未被 await
   - 统一修改为 `if (onRefreshDevices) await onRefreshDevices();`

### 文件变更

**新增函数:**
- `AutoGLM_GUI/adb_plus/device.py`: 添加 `get_device_model()` 函数

**修改文件:**
- `AutoGLM_GUI/adb_plus/__init__.py`: 导出 `get_device_model`
- `AutoGLM_GUI/device_manager.py`: 在 `_create_managed_device()` 和 `_poll_devices()` 中添加 model 获取回退逻辑
- `frontend/src/routes/chat.tsx`: `onRename` 回调中 `loadDevices()` 添加 await
- `frontend/src/components/DeviceSidebar.tsx`: `onDisconnectAll`、`onRename`、`onDelete` 回调中 `onRefreshDevices` 添加 await

### 测试状态

- [x] 后端代码修改完成
- [x] 前端代码修改完成
- [ ] 功能测试

---

## [2025-12-29] 双模型决策链路增强

### 实现内容

1. **异常检测机制**
   - 截图重复检测：通过 MD5 哈希比对连续截图
   - 连续失败检测：追踪操作失败次数
   - 重复操作检测：检测相同操作多次执行无效果
   - 异常上下文生成：将异常信息传递给决策模型

2. **决策模型提示词增强**
   - 添加异常处理指南：屏幕无变化、多次操作无效、意外弹窗、目标不存在
   - 新增 wait、retry 动作类型
   - 多角度分析策略指导
   - 保底方案建议

3. **快速模式支持**
   - 添加 ThinkingMode 枚举 (fast/deep)
   - 快速模式使用精简提示词
   - 深度模式使用完整提示词
   - 前端支持切换思考模式

4. **API 层更新**
   - `/api/dual/init` 增加 thinking_mode 参数
   - 返回 thinking_mode 字段

### 技术要点

1. **AnomalyState 类**
   ```python
   @dataclass
   class AnomalyState:
       consecutive_failures: int = 0
       consecutive_same_screen: int = 0
       last_screenshot_hash: str = ""
       last_action: str = ""
       repeated_actions: int = 0
   ```
   - 截图哈希比对
   - 失败计数器
   - 操作重复检测
   - 异常上下文生成

2. **双模型协调器增强**
   - 在 `_execute_step()` 中集成异常检测
   - 将异常上下文添加到决策请求
   - 支持 wait 动作（等待2秒）

3. **决策模型增强**
   - 根据 ThinkingMode 选择提示词
   - `DECISION_SYSTEM_PROMPT`: 完整版，包含异常处理指南
   - `DECISION_SYSTEM_PROMPT_FAST`: 精简版，快速响应

### 文件变更

**修改文件:**
- `AutoGLM_GUI/dual_model/protocols.py`: 添加 ThinkingMode 枚举和增强提示词
- `AutoGLM_GUI/dual_model/dual_agent.py`: 添加 AnomalyState 类和异常检测逻辑
- `AutoGLM_GUI/dual_model/decision_model.py`: 支持 ThinkingMode
- `AutoGLM_GUI/api/dual_model.py`: API 支持 thinking_mode 参数
- `frontend/src/api.ts`: 添加 thinking_mode 类型定义
- `frontend/src/components/DevicePanel.tsx`: 传递 thinking_mode 到初始化

### 测试状态

- [x] 类型检查通过
- [ ] 异常检测功能测试
- [ ] 快速/深度模式切换测试

---

## [2025-12-29] 设备管理 UX 优化与 Bug 修复

### 实现内容

1. **设备重命名改为弹窗形式**
   - 将内联编辑框改为标准弹窗对话框
   - 支持双击设备名快速触发重命名
   - DeviceCard 和 DevicePanel 两处都支持双击重命名
   - 添加设备别名提示文字

2. **思考模式移至聊天界面**
   - 思考模式从全局设置移到每个设备单独选择
   - 在双重模型图标后面显示快速(⚡)和深度(🎯)模式按钮
   - 每个设备可独立选择思考模式，互不影响

3. **断开设备所有连接功能**
   - 新增断开所有连接按钮（🔌图标）
   - 支持一键断开 USB 和 WiFi 连接
   - 同时清理关联的 Agent 状态
   - 添加确认对话框

4. **停止按钮立即响应修复**
   - 修复点击停止按钮后 UI 仍显示 "Processing..." 的问题
   - 优化 SSE 连接关闭逻辑
   - 立即更新消息状态为中止状态
   - 后端 abort 请求改为非阻塞调用

### 技术要点

1. **DeviceCard 组件**
   - 添加 `onDisconnectAll` prop
   - 重构编辑逻辑为弹窗形式
   - 添加 `handleDoubleClick` 事件处理
   - 使用 `Dialog` 组件替代内联 `Input`

2. **DevicePanel 组件**
   - 添加 `thinkingMode` 和 `onThinkingModeChange` props
   - 添加 `onRename` prop 支持聊天界面重命名
   - 添加重命名弹窗和思考模式切换按钮
   - 优化 `handleAbortChat` 函数立即更新 UI 状态

3. **后端新增 API**
   - `POST /api/devices/{serial}/disconnect_all`: 断开设备所有连接

4. **前端状态管理**
   - 在 chat.tsx 中添加 `deviceThinkingModes` 状态
   - 使用 device.serial 作为 key 存储每个设备的思考模式

### 文件变更

**修改文件:**
- `frontend/src/components/DeviceCard.tsx`: 弹窗重命名、断开所有连接按钮
- `frontend/src/components/DevicePanel.tsx`: 双击重命名、思考模式按钮、abort 优化
- `frontend/src/components/DeviceSidebar.tsx`: 传递 onDisconnectAll prop
- `frontend/src/routes/chat.tsx`: 设备思考模式状态、重命名回调
- `frontend/src/api.ts`: 添加 disconnectAllConnections API
- `frontend/src/lib/locales/zh.ts`: 添加新翻译
- `frontend/src/lib/locales/en.ts`: 添加新翻译
- `AutoGLM_GUI/api/devices.py`: 添加断开所有连接 API

### 测试状态

- [ ] 类型检查
- [ ] 功能测试

---

## [2025-12-29] 配置管理增强与设备管理功能

### 实现内容

1. **决策模型配置管理**
   - 在全局配置中添加决策模型参数配置（Base URL、API Key、模型名称）
   - 添加思考模式选择（快速/深度）
   - 双模型开关状态持久化

2. **设备别名管理**
   - 支持为设备设置自定义显示名称
   - 别名持久化存储在 `~/.config/autoglm/device_aliases.json`
   - 设备卡片上悬停显示编辑按钮

3. **设备删除功能**
   - 支持彻底删除设备（断开连接、清理 Agent、移除别名）
   - 删除前有确认对话框

4. **配置界面优化**
   - 思考模式切换按钮（快速/深度）
   - 可折叠的高级设置区域（决策模型配置）
   - 动态显示决策模型名称

### 技术要点

1. **后端新增**
   - `DeviceAliasManager`: 设备别名管理器（单例模式）
   - 配置 API 扩展支持新字段
   - 设备别名 API：GET/PUT/DELETE `/api/devices/{serial}/alias`
   - 设备删除 API：DELETE `/api/devices/{serial}`

2. **前端更新**
   - `DeviceCard`: 添加重命名和删除功能
   - `DeviceSidebar`: 传递新的 props 给 DeviceCard
   - `chat.tsx`: 配置对话框添加思考模式和决策模型配置
   - `DevicePanel`: 使用配置值初始化双模型

3. **i18n 更新**
   - 添加思考模式相关翻译
   - 添加决策模型配置相关翻译
   - 添加设备删除相关翻译

### 文件变更

**新增文件:**
- `AutoGLM_GUI/device_alias_manager.py`: 设备别名管理器

**修改文件:**
- `AutoGLM_GUI/config_manager.py`: 添加 thinking_mode 字段
- `AutoGLM_GUI/schemas.py`: 扩展配置响应和请求 schema
- `AutoGLM_GUI/api/agents.py`: 更新配置 API 端点
- `AutoGLM_GUI/api/devices.py`: 添加别名和删除端点
- `frontend/src/api.ts`: 添加新的 API 类型和函数
- `frontend/src/routes/chat.tsx`: 添加配置界面增强
- `frontend/src/components/DeviceCard.tsx`: 添加重命名和删除 UI
- `frontend/src/components/DeviceSidebar.tsx`: 传递新 props
- `frontend/src/components/DevicePanel.tsx`: 使用配置值
- `frontend/src/components/DualModelPanel.tsx`: 接收动态模型名称
- `frontend/src/lib/locales/en.ts`: 添加新翻译
- `frontend/src/lib/locales/zh.ts`: 添加新翻译

### 测试状态

- [x] 类型检查通过
- [ ] 功能测试

---

## [2025-12-28] 双模型协作功能 - Bug修复

### 修复内容

修复了 `'Screenshot' object has no attribute 'data'` 错误：
- 问题表现：双模型模式下循环在 vision_start 事件，无法进入决策阶段
- 根因：vision_model.py 使用了错误的 Screenshot 属性名
- 修复：将 `screenshot.data`/`screenshot.base64` 改为 `screenshot.base64_data`

### 文件变更

**修改文件:**
- `AutoGLM_GUI/dual_model/vision_model.py`: 修正 capture_screenshot() 返回值
- `AutoGLM_GUI/dual_model/dual_agent.py`: 适配新的返回值签名

### 测试状态

- [x] 服务器启动正常
- [ ] 双模型功能测试

---

## [2025-12-28] 双模型协作功能 - 前端集成

### 实现内容

完成了双模型功能的前端集成：
- 在 DevicePanel 组件中添加了双模型切换按钮（紫色 Brain 图标）
- 集成了 DualModelPanel 组件用于显示双模型状态
- 实现了双模型流式消息发送功能
- 更新了 Reset 和 Abort 功能以支持双模型模式

### 技术要点

1. **前端组件更新**
   - 导入 `DualModelPanel` 和 `useDualModelState`
   - 导入双模型 API 函数：`initDualModel`, `sendDualModelStream`, `abortDualModelChat`, `resetDualModel`
   - 添加双模型状态变量：`dualModelEnabled`, `dualModelInitialized`
   - 添加双模型流引用：`dualModelStreamRef`

2. **新增功能函数**
   - `handleInitDualModel()`: 初始化双模型 Agent
   - `handleToggleDualModel()`: 切换双模型模式
   - `handleSendDualModel()`: 使用双模型发送消息
   - `handleSendMessage()`: 统一发送函数，根据模式选择单/双模型

3. **UI 更新**
   - 头部添加紫色双模型切换按钮
   - 启用双模型时显示 DualModelPanel 状态面板
   - DualModelPanel 显示：任务计划、大模型状态、小模型状态、进度

### 文件变更

**修改文件:**
- `frontend/src/components/DevicePanel.tsx`: 集成双模型功能

## [2025-12-28] 双模型协作功能

### 实现内容

实现了大模型+小模型的协作机制：
- 大模型(GLM-4.7)：负责任务分析、决策制定、内容生成
- 小模型(autoglm-phone)：负责屏幕识别、动作执行

### 技术要点

1. **后端架构**
   - `DecisionModel`: 决策大模型客户端，支持流式输出和 reasoning_content 解析
   - `VisionModel`: 视觉小模型适配器，复用现有的 ModelClient 和 ActionHandler
   - `DualModelAgent`: 双模型协调器，管理协作流程和状态

2. **API设计**
   - `POST /api/dual/init`: 初始化双模型Agent
   - `POST /api/dual/chat/stream`: 流式聊天(SSE)
   - `POST /api/dual/chat/abort`: 中止任务
   - `GET /api/dual/status`: 获取状态
   - `POST /api/dual/reset`: 重置Agent

3. **前端组件**
   - `DualModelPanel`: 双模型状态显示组件
   - `useDualModelState`: 状态管理Hook
   - 扩展了 api.ts 支持双模型API调用

4. **SSE事件类型**
   - `decision_start/thinking/result`: 大模型相关事件
   - `vision_start/recognition`: 小模型识图事件
   - `action_start/result`: 动作执行事件
   - `task_plan`: 任务计划事件
   - `step_complete/task_complete`: 进度事件

### 文件变更

**新增文件:**
- `AutoGLM_GUI/dual_model/__init__.py`
- `AutoGLM_GUI/dual_model/protocols.py`
- `AutoGLM_GUI/dual_model/decision_model.py`
- `AutoGLM_GUI/dual_model/vision_model.py`
- `AutoGLM_GUI/dual_model/dual_agent.py`
- `AutoGLM_GUI/api/dual_model.py`
- `frontend/src/components/DualModelPanel.tsx`
- `docs/dual_model.md`
- `docs/development_log.md`

**修改文件:**
- `AutoGLM_GUI/api/__init__.py`: 注册双模型路由
- `AutoGLM_GUI/config_manager.py`: 添加双模型配置字段
- `frontend/src/api.ts`: 添加双模型API类型和函数

### 测试状态

- [ ] 后端API测试
- [ ] 前端组件测试
- [ ] 集成测试

### 备注

- 大模型使用 ModelScope 的 GLM-4.7，支持 reasoning_content 字段
- 小模型复用现有的 autoglm-phone 模型
- 双模型模式需要分别配置两个模型的 API Key

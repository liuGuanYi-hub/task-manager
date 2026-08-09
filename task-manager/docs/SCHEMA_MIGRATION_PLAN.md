# Task Manager 数据结构迁移方案

## 文档状态

- 当前状态：设计评审，未执行数据库或模型修改
- 当前基线：JSON 导出 `schema_version=1`；SQLite `metadata.schema_version=1`
- 适用范围：子任务、提醒、重复任务、专注工时和后续看板排序/依赖
- 实施前提：需要用户明确允许核心 schema、JSON 兼容和 API payload 变更

## 1. 当前基线与风险

当前 `Task` 字段包括标题、描述、优先级、状态、创建时间、截止时间、更新时间、完成时间、归档、标签和 `project_id`，没有父任务、重复规则、提醒时间或工时记录。

当前数据边界有三个特点：

1. JSON 内部任务文件没有显式版本字段，但完整导出会写入 `schema_version=1`；导入缺少版本时按 v1 兼容。
2. SQLite 有 `metadata.schema_version`，但初始化逻辑目前只创建 v1 表，没有迁移 runner。
3. API v1 的任务创建/更新和备份导入都只接受现有字段，任务 ID 和项目 ID 冲突支持 remap、skip、replace。

因此不能直接在 `Task` dataclass、SQLite `CREATE TABLE`、JSON 校验和 API 解析器中同时加字段；否则旧 JSON、旧 SQLite、旧 API 客户端和导入 ID 映射会出现不一致。

## 2. 分阶段版本方案

### v1 → v2：迁移基础设施 + 子任务关系

第一步只建立版本迁移骨架，并加入最小的父子关系：

- JSON：内部 payload 和导出 payload 明确写出 `schema_version: 2`；读取缺失版本视为 v1，先在内存中补默认值，再由下一次安全写入升级。
- SQLite：读取 metadata 版本，使用显式迁移函数逐版本执行；每个版本在一个事务中完成，成功后才更新 metadata。
- Task：增加 nullable `parent_id`，指向同一任务表；删除父任务时暂时采用 `ON DELETE SET NULL`，避免级联删除用户任务。
- 业务校验：禁止 `parent_id == id`、不存在的父任务和形成环的关系；父子任务默认要求同一 `project_id`，防止项目级隔离被绕过。
- JSON 导入：先完成任务 ID remap，再按映射更新 `parent_id`；父任务缺失或形成环时整批拒绝，不部分写入。

### v2 → v3：提醒字段与提醒状态

在迁移基础设施稳定后再增加：

- `reminder_at`：nullable ISO 日期时间，统一使用现有 `parse_datetime`。
- 提醒查询只返回未归档、未完成且已到时间窗口的任务；保存失败不影响任务主体。
- API/JSON/SQLite 均允许字段缺失并按 `null` 读取，旧客户端不需要携带新字段。
- 暂不加入后台通知服务；先提供查询和 UI 展示，避免把调度、时区和进程常驻混入同一迁移。

### v3 → v4：有限重复规则与 occurrence 记录

重复任务不能通过覆盖同一个任务的完成状态实现，否则会丢失历史。建议单独设计：

- `repeat_rule` 使用受限结构，而不是自由文本；第一版只支持每日/每周、间隔和星期集合。
- 新增 occurrence/实例记录，保存计划日期、完成时间、跳过状态和来源任务 ID。
- “跳过本次”只关闭当前 occurrence，不修改规则本身。
- 规则计算必须有最大展开窗口和时区策略，拒绝无法解析的规则。

### v4 → v5：专注工时与计划时长

当前 13.1 专注计时只保存在浏览器 `localStorage`。要进入数据层，建议独立表而不是继续膨胀 Task：

- `time_entries`：`id`、`task_id`、`started_at`、`ended_at`、`duration_seconds`、`source`、`created_at`。
- 计时记录独立于任务完成状态，暂停/结束不会重复累计。
- API 采用新增资源或明确动作接口，避免把浏览器计时状态直接覆盖到 Task PATCH。
- 统计先按任务/项目/日期聚合，再考虑周报和导出。

### 后续版本：看板排序与依赖

排序和依赖不与 v2/v3 混做：

- 排序需要明确作用域（项目、视图还是看板列）和稳定 tie-breaker。
- 依赖需要 `task_dependencies` 独立关系表，并在写入时检测环；不能只用逗号分隔 ID。
- 迁移前先做查询计划和索引设计，避免新增字段后破坏现有 SQLite 分页性能。

## 3. 迁移 runner 设计

建议新增一个只负责版本编排的迁移模块：

```text
read_version()
backup_before_migrate()
for target_version in (current + 1 ... latest):
    begin transaction
    validate preconditions
    apply migration
    update schema_version
    commit
on failure: rollback and keep original backup
```

具体约束：

- 迁移必须幂等；重复启动不能重复创建关系或重复写 occurrence。
- SQLite 迁移使用事务和 `PRAGMA foreign_keys=ON`；失败不得留下半个版本。
- JSON 迁移使用同目录临时文件、`fsync` 和原子替换，替换前保留带时间戳的备份。
- CLI 先提供 `migration-plan`/dry-run，输出版本、记录数、错误数和预计变更，不输出任务正文或敏感配置。
- Web/API 在迁移失败时返回明确错误，不自动删除或重置原文件。

## 4. API 与备份兼容策略

### API

- 继续保持 `/api/v1`，新增字段默认可选，旧请求行为不变。
- 返回的新字段在旧数据上为 `null`、空数组或明确的默认值。
- 父子任务可先通过任务详情中的 `parent_id` 和 `subtask_summary` 暴露；批量关系操作另设明确接口。
- 错误响应沿用 `{error: {code, message}}`，新增 `migration_required`、`cycle_detected` 等稳定 code。

### JSON/SQLite 导入导出

- 导出 payload 顶层记录 schema 版本和可选 feature 列表。
- 导入顺序固定为：版本识别 → 结构迁移 → 基础字段校验 → ID 映射 → 关系校验 → 预览/写入。
- `parent_id`、occurrence 和 time entry 的 ID 映射必须在冲突策略中统一处理。
- `replace` 仍只替换明确冲突实体；失败恢复到迁移前快照。

## 5. 回滚与数据安全

迁移前必须满足：

- 自动生成可验证的 JSON/SQLite 备份，并记录源版本和目标版本。
- dry-run 能在不写用户文件的情况下报告无效父引用、循环关系、日期解析错误和重复 ID。
- 迁移失败时保留原始文件、临时文件和错误摘要，禁止静默删除。
- 完成后执行旧备份恢复演练，再允许切换默认读写版本。

## 6. 验收清单

实施每个版本时必须新增对应测试：

- v1 旧 JSON、旧 SQLite 可以读取，schema 缺失按兼容默认处理。
- 迁移重复执行结果不变，版本号不会回退或跳过。
- 父任务自引用、跨项目父引用和环形关系都会被拒绝且原数据不变。
- JSON/SQLite 导出再导入后父子关系、项目隔离和归档状态保持一致。
- API 旧请求、分页、认证、备份导入和错误结构不回归。
- 迁移失败、磁盘写入失败和非法输入都能恢复，不覆盖原始数据。
- time entry 和 occurrence 只有在各自版本实施时才加入测试与 API 文档。

## 7. 当前确认门槛

本文件完成的是设计和风险审计，当前没有修改：

- `models/task.py`
- `storage/json_storage.py`
- `storage/sqlite_storage.py`
- `routes/api_routes.py`
- JSON/SQLite 文件

开始 v1 实施前，需要明确确认：

1. 是否允许为 JSON/SQLite 引入正式 schema 迁移 runner。
2. 是否接受第一批增加 `Task.parent_id` 及其导入/API/备份字段。
3. 是否接受迁移前自动创建备份和新增 dry-run CLI。

未获得确认前，继续维护当前 v1 数据契约，并只推进不改 schema 的 UI、文档和质量工作。

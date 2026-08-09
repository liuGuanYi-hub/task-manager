# Task Manager API v1

## 基础信息

- Base path：`/api/v1`
- 发现入口：`GET /api/v1`
- 健康检查：`GET /api/v1/health`
- 默认分页：20 条
- 最大分页：100 条
- 日期：接受 ISO 8601 日期或日期时间；带时区输入会转换为本地无时区时间

访问 `GET /api/v1` 可以获得当前版本、认证方式、分页限制和端点列表。该响应适合 CLI、脚本或前端在启动时做能力发现。

## 认证

本地未设置 `TASK_MANAGER_API_TOKEN` 时，API 保持开发兼容模式。部署时在安全配置中设置该环境变量：

```powershell
$env:TASK_MANAGER_API_TOKEN = "YOUR_API_TOKEN"
```

配置 token 后，除 `/api/v1` 和 `/api/v1/health` 外的 API 都需要：

```text
Authorization: Bearer YOUR_API_TOKEN
```

不要把真实 token 写入代码、文档、日志或 Git。

## 端点

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1` | API 版本和能力发现 |
| GET | `/api/v1/health` | 健康检查和存储后端 |
| GET | `/api/v1/tasks` | 分页查询任务 |
| POST | `/api/v1/tasks` | 创建任务 |
| GET | `/api/v1/tasks/<id>` | 查看任务 |
| PATCH | `/api/v1/tasks/<id>` | 局部更新任务 |
| DELETE | `/api/v1/tasks/<id>` | 归档任务 |
| GET | `/api/v1/projects` | 分页查询项目 |
| POST | `/api/v1/projects` | 创建项目 |
| GET | `/api/v1/projects/<id>` | 查看项目及其任务 |

`DELETE /tasks/<id>` 是可恢复语义的归档，不是永久删除。

## 任务字段

创建任务时 `title` 必填；其他字段可使用以下格式：

```json
{
  "title": "整理项目资料",
  "description": "准备本周汇报",
  "priority": "高",
  "status": "待办",
  "due_date": "2026-08-12T18:00:00",
  "tags": ["项目", "汇报"],
  "project_id": 1
}
```

可选 `priority`：`低`、`中`、`高`。

可选 `status`：`待办`、`进行中`、`已完成`。

`project_id` 必须指向现有项目，也可以传 `null` 表示未归属项目。`PATCH` 只校验并更新请求体中出现的字段。

## 查询和分页

任务列表支持：

```text
GET /api/v1/tasks?page=2&page_size=20
GET /api/v1/tasks?status=进行中&priority=高
GET /api/v1/tasks?statuses=待办,进行中&project_id=1
GET /api/v1/tasks?include_archived=1&sort_by=due_date&reverse=1
```

项目列表和项目详情中的任务也支持 `page`、`page_size`。集合响应统一使用：

```json
{
  "data": [],
  "meta": {
    "page": 1,
    "page_size": 20,
    "pages": 0,
    "total": 0,
    "count": 0,
    "returned": 0
  }
}
```

## 错误响应

错误响应统一为：

```json
{
  "error": {
    "code": "not_found",
    "message": "任务不存在"
  }
}
```

常见状态码：

- `400`：请求体或查询参数无效
- `401`：缺少或错误的 Bearer Token
- `404`：任务、项目或路径不存在
- `500`：服务器暂时无法处理请求

## 最小 smoke 示例

```bash
curl http://localhost:5000/api/v1
curl http://localhost:5000/api/v1/health
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
  "http://localhost:5000/api/v1/tasks?page=1&page_size=20"
```

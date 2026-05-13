# 自习座位预约系统 - API 接口文档（草案）

> 版本：v1.0（草案）  
> 适用范围：学生端、管理端、AI 助手模块  
> 状态：待开发组评审确认后定稿

---

## 1. 通用规范

### 1.1 Base URL
```
/api/v1
```

### 1.2 请求格式
- 所有请求均为 `application/json`（除文件上传外）。
- 日期时间统一采用 ISO 8601 格式，如 `2025-04-14T09:00:00`。

### 1.3 认证方式
- 采用 **JWT（Bearer Token）** 认证。
- 登录成功后，服务端返回 `access_token`。
- 后续请求在 Header 中携带：
  ```
  Authorization: Bearer <access_token>
  ```

### 1.4 统一响应格式
```json
{
  "code": 200,
  "message": "success",
  "data": { }
}
```

**字段说明**：
- `code`：业务状态码，`200` 表示成功，其他为具体错误码。
- `message`：提示信息。
- `data`：实际返回数据，失败时可能为 `null`。

### 1.5 公共错误码

| 错误码 | 含义 | 说明 |
|--------|------|------|
| `200` | 成功 | 请求处理成功 |
| `400` | 参数错误 | 请求参数缺失或格式不正确 |
| `401` | 未认证 | Token 缺失、过期或无效 |
| `403` | 无权限 | 用户没有该接口的操作权限 |
| `404` | 资源不存在 | 请求的数据未找到 |
| `409` | 资源冲突 | 如座位已被预约、角色下仍有用户等 |
| `500` | 服务器错误 | 服务端内部异常 |

### 1.6 分页规范
列表接口默认支持分页，请求参数与响应格式如下：

**请求参数**：
```json
{
  "page": 1,
  "per_page": 20
}
```

**响应数据**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [ ],
    "total": 100,
    "page": 1,
    "per_page": 20,
    "pages": 5
  }
}
```

---

## 2. 学生端接口

### 2.1 认证相关

#### POST `/student/auth/login`
**描述**：学生登录

**请求体**：
```json
{
  "username": "2025123456",
  "password": "123456"
}
```

**响应示例**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
    "token_type": "Bearer",
    "expires_in": 86400,
    "user": {
      "id": 3,
      "username": "2025123456",
      "name": "张三",
      "user_type": "student",
      "department": "计算机学院"
    }
  }
}
```

---

### 2.2 个人信息

#### GET `/student/profile`
**描述**：获取当前学生个人信息

**响应示例**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 3,
    "username": "2025123456",
    "name": "张三",
    "department": "计算机学院",
    "email": "2025123456@fdu.edu.cn",
    "active_reservations": 1,
    "total_violations": 0
  }
}
```

---

### 2.3 自习室与座位查询

#### GET `/student/rooms`
**描述**：查看可用自习室列表

**查询参数**：
- `room_type`（可选）：`public` | `department`
- `date`（可选）：查询日期，如 `2025-04-14`

**响应示例**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "name": "理科图书馆 301 自习室",
        "location": "理科图书馆 3楼",
        "room_type": "public",
        "open_time": "07:00:00",
        "close_time": "22:00:00",
        "available_seats": 45
      }
    ]
  }
}
```

#### GET `/student/rooms/{room_id}/seats`
**描述**：查询指定自习室的座位及可用时间段

**查询参数**：
- `date`（必填）：查询日期，如 `2025-04-14`

**响应示例**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "room": { "id": 1, "name": "理科图书馆 301 自习室" },
    "seats": [
      {
        "id": 1,
        "seat_number": "A01",
        "has_window": true,
        "has_plug": true,
        "status": "available",
        "available_slots": ["09:00-10:00", "10:00-12:00", "14:00-16:00"]
      }
    ]
  }
}
```

#### GET `/student/seats/search`
**描述**：按条件搜索座位

**查询参数**：
- `date`（必填）：查询日期
- `start_time`（可选）：开始时间，如 `09:00`
- `end_time`（可选）：结束时间，如 `12:00`
- `has_window`（可选）：`true` | `false`
- `has_plug`（可选）：`true` | `false`
- `room_type`（可选）：`public` | `department`
- `page` / `per_page`：分页

**响应示例**：同 `/student/rooms/{room_id}/seats` 中的 `seats` 列表格式，增加 `room_name` 字段。

---

### 2.4 预约管理

#### POST `/student/reservations`
**描述**：提交座位预约

**请求体**：
```json
{
  "seat_id": 1,
  "start_time": "2025-04-14T09:00:00",
  "end_time": "2025-04-14T12:00:00"
}
```

**响应示例**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 101,
    "seat_id": 1,
    "seat_number": "A01",
    "room_name": "理科图书馆 301 自习室",
    "start_time": "2025-04-14T09:00:00",
    "end_time": "2025-04-14T12:00:00",
    "status": "reserved",
    "created_at": "2025-04-13T20:00:00"
  }
}
```

#### GET `/student/reservations`
**描述**：我的预约记录

**查询参数**：
- `status`（可选）：`reserved` | `checked_in` | `completed` | `cancelled` | `violation`
- `page` / `per_page`：分页

#### GET `/student/reservations/{id}`
**描述**：预约详情

#### POST `/student/reservations/{id}/cancel`
**描述**：取消预约

**请求体**（可选）：
```json
{
  "reason": "临时有事"
}
```

---

### 2.5 签到

#### POST `/student/reservations/{id}/check-in`
**描述**：预约签到

**请求体**：
```json
{
  "code": "ABC123"  // 动态签到码
}
```

**响应示例**：
```json
{
  "code": 200,
  "message": "签到成功",
  "data": {
    "check_in_time": "2025-04-14T09:05:00"
  }
}
```

---

### 2.6 通知与违约

#### GET `/student/notifications`
**描述**：通知列表

**查询参数**：
- `is_read`（可选）：`true` | `false`
- `page` / `per_page`：分页

#### PUT `/student/notifications/{id}/read`
**描述**：标记单条通知为已读

#### PUT `/student/notifications/read-all`
**描述**：标记所有通知为已读

#### GET `/student/violations`
**描述**：我的违约记录

**响应示例**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "reservation_id": 55,
        "violation_time": "2025-04-10T09:15:00",
        "reason": "超时未签到",
        "seat_number": "B02",
        "room_name": "理科图书馆 301 自习室"
      }
    ]
  }
}
```

---

## 3. 管理端接口

### 3.1 认证相关

#### POST `/admin/auth/login`
**描述**：管理员登录

**请求体**：
```json
{
  "username": "admin",
  "password": "123456"
}
```

**响应示例**：同学生端登录，但 `user_type` 为 `admin`，并返回 `roles` 列表。

---

### 3.2 仪表盘（可选）

#### GET `/admin/dashboard/stats`
**描述**：管理端首页统计数据

**响应示例**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total_rooms": 10,
    "total_seats": 300,
    "today_reservations": 156,
    "today_violations": 3,
    "active_users": 89
  }
}
```

---

### 3.3 RBAC 权限管理

#### GET `/admin/roles`
**描述**：角色列表（分页）

#### POST `/admin/roles`
**描述**：创建角色

**请求体**：
```json
{
  "name": "room_manager",
  "description": "自习室管理员",
  "permission_ids": [3, 4, 5]
}
```

#### GET `/admin/roles/{id}`
**描述**：角色详情（含权限列表）

#### PUT `/admin/roles/{id}`
**描述**：更新角色

#### DELETE `/admin/roles/{id}`
**描述**：删除角色（如角色下仍有用户，返回 `409` 冲突）

#### GET `/admin/permissions`
**描述**：权限列表（全量，不分页）

---

### 3.4 用户管理（管理员账号）

#### GET `/admin/users`
**描述**：管理员用户列表（分页）

**查询参数**：
- `role_id`（可选）
- `keyword`（可选）：按用户名/姓名模糊搜索

#### POST `/admin/users`
**描述**：创建管理员账号

**请求体**：
```json
{
  "username": "teacher02",
  "password": "123456",
  "name": "王老师",
  "department": "数学学院",
  "email": "teacher02@fdu.edu.cn",
  "role_ids": [2]
}
```

#### GET `/admin/users/{id}`
**描述**：管理员详情

#### PUT `/admin/users/{id}`
**描述**：更新管理员信息及角色分配

#### DELETE `/admin/users/{id}`
**描述**：删除管理员账号

---

### 3.5 自习室管理

#### GET `/admin/rooms`
**描述**：自习室列表（分页）

**查询参数**：
- `room_type`（可选）
- `is_active`（可选）：`true` | `false`
- `keyword`（可选）：按名称/位置搜索

#### POST `/admin/rooms`
**描述**：登记自习室

**请求体**：
```json
{
  "name": "理科图书馆 301 自习室",
  "location": "理科图书馆 3楼",
  "capacity": 60,
  "room_type": "public",
  "department": null,
  "open_time": "07:00:00",
  "close_time": "22:00:00"
}
```

#### GET `/admin/rooms/{id}`
**描述**：自习室详情

#### PUT `/admin/rooms/{id}`
**描述**：更新自习室信息

#### DELETE `/admin/rooms/{id}`
**描述**：注销自习室（`is_active` 设为 `false`，并自动取消未来预约）

---

### 3.6 座位管理

#### GET `/admin/rooms/{room_id}/seats`
**描述**：某自习室的座位列表（分页）

#### POST `/admin/rooms/{room_id}/seats`
**描述**：批量登记座位

**请求体**：
```json
{
  "prefix": "A",
  "start_number": 1,
  "count": 6,
  "has_window": true,
  "has_plug": true
}
```
或逐个指定：
```json
{
  "seats": [
    { "seat_number": "A01", "has_window": true, "has_plug": true },
    { "seat_number": "A02", "has_window": true, "has_plug": false }
  ]
}
```

#### PUT `/admin/seats/{id}`
**描述**：更新座位（状态、标记）

**请求体**：
```json
{
  "status": "maintenance",
  "has_window": true,
  "has_plug": false
}
```

#### DELETE `/admin/seats/{id}`
**描述**：注销座位（`status` 设为 `retired`）

---

### 3.7 预约与违约管理

#### GET `/admin/reservations`
**描述**：全局预约记录查询（分页）

**查询参数**：
- `user_id`（可选）
- `room_id`（可选）
- `seat_id`（可选）
- `status`（可选）
- `start_date` / `end_date`（可选）：按预约日期范围筛选
- `keyword`（可选）：按学生学号/姓名搜索

#### POST `/admin/reservations`
**描述**：代理预约（为学生预约座位）

**请求体**：
```json
{
  "username": "2025123456",
  "seat_id": 1,
  "start_time": "2025-04-14T09:00:00",
  "end_time": "2025-04-14T12:00:00",
  "notify_user": true
}
```

#### POST `/admin/reservations/{id}/cancel`
**描述**：管理员取消预约

**请求体**：
```json
{
  "reason": "教室临时征用",
  "notify_user": true
}
```

#### GET `/admin/violations`
**描述**：违约记录列表（分页）

**查询参数**：
- `user_id`（可选）
- `start_date` / `end_date`（可选）
- `keyword`（可选）：按学号/姓名搜索

#### GET `/admin/violations/export`
**描述**：导出违约记录（CSV/Excel）

---

### 3.8 系统配置

#### GET `/admin/configs`
**描述**：系统参数列表（全量，不分页）

#### PUT `/admin/configs/{key}`
**描述**：更新系统参数

**请求体**：
```json
{
  "config_value": "6",
  "description": "期末考试周调整为6小时"
}
```

---

## 4. AI 助手接口

#### POST `/ai/chat`
**描述**：智能助手交互

**请求体**：
```json
{
  "message": "今天晚上还有空座吗？",
  "session_id": "uuid-string"  // 可选, 用于上下文追踪
}
```

**响应示例**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "reply": "今天晚上理科图书馆 301 自习室还有 12 个空座，推荐 A01（靠窗、有插座）。",
    "action": "search_seats",
    "payload": {
      "date": "2025-04-14",
      "available_count": 12,
      "recommendations": [
        { "seat_id": 1, "seat_number": "A01", "room_name": "理科图书馆 301 自习室", "has_window": true, "has_plug": true }
      ]
    }
  }
}
```

**`action` 类型说明**：
- `text`：纯文本回复
- `search_seats`：查询空座并返回推荐
- `show_reservations`：展示用户当前预约
- `redirect`：引导用户去特定页面操作（如"请前往预约页面"）
- `error`：无法理解用户意图

---

## 5. 接口分工与开发建议

| 接口分组 | 负责小组 | 开发优先级 |
|---------|---------|-----------|
| 学生端认证 + 个人信息 | 学生端小组 | P0 |
| 自习室/座位查询 | 学生端小组 | P0 |
| 预约 + 取消 + 签到 | 学生端小组 | P0 |
| 通知 + 违约查看 | 学生端小组 | P1 |
| 管理端认证 | 管理端小组 | P0 |
| RBAC（角色/权限/用户） | 管理端小组 | P0 |
| 自习室/座位 CRUD | 管理端小组 | P0 |
| 预约/违约管理 | 管理端小组 | P1 |
| 系统配置 | 管理端小组 | P1 |
| AI 聊天接口 | AI 小组 | P0 |
| 仪表盘/统计 | 各组按需 | P2 |

---

## 6. 待确认事项

在正式开发前，建议全组评审并确认以下内容：

1. **JWT 过期时间**：建议 access_token 有效期 24 小时，是否足够？
2. **签到码刷新频率**：文档中默认 24 小时，是否需要支持按小时调整？
3. **批量创建座位 API**：采用 `prefix + count` 模式还是传入数组？
4. **AI 回复 `action` 枚举**：上述 5 种是否覆盖全部场景，AI 小组是否需要扩展？
5. **时间区问题**：是否统一使用服务器本地时间（UTC+8）还是存储 UTC？
6. **文件导出格式**：违约记录导出优先 CSV 还是 Excel？

---

## 7. 附录：接口前缀速查

| 模块 | 前缀 |
|------|------|
| 学生端 | `/api/v1/student` |
| 管理端 | `/api/v1/admin` |
| AI 助手 | `/api/v1/ai` |

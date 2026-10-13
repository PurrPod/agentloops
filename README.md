<h1 align="center">PurrCat AgentLoop Market</h1>

<p align="center">
    专为 <a href="https://github.com/PurrPod/purrcat">PurrCat</a> 构建的 Agent Loop（范式）市场与注册表中心。
</p>

---

## 1. 简介

AgentLoop 是 PurrCat Agent 的「主循环范式」，即一份 PARADIGM YAML：它声明每一轮循环在哪些阶段（`on_build_system_prompt` / `on_loop_start` / `on_loop_epoch` / `on_loop_end` …）注入什么内容、执行什么检查，以及定时触发（`trigger`）与循环结束的最大重试次数（`loop_end_max_retry`）。

所有范式存放于 `~/.purrcat/paradigms/`，一个文件一个 loop；`PARADIGM.yaml` 为默认范式，本仓库收录的范式安装为**备选范式**（不会覆盖默认文件），用户可在会话里切换。

AgentLoop 通常作为 UI 插件 / Graph 的依赖被自动安装：插件在其 `dependency` 中声明 `{"type": "agentloop", "id": "<范式名>"}`，市场下载插件时会一并把该范式安装到 `~/.purrcat/paradigms/<范式名>.yaml`。

---

## 2. 仓库架构设计

```text
agentloops/
├── .github/workflows/   # CI/CD 自动化构建流水线
├── scripts/             # 注册表构建与校验脚本
├── registry.json        # 全局注册表 (由 Action 自动生成)
├── README.md            # 说明文档与范式列表 (由 Action 自动更新)
│
└── agentloops/          # 官方 Agent Loop (源码直接在本仓库维护)
    └── <loop-name>.yaml # 一个范式一个 YAML 文件
```

---

## 3. 已收录 Agent Loop 清单

*(注：本列表由自动化流水线实时生成)*

<!-- AGENTLOOPS:START -->
| 范式名 (Install ID) | 描述 |
| :--- | :--- |
| `default-agentloop` | PurrCat 默认 Agent Loop（范式）：注入规则/信息/灵魂/记忆，并在循环结束时校验 Memo 工具调用。 |
<!-- AGENTLOOPS:END -->

---

## 4. 统一字段规范

每个 `agentloops/<loop-name>.yaml` 的**首部字段**必须包含以下内容（注册表条目由它派生，其余为标准 PARADIGM 字段）：

```yaml
name: "default-agentloop"                 # 必填，必须与文件名一致
description: "…（中文，范式说明）"          # 必填
description-en: "…（英文，市场展示）"       # 必填
dependency: []                            # 必填，依赖声明数组
path: "agent_vm"                          # 标准 PARADIGM 字段
loop_end_max_retry: 3
trigger: []
hooks: {}                                 # 必填，非空对象（各阶段钩子）
```

### 字段解析

* **`name`** (必填): 安装标识，必须与文件名（去掉 `.yaml`）完全一致。
* **`description`** (必填): 中文描述，用于市场中文展示。
* **`description-en`** (必填): 英文描述，注册表 `${description}` 与市场英文展示。
* **`dependency`** (必填): 依赖声明数组，元素形如 `{ "type": "<类型>", "id": "<安装标识>" }`；`type` 白名单为 `skill` / `plugin` / `mcp` / `agentloop` / `sensor` / `graph`。无依赖时为 `[]`。
* **`path` / `loop_end_max_retry` / `trigger` / `hooks`**: 标准 PARADIGM 字段，语义见 PurrCat 主仓 `src/agent/hook_handler.py`。

### 命名一致性要求

**文件名（去掉 `.yaml`）= YAML 内的 `name` 字段**

CI 构建时会自动校验。例如范式 `default-agentloop`：

```
agentloops/default-agentloop.yaml   # ✅ name: "default-agentloop"
```

---

## 5. 收录方式

在 `agentloops/` 目录下新建 `<loop-name>.yaml`，包含上述全部必填字段与合法 `hooks`。

提交 Pull Request。CI 会自动校验：

* 文件名与 YAML 内的 `name` 字段一致；
* `description` / `description-en` 非空；
* `hooks` 为非空对象；
* `dependency` 类型在白名单内。

PR 审核通过并合并后，流水线将自动把所有范式合并为全局注册表 `registry.json`，并重写本文档的范式清单。

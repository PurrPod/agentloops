#!/usr/bin/env python3
"""构建 agentloop 的 registry.json 并同步 README.md

目录约定:
  agentloops/<loop-name>.yaml   一个 Agent Loop（PARADIGM 范式）一个 YAML 文件

统一字段: 注册表条目由各 YAML 的首部字段派生
  name          = 文件名（去掉 .yaml），必须与 YAML 内的 name 字段一致
  description   = YAML 的 description-en（英文，市场用）
  description-zh= YAML 的 description（中文，范式说明）
  enabled       = 固定 true
  files         = ["<name>.yaml"]
  dependency    = YAML 的 dependency 归一化后 [{type,id}]（白名单见 DEP_TYPES）
"""
import json
import os
import sys

import yaml

REGISTRY_FILE = "registry.json"
README_FILE = "README.md"
REPO_URL = "https://github.com/PurrPod/agentloop"

LOOPS_DIR = "agentloops"

# 依赖类型白名单，与极简宿主 webmin.py 的 DEP_TYPES 完全一致
DEP_TYPES = ("skill", "plugin", "mcp", "agentloop", "sensor", "graph")


def fail(msg):
    print(f"[Error] {msg}")
    sys.exit(1)


def load_yaml(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except (OSError, yaml.YAMLError) as e:
        fail(f"无法读取或解析 {filepath}: {e}")


def normalize_dependency(raw, name):
    out = []
    if raw is None:
        return out
    if not isinstance(raw, list):
        fail(f"[{name}.yaml] 'dependency' 必须是数组")
    for item in raw:
        if not isinstance(item, dict):
            fail(f"[{name}.yaml] 'dependency' 元素必须是对象 {{type,id}}")
        dep_type = str(item.get("type") or "").strip()
        dep_id = str(item.get("id") or "").strip()
        if dep_type not in DEP_TYPES:
            fail(
                f"[{name}.yaml] 'dependency.type' ('{dep_type}') 非法，"
                f"仅支持 {', '.join(DEP_TYPES)}"
            )
        if not dep_id:
            fail(f"[{name}.yaml] 'dependency.id' 不能为空")
        out.append({"type": dep_type, "id": dep_id})
    return out


def build_entry(file_name):
    """由 agentloops/<file_name> 派生注册表条目。"""
    name = file_name[: -len(".yaml")]
    path = os.path.join(LOOPS_DIR, file_name)
    data = load_yaml(path)
    if not isinstance(data, dict):
        fail(f"[{LOOPS_DIR}/{file_name}] YAML 顶层必须是对象")

    inner = str(data.get("name") or "").strip()
    if not inner:
        fail(f"[{LOOPS_DIR}/{file_name}] 缺少 'name'")
    if inner != name:
        fail(f"[{LOOPS_DIR}/{file_name}] 'name' ('{inner}') 必须与文件名 ('{name}') 一致")

    if not str(data.get("description", "")).strip():
        fail(f"[{LOOPS_DIR}/{file_name}] 'description' (中文) 不能为空")
    if not str(data.get("description-en", "")).strip():
        fail(f"[{LOOPS_DIR}/{file_name}] 'description-en' (英文) 不能为空")

    if not isinstance(data.get("hooks"), dict) or not data["hooks"]:
        fail(f"[{LOOPS_DIR}/{file_name}] 'hooks' 必须是非空对象")

    return {
        "name": name,
        "description": data["description-en"],
        "description-zh": data["description"],
        "enabled": True,
        "files": [file_name],
        "dependency": normalize_dependency(data.get("dependency"), name),
    }


def scan_loops():
    entries = []
    if not os.path.isdir(LOOPS_DIR):
        return entries
    for item in sorted(os.listdir(LOOPS_DIR)):
        if item.startswith(".") or not item.endswith((".yaml", ".yml")):
            continue
        if not os.path.isfile(os.path.join(LOOPS_DIR, item)):
            continue
        entries.append(build_entry(item))
    return entries


def generate_markdown_table(entries):
    lines = [
        "| 范式名 (Install ID) | 描述 |",
        "| :--- | :--- |",
    ]
    if not entries:
        lines.append("| *(虚位以待)* | 期待您的收录！ |")
        return "\n".join(lines) + "\n"

    for info in entries:
        desc = str(info["description-zh"]).replace("|", "\\|")
        lines.append(f"| `{info['name']}` | {desc} |")
    return "\n".join(lines) + "\n"


def replace_between_tags(text, start_tag, end_tag, new_content):
    start_idx = text.find(start_tag)
    end_idx = text.find(end_tag)
    if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
        head = text[: start_idx + len(start_tag)]
        tail = text[end_idx:]
        return f"{head}\n{new_content}{tail}"
    return text


def update_readme(entries):
    if not os.path.exists(README_FILE):
        return
    with open(README_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    content = replace_between_tags(
        content,
        "<!-- AGENTLOOPS:START -->",
        "<!-- AGENTLOOPS:END -->",
        generate_markdown_table(entries),
    )
    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    print(f"扫描 {LOOPS_DIR}/ 下的 Agent Loop ...")
    entries = scan_loops()

    names = [e["name"] for e in entries]
    duplicates = sorted({n for n in names if names.count(n) > 1})
    if duplicates:
        fail(f"存在同名范式: {', '.join(duplicates)}")

    registry = {
        "version": "1.0",
        "repository": REPO_URL,
        "agentloops": entries,
    }

    print(f"生成 {REGISTRY_FILE} ...")
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print("更新 README.md ...")
    update_readme(entries)

    print(f"构建与校验完成！共 {len(entries)} 个 Agent Loop。")


if __name__ == "__main__":
    main()

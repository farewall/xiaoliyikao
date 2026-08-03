# -*- coding: utf-8 -*-
"""导入语料库 Markdown → KnowledgePoint.description。

用法(backend/ 下):
    .venv/Scripts/python.exe corpus/import.py

格式见 corpus/README.md。幂等:按 (subject, chapter, name) 更新或插入,
已有题目关联的考点只更新 description,不影响 knowledge_point_id。
"""
import re
import sys
from pathlib import Path

# 保证从 corpus/ 子目录运行也能 import app(backend 根目录入 sys.path)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models.knowledge_point import KnowledgePoint

CORPUS_DIR = Path(__file__).resolve().parent
SECTION_ORDER = ["核心讲解", "鉴别要点", "易错点", "记忆口诀"]


def parse_file(path: Path):
    """解析单个语料 md,返回 (subject, [(chapter, name, sections)])"""
    subject = path.stem  # 文件名即科目
    items: list = []
    chapter: str | None = None
    current_name: str | None = None
    current_sections: dict = {}
    current_section: str | None = None
    current_lines: list[str] = []

    def flush_kp():
        nonlocal current_name, current_sections, current_section, current_lines
        if current_name and chapter:
            cleaned = {k: "\n".join(v).strip() for k, v in current_sections.items()}
            cleaned = {k: v for k, v in cleaned.items() if v}
            if cleaned:
                items.append((chapter, current_name, cleaned))
        current_name = None
        current_sections = {}
        current_section = None
        current_lines = []

    def strip_prefix(line: str, prefix: str) -> str:
        return re.sub(rf"^{prefix}\s*[:：]\s*", "", line).strip()

    in_comment = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if in_comment:
            if "-->" in line:
                in_comment = False
            continue
        if "<!--" in line:
            # 跳过 HTML 注释(模板占位说明,不是语料)
            if "-->" not in line:
                in_comment = True
            continue
        if not line.strip():
            continue
        if line.startswith("### "):
            flush_kp()
            current_name = strip_prefix(line[4:].strip(), "考点")
            current_section = None
            current_lines = []
        elif line.startswith("## "):
            flush_kp()  # 用当前(旧的)章节先收尾
            chapter = strip_prefix(line[3:].strip(), "章节")
        elif line.startswith("# "):
            continue  # 文件标题,忽略(科目取文件名)
        elif line.startswith("**") and line.endswith("**"):
            current_section = line.strip("*").strip()
            current_lines = []
        elif current_section:
            # 普通内容行(HTML 注释等无小节时自动忽略)
            current_sections.setdefault(current_section, []).append(line)
    flush_kp()
    return subject, items


def build_description(sections: dict) -> str:
    """小节 → 【核心讲解】…【记忆口诀】… 拼接。"""
    parts = []
    for sec in SECTION_ORDER:
        if sec in sections:
            parts.append(f"【{sec}】\n{sections[sec]}")
    return "\n\n".join(parts)


def main() -> None:
    db = SessionLocal()
    try:
        updated = inserted = 0
        for path in sorted(CORPUS_DIR.glob("*.md")):
            if path.name == "README.md":
                continue
            subject, items = parse_file(path)
            for chapter, name, sections in items:
                desc = build_description(sections)
                if not desc:
                    continue
                kp = (
                    db.query(KnowledgePoint)
                    .filter(
                        KnowledgePoint.subject == subject,
                        KnowledgePoint.chapter == chapter,
                        KnowledgePoint.name == name,
                    )
                    .first()
                )
                if kp:
                    if kp.description != desc:
                        kp.description = desc
                        updated += 1
                else:
                    db.add(
                        KnowledgePoint(
                            subject=subject, chapter=chapter, name=name, description=desc
                        )
                    )
                    inserted += 1
        db.commit()
        print(f"导入完成: 新增 {inserted} 个考点, 更新 {updated} 个考点")
    finally:
        db.close()


if __name__ == "__main__":
    main()

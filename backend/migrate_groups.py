# -*- coding: utf-8 -*-
"""一次性迁移:题组表方案(ADR 0004)。

内容:
1. 建 `question_groups` 表(create_all,顺带补齐 `question_knowledge_points` 等新表)
2. `questions` 加 `group_id` / `position` 两列,`options` 改可空
3. 为现有无题组的独立题各建一个 `single` 空壳题组并回填(group_id + position=1)
4. 删早期方案的 `scenario` / `series` 两列与 `ix_questions_series` 索引

幂等,可重复执行。

用法(backend/ 下):
    .venv/Scripts/python.exe migrate_groups.py
"""
from sqlalchemy import text

from app import models  # noqa: F401  # 注册全部 ORM 模型,create_all 才能建新表
from app.database import Base, engine


def main() -> None:
    # 1) 新表(create_all 对已存在的表是无害的 no-op)
    Base.metadata.create_all(bind=engine)

    with engine.begin() as conn:
        # 2) questions 加列 + options 改可空 + group_id 索引
        conn.execute(text("ALTER TABLE questions ADD COLUMN IF NOT EXISTS group_id INTEGER"))
        conn.execute(text("ALTER TABLE questions ADD COLUMN IF NOT EXISTS position INTEGER"))
        conn.execute(text("ALTER TABLE questions ALTER COLUMN options DROP NOT NULL"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_questions_group_id ON questions (group_id)"))

        # 3) 回填:无题组的独立题 → 各建一个 single 空壳题组
        rows = conn.execute(text("SELECT id FROM questions WHERE group_id IS NULL")).fetchall()
        for (qid,) in rows:
            gid = conn.execute(
                text(
                    "INSERT INTO question_groups (kind, created_at) "
                    "VALUES ('single', now()) RETURNING id"
                )
            ).scalar_one()
            conn.execute(
                text("UPDATE questions SET group_id = :g, position = 1 WHERE id = :q"),
                {"g": gid, "q": qid},
            )

        # 回填后加非空约束,与模型一致
        conn.execute(text("ALTER TABLE questions ALTER COLUMN group_id SET NOT NULL"))
        conn.execute(text("ALTER TABLE questions ALTER COLUMN position SET NOT NULL"))

        # 4) 删早期方案的列与索引(见 ADR 0004)
        conn.execute(text("ALTER TABLE questions DROP COLUMN IF EXISTS scenario"))
        conn.execute(text("ALTER TABLE questions DROP COLUMN IF EXISTS series"))
        conn.execute(text("DROP INDEX IF EXISTS ix_questions_series"))

    print(f"迁移完成:题组表方案就绪(回填独立题 {len(rows)} 道)。")


if __name__ == "__main__":
    main()

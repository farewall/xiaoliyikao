# -*- coding: utf-8 -*-
"""为 questions.explanation 生成解析草稿(基于「题目 + 考点语料」),人工审校后入库。

用法(backend/ 下):
    # 1) 生成草稿:找空解析的题,DeepSeek 起草,写入 review CSV(不碰数据库)
    .venv/Scripts/python.exe generate_explanations.py --draft [--limit 20] [--subject 生理学]
    # 2) 用 Excel/WPS 打开 review CSV(backend/data/解析草稿.csv),编辑「解析草稿」列
    #    —— 保留=采用;清空该格=不采用
    # 3) 审校确认后入库:
    .venv/Scripts/python.exe generate_explanations.py --apply

设计:医学内容必须人工审校,故分两阶段——草稿落盘供审校,确认后才写库。
"""
import argparse
import csv
import sys
from pathlib import Path

from openai import OpenAI

from app.config import settings
from app.database import SessionLocal
from app.models.knowledge_point import KnowledgePoint
from app.models.question import Question

REVIEW_FILE = Path(__file__).resolve().parent / "data" / "解析草稿.csv"

PROMPT_TEMPLATE = """你是一位资深西医综合(306)辅导老师。请为下面这道题写解析。

要求:
1. 先明确正确答案,再解释「正确项为什么对」和「干扰项为什么错」
2. 结合提供的考点资料,讲清背后的医学原理,让考生真正搞懂
3. 控制在 300 字左右,条理清晰,不要客套用语
4. 只依据提供的资料作答,资料不足时明确说明

【题目】
{stem}

【选项】
{options}

【参考答案】{answer}

【考点资料】
{kp_desc}"""


def build_prompt(q: Question, kp_desc: str) -> str:
    options = "\n".join(f"{k}. {v}" for k, v in q.options.items())
    return PROMPT_TEMPLATE.format(
        stem=q.stem,
        options=options,
        answer="、".join(q.answer),
        kp_desc=kp_desc or "(该考点语料暂缺,请基于常识作答,并在解析中标注「考点语料待补充」)",
    )


def get_client() -> OpenAI:
    return OpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)


def draft(db, limit: int, subject: str | None) -> None:
    query = db.query(Question).filter(Question.explanation == "")
    if subject:
        query = (
            query.join(KnowledgePoint, Question.knowledge_point_id == KnowledgePoint.id)
            .filter(KnowledgePoint.subject == subject)
        )
    questions = query.limit(limit).all()
    if not questions:
        print("没有空解析的题目需要生成")
        return

    print(f"将生成 {len(questions)} 道题的解析草稿(约 ¥0.01/题)...")
    client = get_client()
    rows = []
    for q in questions:
        kp = db.get(KnowledgePoint, q.knowledge_point_id) if q.knowledge_point_id else None
        kp_desc = kp.description if kp else ""
        try:
            resp = client.chat.completions.create(
                model=settings.deepseek_model,
                messages=[
                    {"role": "system", "content": "你是一位资深西医综合(306)辅导老师。"},
                    {"role": "user", "content": build_prompt(q, kp_desc)},
                ],
                temperature=0.3,
                max_tokens=800,
            )
            draft_text = (resp.choices[0].message.content or "").strip()
        except Exception as e:  # noqa: BLE001 - 单题失败不阻断
            print(f"[题{q.id}] 生成失败: {e}")
            draft_text = ""
        rows.append({
            "question_id": q.id,
            "题干": q.stem,
            "参考答案": "、".join(q.answer),
            "解析草稿": draft_text,
        })

    REVIEW_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REVIEW_FILE, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["question_id", "题干", "参考答案", "解析草稿"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"草稿已写入: {REVIEW_FILE}")
    print("请用 Excel/WPS 打开,编辑「解析草稿」列;确认后运行 --apply 入库")


def apply(db) -> None:
    if not REVIEW_FILE.exists():
        print("没有草稿文件,先运行 --draft")
        return
    updated = skipped = 0
    with open(REVIEW_FILE, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            try:
                qid = int(row["question_id"])
            except (ValueError, KeyError):
                continue
            draft_text = (row.get("解析草稿") or "").strip()
            if not draft_text:
                skipped += 1
                continue
            q = db.get(Question, qid)
            if q is None:
                skipped += 1
                continue
            q.explanation = draft_text
            updated += 1
    db.commit()
    print(f"已入库 {updated} 条解析, 跳过 {skipped} 条(空或题不存在)")


def main() -> None:
    parser = argparse.ArgumentParser(description="生成并审校题目解析")
    parser.add_argument("--draft", action="store_true", help="生成草稿到 review CSV")
    parser.add_argument("--apply", action="store_true", help="将审校后的草稿写入数据库")
    parser.add_argument("--limit", type=int, default=50, help="--draft 时最多生成多少道")
    parser.add_argument("--subject", default=None, help="--draft 时只处理某学科")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.draft:
            if not settings.deepseek_api_key:
                print("DEEPSEEK_API_KEY 未配置,无法生成")
                sys.exit(1)
            draft(db, args.limit, args.subject)
        elif args.apply:
            apply(db)
        else:
            parser.print_help()
    finally:
        db.close()


if __name__ == "__main__":
    main()

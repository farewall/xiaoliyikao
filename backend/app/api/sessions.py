"""会话 API(练习 / 模拟测试)。

- 模拟测试:start 组卷建会话 → 考试中 progress 同步进度/剩余时间 → submit 交卷判分出报告。
  中断续考 = 查 kind=mock 且 status=in_progress 的会话,重进时由前端询问用户。
- 练习:结束时 practice 落一条 completed 会话,供「练习记录 / 该轮错题回顾」。
- 历史记录:GET /sessions?kind=...。
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.answer_record import AnswerRecord
from app.models.knowledge_point import KnowledgePoint
from app.models.question import Question
from app.models.session import StudySession
from app.models.user import User
from app.schemas.question import QuestionOut
from app.schemas.session import (
    MockProgressRequest,
    MockStartRequest,
    MockStartResponse,
    MockSubmitRequest,
    PracticeCompleteRequest,
    QuestionAnswer,
    SessionListItem,
    SessionOut,
)
from app.services.auth import get_current_user
from app.services.question_bank import pick_questions

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _get_owned_session(db: Session, session_id: int, user_id: int) -> StudySession:
    """取当前用户拥有的会话,不存在则 404。"""
    session = db.get(StudySession, session_id)
    if session is None or session.user_id != user_id:
        raise HTTPException(status_code=404, detail="会话不存在")
    return session


def _grade(user_answer: list[str], correct_answer: list[str]) -> bool:
    """判分:排序后逐一相等(单选/多选/顺序无关)。"""
    return sorted(user_answer) == sorted(correct_answer)


def _subjects_of(db: Session, questions: list[Question]) -> dict[int, str]:
    """题目 id -> 科目。"""
    kp_ids = {q.knowledge_point_id for q in questions if q.knowledge_point_id}
    rows = db.query(KnowledgePoint).filter(KnowledgePoint.id.in_(kp_ids)).all()
    return {kp.id: kp.subject for kp in rows}


def _build_mock_report(
    db: Session,
    session: StudySession,
    answers: list[dict],
) -> dict:
    """判分全部作答,写入 answer_records,计算报告。

    报告:{correct_count, total_count, est_score, is_full_paper, subjects:[{subject, correct, total, accuracy}]}
    """
    question_ids = [a["question_id"] for a in answers]
    questions = db.query(Question).filter(Question.id.in_(question_ids)).all()
    q_by_id = {q.id: q for q in questions}
    subj_of = _subjects_of(db, questions)

    correct = 0
    subject_stats: dict[str, dict] = {}
    records: list[AnswerRecord] = []

    for a in answers:
        q = q_by_id.get(a["question_id"])
        if q is None:
            continue
        user_answer = sorted(a.get("user_answer") or [])
        is_correct = _grade(user_answer, q.answer)
        a["user_answer"] = user_answer
        a["is_correct"] = is_correct
        if is_correct:
            correct += 1

        subject = subj_of.get(q.knowledge_point_id, "未知")
        s = subject_stats.setdefault(subject, {"correct": 0, "total": 0})
        s["total"] += 1
        if is_correct:
            s["correct"] += 1

        records.append(
            AnswerRecord(
                user_id=session.user_id,
                question_id=q.id,
                user_answer=user_answer,
                is_correct=is_correct,
                duration_seconds=a.get("duration_seconds"),
            )
        )

    total = len(records)
    if total:
        db.add_all(records)

    paper_type = (session.config or {}).get("paper_type", 0)
    subjects_list = [
        {
            "subject": name,
            "correct": v["correct"],
            "total": v["total"],
            "accuracy": round(v["correct"] / v["total"], 3) if v["total"] else 0,
        }
        for name, v in subject_stats.items()
    ]
    subjects_list.sort(key=lambda x: x["accuracy"])

    return {
        "correct_count": correct,
        "total_count": total,
        "est_score": round(300 * correct / total) if total else 0,
        "is_full_paper": paper_type == 180,
        "subjects": subjects_list,
    }


@router.post("/mock/start", response_model=MockStartResponse)
def mock_start(
    payload: MockStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MockStartResponse:
    """开始模拟:组卷 + 建 in_progress 会话,返回题目与剩余时间。"""
    questions = pick_questions(
        db,
        subjects=payload.subjects or None,
        count=payload.paper_type,
    )
    if not questions:
        raise HTTPException(status_code=400, detail="当前范围还没有题目,请先录入题库")

    # 限时按实际题数(1题1分钟);题库不足 paper_type 时按现有题数计
    session = StudySession(
        user_id=current_user.id,
        kind="mock",
        status="in_progress",
        config={"subjects": payload.subjects, "paper_type": payload.paper_type},
        question_ids=[q.id for q in questions],
        answers=[],
        current_index=0,
        remaining_seconds=len(questions) * 60,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return MockStartResponse(
        session_id=session.id,
        questions=[QuestionOut.model_validate(q) for q in questions],
        remaining_seconds=session.remaining_seconds or 0,
    )


@router.post("/mock/{session_id}/progress")
def mock_progress(
    session_id: int,
    payload: MockProgressRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """同步考试进度;status='abandoned' 表示放弃本次。"""
    session = _get_owned_session(db, session_id, current_user.id)
    if session.kind != "mock":
        raise HTTPException(status_code=400, detail="会话类型不是模拟测试")

    if payload.status == "abandoned":
        session.status = "abandoned"
        session.finished_at = datetime.now(timezone.utc)
        db.commit()
        return {"ok": True, "status": "abandoned"}

    if session.status != "in_progress":
        # 已完成/已放弃的会话不再接收进度
        return {"ok": True, "status": session.status}

    session.current_index = payload.current_index
    if payload.remaining_seconds is not None:
        session.remaining_seconds = payload.remaining_seconds
    if payload.answers:
        session.answers = [a.model_dump() for a in payload.answers]
    db.commit()
    return {"ok": True, "status": "in_progress"}


@router.post("/mock/{session_id}/submit")
def mock_submit(
    session_id: int,
    payload: MockSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """交卷:判分、落 answer_records、算报告、置 completed。"""
    session = _get_owned_session(db, session_id, current_user.id)
    if session.kind != "mock":
        raise HTTPException(status_code=400, detail="会话类型不是模拟测试")
    if session.status != "in_progress":
        raise HTTPException(status_code=400, detail="该会话已交卷或已放弃")

    # 未作答的题按错误计入(跳过即不得分,估分才反映真实水平)
    answer_map = {a.question_id: a.model_dump() for a in payload.answers}
    full_answers: list[dict] = []
    for qid in session.question_ids:
        if qid in answer_map:
            full_answers.append(answer_map[qid])
        else:
            full_answers.append({"question_id": qid, "user_answer": [], "duration_seconds": None})

    session.answers = full_answers
    if payload.remaining_seconds is not None:
        session.remaining_seconds = payload.remaining_seconds
    session.report = _build_mock_report(db, session, full_answers)
    session.status = "completed"
    session.finished_at = datetime.now(timezone.utc)
    db.commit()

    return {"ok": True, "report": session.report}


@router.post("/practice")
def practice_complete(
    payload: PracticeCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """练习结束:落一条 completed 练习会话,供「练习记录 / 该轮错题回顾」。"""
    question_ids = [a.question_id for a in payload.answers]
    questions = db.query(Question).filter(Question.id.in_(question_ids)).all()
    q_by_id = {q.id: q for q in questions}

    answers: list[dict] = []
    for a in payload.answers:
        q = q_by_id.get(a.question_id)
        if q is None:
            continue
        answers.append(
            {
                "question_id": a.question_id,
                "user_answer": sorted(a.user_answer),
                "duration_seconds": a.duration_seconds,
                "is_correct": _grade(a.user_answer, q.answer),
            }
        )

    session = StudySession(
        user_id=current_user.id,
        kind="practice",
        status="completed",
        config=payload.config,
        question_ids=question_ids,
        answers=answers,
        finished_at=datetime.now(timezone.utc),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"ok": True, "session_id": session.id}


@router.get("", response_model=list[SessionListItem])
def list_sessions(
    kind: str | None = None,
    status: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SessionListItem]:
    """会话历史(按开始时间倒序)。kind 可选 practice / mock。"""
    stmt = select(StudySession).where(StudySession.user_id == current_user.id)
    if kind:
        stmt = stmt.where(StudySession.kind == kind)
    if status:
        stmt = stmt.where(StudySession.status == status)
    stmt = stmt.order_by(StudySession.id.desc()).limit(min(limit, 200))

    items: list[SessionListItem] = []
    for s in db.execute(stmt).scalars().all():
        if s.kind == "mock" and s.report:
            correct = s.report.get("correct_count", 0)
            total = s.report.get("total_count", 0)
        else:
            correct = sum(1 for a in s.answers if a.get("is_correct"))
            total = len(s.answers)
        items.append(
            SessionListItem(
                id=s.id,
                kind=s.kind,
                status=s.status,
                config=s.config,
                started_at=s.started_at,
                finished_at=s.finished_at,
                correct_count=correct,
                total_count=total,
                report=s.report,
            )
        )
    return items


@router.get("/{session_id}", response_model=SessionOut)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SessionOut:
    """会话详情:题目展开 + 作答明细 + 报告(续考 / 回看用)。"""
    session = _get_owned_session(db, session_id, current_user.id)

    questions = (
        db.query(Question).filter(Question.id.in_(session.question_ids)).all()
        if session.question_ids
        else []
    )
    q_by_id = {q.id: q for q in questions}
    ordered = [QuestionOut.model_validate(q_by_id[i]) for i in session.question_ids if i in q_by_id]

    return SessionOut(
        id=session.id,
        kind=session.kind,
        status=session.status,
        config=session.config,
        question_ids=session.question_ids,
        answers=[QuestionAnswer(**a) for a in (session.answers or [])],
        current_index=session.current_index,
        remaining_seconds=session.remaining_seconds,
        report=session.report,
        started_at=session.started_at,
        finished_at=session.finished_at,
        questions=ordered,
    )

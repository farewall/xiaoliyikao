"""RAG 答疑服务(核心差异化能力)。

当前实现(MVP):
- 检索:基于考点标签 + 题目语义关键词,从题库/考点库中取上下文。
  检索结果 = 题目题干 + 解析 + 关联考点讲解,拼成 prompt 给 DeepSeek。
- 生成:调用 DeepSeek(OpenAI 兼容接口),要求模型只基于上下文作答、可溯源。
- 向量检索接口预留:将来 embedding 管线就绪后,替换 _retrieve 的实现即可。

设计原则(见讨论记录 Q3/Q5):
- AI 是讲解员,不是题源;回答必须基于检索到的依据,减少幻觉。
- 解析为 AI 自主重写,不直接引用出版物原文。
"""
import logging

from openai import OpenAI
from sqlalchemy.orm import Session

from app.config import settings
from app.models.knowledge_point import KnowledgePoint
from app.models.question import Question

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "你是一位资深西医综合(306)辅导老师。请基于下面提供的题目、解析和知识点资料,"
    "用通俗易懂的方式回答用户针对这道题的追问。"
    "要求:\n"
    "1. 只依据提供的资料作答,不要编造资料之外的知识点;资料不足以回答时,明确说明。\n"
    "2. 讲清楚背后的医学原理,让用户真正搞懂,而不是背答案。\n"
    "3. 如果用户是追问某道题,先引用题干的对应部分,再展开解释。\n"
    "4. 回答控制在 300 字以内,条理清晰。\n"
)


class RAGService:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)

    # ---- 检索 ----
    def _retrieve(self, db: Session, question_id: int) -> dict[str, str]:
        """检索与该题相关的上下文,返回拼装好的资料文本与引用来源。"""
        question = db.get(Question, question_id)
        if question is None:
            raise KeyError(f"question {question_id} not found")

        kp = db.get(KnowledgePoint, question.knowledge_point_id) if question.knowledge_point_id else None

        # 组装题目 + 解析
        options_text = "\n".join(f"{k}. {v}" for k, v in question.options.items())
        question_block = (
            f"【题目】{question.stem}\n"
            f"【选项】\n{options_text}\n"
            f"【参考答案】{', '.join(question.answer)}\n"
            f"【解析】{question.explanation}"
        )

        # 关联考点讲解(若有)
        kp_block = ""
        if kp and kp.description:
            kp_block = f"\n【考点:{kp.subject}/{kp.chapter}/{kp.name}】\n{kp.description}"

        references: list[str] = []
        if kp:
            references.append(f"考点:{kp.subject}/{kp.chapter}/{kp.name}")
        if question.source:
            references.append(question.source)

        return {
            "context": question_block + kp_block,
            "references": references,
        }

    # ---- 生成 ----
    def ask(self, db: Session, question_id: int, user_question: str) -> tuple[str, list[str]]:
        """针对某题的追问答疑。返回 (回答, 引用来源)。"""
        try:
            retrieved = self._retrieve(db, question_id)
        except KeyError as e:
            raise ValueError(str(e)) from e

        user_prompt = (
            f"{retrieved['context']}\n\n"
            f"用户追问:{user_question}\n\n"
            f"请回答用户的问题。"
        )

        try:
            resp = self.client.chat.completions.create(
                model=settings.deepseek_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=800,
            )
            answer = resp.choices[0].message.content or ""
        except Exception as e:  # noqa: BLE001 - 统一降级,避免把底层错误暴露给用户
            logger.exception("DeepSeek call failed")
            raise RuntimeError("AI 答疑服务暂时不可用,请稍后再试") from e

        return answer.strip(), retrieved["references"]

    # ---- 预留:向量检索(MVP 后启用) ----
    # 需要:1) 安装 pgvector 扩展 2) Question 增加 Vector 字段 3) 填充 embedding 数据
    # 启用后再实现按余弦相似度检索相似题目/知识片段。
    # 当前 MVP 用「考点标签 + 题目上下文」检索(见 _retrieve),不依赖向量。

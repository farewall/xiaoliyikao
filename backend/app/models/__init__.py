"""ORM 模型统一入口:导入即注册到 Base.metadata,供启动时 create_all 建表。"""
from app.models.answer_record import AnswerRecord
from app.models.knowledge_point import KnowledgePoint
from app.models.question import Question
from app.models.question_group import QuestionGroup
from app.models.question_knowledge_point import QuestionKnowledgePoint
from app.models.quota import AIUsage
from app.models.session import StudySession
from app.models.user import User

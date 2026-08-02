"""开发用种子数据:填充考点与题目,便于本地联调「刷题→判分→解析→薄弱点」全流程。

用法(在 backend/ 目录):
    .venv/Scripts/python seed.py

说明:
- 幂等:仅在考点表为空时插入,重复执行不会重复灌数据。
- 解析均为原创编写(不录入出版物原文,见讨论记录 Q5)。
- 题目为联调用示例题,正式题库需另行录入/导入。
"""
from app.database import SessionLocal
from app.models.knowledge_point import KnowledgePoint
from app.models.question import Question

KNOWLEDGE_POINTS = [
    {
        "subject": "生理学",
        "chapter": "呼吸系统",
        "name": "肺通气",
        "description": "肺通气指肺泡与外界环境之间进行气体交换的过程。其原动力是呼吸肌的节律性舒缩引起胸廓容积变化,直接动力是肺内压与大气压之间的压力差。",
    },
    {
        "subject": "生理学",
        "chapter": "循环系统",
        "name": "心脏泵血",
        "description": "心动周期中,心室收缩使室内压升高超过主动脉压时主动脉瓣开启,血液射入动脉。心输出量=心率×每搏输出量,是评价心脏泵血功能的重要指标。",
    },
    {
        "subject": "生物化学",
        "chapter": "糖代谢",
        "name": "糖酵解",
        "description": "糖酵解是葡萄糖在胞质中经一系列酶催化分解为丙酮酸并生成少量ATP的过程。关键酶为己糖激酶、磷酸果糖激酶-1和丙酮酸激酶,整个过程无需氧参与。",
    },
    {
        "subject": "生物化学",
        "chapter": "蛋白质生物合成",
        "name": "翻译",
        "description": "翻译是以mRNA为模板,在核糖体上合成蛋白质的过程。mRNA携带遗传信息,tRNA携带氨基酸并识别密码子,rRNA与蛋白质构成核糖体。",
    },
    {
        "subject": "内科学",
        "chapter": "呼吸系统",
        "name": "肺炎",
        "description": "社区获得性肺炎以肺炎链球菌最常见。典型表现为发热、咳嗽、咳铁锈色痰,胸部影像可见实变影。",
    },
    {
        "subject": "内科学",
        "chapter": "循环系统",
        "name": "心房颤动",
        "description": "心房颤动是最常见的心律失常之一。心电图特征为P波消失代之以f波,R-R间期绝对不规则。治疗核心是控制心室率和抗凝预防血栓。",
    },
]

QUESTIONS = [
    {
        "qtype": "single",
        "stem": "肺通气的直接动力是?",
        "options": {
            "A": "肺内压与大气压之间的压力差",
            "B": "呼吸肌的节律性舒缩",
            "C": "胸廓的弹性回缩力",
            "D": "肺泡表面张力",
        },
        "answer": ["A"],
        "knowledge_point": "肺通气",
        "explanation": "肺通气发生的直接动力是肺内压与大气压之间的压力差。呼吸肌舒缩是原动力,它先引起胸廓容积变化,再改变肺内压,最终形成压力差驱动气体进出。注意区分\"直接动力\"与\"原动力\"。",
        "source": "开发示例题",
    },
    {
        "qtype": "single",
        "stem": "平静呼气末,肺内压与大气压的关系是?",
        "options": {
            "A": "肺内压等于大气压",
            "B": "肺内压大于大气压",
            "C": "肺内压小于大气压",
            "D": "无法确定",
        },
        "answer": ["A"],
        "knowledge_point": "肺通气",
        "explanation": "平静呼气末,呼吸肌舒张,肺内压回落至与大气压相等,气流停止,此时肺容量即功能残气量。任何呼吸时相转换的瞬间,肺内压均等于大气压。",
        "source": "开发示例题",
    },
    {
        "qtype": "single",
        "stem": "心动周期中,主动脉瓣开启的时机是?",
        "options": {
            "A": "等容收缩期",
            "B": "快速射血期",
            "C": "减慢射血期",
            "D": "等容舒张期",
        },
        "answer": ["B"],
        "knowledge_point": "心脏泵血",
        "explanation": "心室开始收缩后,室内压迅速升高超过主动脉压时,主动脉瓣被冲开,血液射入主动脉,即进入快速射血期。等容收缩期室内压仍在升高但未超过动脉压,瓣膜尚未开放。",
        "source": "开发示例题",
    },
    {
        "qtype": "single",
        "stem": "心输出量是指?",
        "options": {
            "A": "一侧心室每次搏动射出的血量",
            "B": "每分钟由一侧心室射入动脉的血量",
            "C": "每搏输出量占心室舒张末期容积的百分比",
            "D": "按体表面积折算的每分钟心输出量",
        },
        "answer": ["B"],
        "knowledge_point": "心脏泵血",
        "explanation": "心输出量(每分心输出量)=每搏输出量×心率,是每分钟一侧心室射入动脉的血量。A为每搏输出量,C为射血分数,D为心指数,注意区分这几个概念。",
        "source": "开发示例题",
    },
    {
        "qtype": "single",
        "stem": "糖酵解的限速酶是?",
        "options": {
            "A": "己糖激酶",
            "B": "磷酸果糖激酶-1",
            "C": "丙酮酸激酶",
            "D": "磷酸甘油酸激酶",
        },
        "answer": ["B"],
        "knowledge_point": "糖酵解",
        "explanation": "磷酸果糖激酶-1催化果糖-6-磷酸→果糖-1,6-二磷酸,是糖酵解最主要的限速酶,受ATP、柠檬酸抑制,受AMP、果糖-2,6-二磷酸激活。己糖激酶和丙酮酸激酶也是关键酶,但调控地位不及PFK-1。",
        "source": "开发示例题",
    },
    {
        "qtype": "single",
        "stem": "1分子葡萄糖经糖酵解净生成的ATP数目是?",
        "options": {
            "A": "1分子",
            "B": "2分子",
            "C": "4分子",
            "D": "38分子",
        },
        "answer": ["B"],
        "knowledge_point": "糖酵解",
        "explanation": "1分子葡萄糖经糖酵解共生成4分子ATP,但底物水平磷酸化消耗2分子ATP用于己糖激酶和磷酸果糖激酶-1,故净生成2分子ATP。38分子是葡萄糖完全氧化(有氧)的总产能。",
        "source": "开发示例题",
    },
    {
        "qtype": "single",
        "stem": "社区获得性肺炎最常见的病原体是?",
        "options": {
            "A": "金黄色葡萄球菌",
            "B": "肺炎链球菌",
            "C": "铜绿假单胞菌",
            "D": "肺炎支原体",
        },
        "answer": ["B"],
        "knowledge_point": "肺炎",
        "explanation": "社区获得性肺炎最常见的病原体是肺炎链球菌。铜绿假单胞菌多见于院内获得性肺炎/免疫低下者,支原体多见于儿童及青年。本题考最常见的病原体,应选肺炎链球菌。",
        "source": "开发示例题",
    },
    {
        "qtype": "single",
        "stem": "肺炎链球菌肺炎的特征性痰液是?",
        "options": {
            "A": "铁锈色痰",
            "B": "粉红色泡沫痰",
            "C": "果酱样痰",
            "D": "大量脓臭痰",
        },
        "answer": ["A"],
        "knowledge_point": "肺炎",
        "explanation": "肺炎链球菌肺炎典型痰液为铁锈色痰(肺泡内红细胞破坏、含铁血黄素沉积)。粉红色泡沫痰见于急性左心衰,脓臭痰提示厌氧菌感染(如肺脓肿)。",
        "source": "开发示例题",
    },
    {
        "qtype": "single",
        "stem": "心房颤动心电图最典型的改变是?",
        "options": {
            "A": "P波消失,代之以大小不等的f波",
            "B": "P波增宽、双峰",
            "C": "ST段弓背向上抬高",
            "D": "QRS波群宽大畸形",
        },
        "answer": ["A"],
        "knowledge_point": "心房颤动",
        "explanation": "房颤心电图特征为P波消失代之以f波(频率350~600次/分),R-R间期绝对不规则。ST段抬高提示心肌梗死,P波增宽见于二尖瓣狭窄等。",
        "source": "开发示例题",
    },
    {
        "qtype": "multiple",
        "stem": "参与蛋白质生物合成的RNA包括哪些?",
        "options": {
            "A": "mRNA",
            "B": "tRNA",
            "C": "rRNA",
            "D": "snRNA",
        },
        "answer": ["A", "B", "C"],
        "knowledge_point": "翻译",
        "explanation": "三种RNA均参与翻译:mRNA是模板、tRNA携带并转运氨基酸、rRNA与蛋白质构成核糖体作为合成场所。snRNA参与mRNA前体剪接,不直接参与翻译,故不选。",
        "source": "开发示例题",
    },
]


def seed() -> None:
    db = SessionLocal()
    try:
        if db.query(KnowledgePoint).count() > 0:
            print("考点表已有数据,跳过种子(如需重灌请先清空 knowledge_points / questions 表)。")
            return

        kp_by_name: dict[str, KnowledgePoint] = {}
        for kp in KNOWLEDGE_POINTS:
            obj = KnowledgePoint(**kp)
            db.add(obj)
            db.flush()
            kp_by_name[kp["name"]] = obj

        for q in QUESTIONS:
            kp_name = q.pop("knowledge_point")
            db.add(Question(**q, knowledge_point_id=kp_by_name[kp_name].id))

        db.commit()
        print(f"已插入考点 {len(KNOWLEDGE_POINTS)} 条、题目 {len(QUESTIONS)} 条。")
    finally:
        db.close()


if __name__ == "__main__":
    seed()

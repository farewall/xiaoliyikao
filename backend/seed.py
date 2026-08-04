"""开发用种子数据:填充考点、题组与题目,便于本地联调「刷题→判分→解析→薄弱点」全流程。

用法(在 backend/ 目录):
    .venv/Scripts/python.exe seed.py

说明:
- 幂等:仅在考点表为空时插入,重复执行不会重复灌数据。
- 解析均为原创编写(不录入出版物原文,见讨论记录 Q5)。
- 题目为联调用示例题,正式题库需另行录入/导入。
- 组织方式:题组(question_groups)为练习/组卷/展示单位,独立题 1:1、A3/A4 病例与
  B 型选项池 1:N;共享内容只存题组一行,组内顺序用 position 显式保证(见 ADR 0004)。
"""
from app.database import SessionLocal
from app.models.knowledge_point import KnowledgePoint
from app.models.question import Question
from app.models.question_group import QuestionGroup
from app.models.question_knowledge_point import QuestionKnowledgePoint

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
    {
        "subject": "内科学",
        "chapter": "循环系统",
        "name": "冠心病",
        "description": "冠心病指冠状动脉粥样硬化致管腔狭窄或闭塞,引起心肌缺血缺氧。急性心肌梗死时心电图出现病理性Q波及ST段弓背向上抬高,尽早再灌注治疗(PCI/溶栓)是关键。",
    },
    {
        "subject": "内科学",
        "chapter": "循环系统",
        "name": "心力衰竭",
        "description": "心力衰竭是心脏结构或功能异常致心室充盈和(或)射血能力受损的一组临床综合征。急性心肌梗死可致泵衰竭,表现为低血压甚至心源性休克。",
    },
]

# ---- 组块示例(题组共享内容)----
# A3/A4 共享病例:存题组的 scenario 列,子题 stem 只存纯问句、各自有 options
AMI_CASE = (
    "男,58岁,突发胸骨后压榨样疼痛2小时,含服硝酸甘油不缓解,伴大汗、恶心。"
    "查体:血压90/60mmHg,心率100次/分,律齐。心电图:V1~V5导联ST段弓背向上抬高。"
)
# B 型共用选项池:存题组的 options 列,子题 options 为空(渲染时取池)、答案取池内单个字母
RESP_POOL = {
    "A": "肺炎(大叶性肺炎)",
    "B": "急性左心衰",
    "C": "冠心病心绞痛",
    "D": "心房颤动",
}

# 题组 + 题目(嵌套结构):kind=single 独立题 1:1;kind=case 共享病例;kind=pool 共用选项池
QUESTION_GROUPS = [
    {
        "kind": "single",
        "questions": [
            {
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
        ],
    },
    {
        "kind": "single",
        "questions": [
            {
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
        ],
    },
    {
        "kind": "single",
        "questions": [
            {
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
        ],
    },
    {
        "kind": "single",
        "questions": [
            {
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
        ],
    },
    {
        "kind": "single",
        "questions": [
            {
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
        ],
    },
    {
        "kind": "single",
        "questions": [
            {
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
        ],
    },
    {
        "kind": "single",
        "questions": [
            {
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
        ],
    },
    {
        "kind": "single",
        "questions": [
            {
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
        ],
    },
    {
        "kind": "single",
        "questions": [
            {
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
        ],
    },
    {
        "kind": "single",
        "questions": [
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
        ],
    },

    # ---- A3/A4 共享病例题组:一个病例 + 三道子题,共享内容存题组 scenario ----
    {
        "kind": "case",
        "scenario": AMI_CASE,
        "questions": [
            {
                "stem": "该患者最可能的诊断是?",
                "options": {
                    "A": "急性心肌梗死",
                    "B": "急性心包炎",
                    "C": "肺栓塞",
                    "D": "主动脉夹层",
                },
                "answer": ["A"],
                "knowledge_point": "冠心病",
                "explanation": "患者突发胸骨后压榨样疼痛、含服硝酸甘油不缓解、伴大汗,心电图V1~V5导联ST段弓背向上抬高,为急性前壁心肌梗死的典型表现。急性心包炎胸痛与体位相关、ST段抬高为弥漫性;肺栓塞以突发呼吸困难伴低氧为主;主动脉夹层多为撕裂样剧痛且放射,均不出现此典型心电图改变。",
                "source": "开发示例题",
            },
            {
                "stem": "心电图V1~V5导联ST段抬高提示心肌梗死的部位是?",
                "options": {
                    "A": "前壁",
                    "B": "下壁",
                    "C": "后壁",
                    "D": "右室",
                },
                "answer": ["A"],
                "knowledge_point": "冠心病",
                "explanation": "V1~V5导联对应左心室前壁,ST段弓背向上抬高提示前壁急性心肌梗死。下壁梗死见于II、III、aVF导联,后壁梗死需加做V7~V9导联,右室梗死累及V3R~V5R。心电图导联定位是判断梗死相关血管的重要依据。",
                "source": "开发示例题",
            },
            {
                "stem": "该患者血压偏低最可能的原因是?",
                "options": {
                    "A": "心肌收缩力下降致泵衰竭",
                    "B": "外周血管阻力降低",
                    "C": "血容量不足",
                    "D": "迷走神经反射",
                },
                "answer": ["A"],
                "knowledge_point": "冠心病",
                "attached_knowledge_points": ["心脏泵血"],
                "explanation": "急性心肌梗死时大面积心肌坏死使左心室射血能力显著下降,可致泵衰竭,表现为血压降低甚至心源性休克,为最可能原因。外周血管阻力降低、血容量不足、迷走神经反射亦可见低血压,但本例核心机制是心肌泵功能受损。",
                "source": "开发示例题",
            },
        ],
    },

    # ---- B 型共用选项池题组:一个池 + 三道子题,池存题组 options、子题 options 为空 ----
    {
        "kind": "pool",
        "options": RESP_POOL,
        "questions": [
            {
                "stem": "咳铁锈色痰,最可能的疾病是?",
                "answer": ["A"],
                "knowledge_point": "肺炎",
                "explanation": "铁锈色痰是肺炎链球菌感染后肺泡内红细胞破坏、含铁血黄素沉积的特征性表现,最可能为大叶性肺炎(肺炎链球菌肺炎)。",
                "source": "开发示例题",
            },
            {
                "stem": "突发气促、咳粉红色泡沫痰,最可能的疾病是?",
                "answer": ["B"],
                "knowledge_point": "心力衰竭",
                "explanation": "粉红色泡沫痰提示肺淤血、肺泡内血浆渗出,是急性左心衰竭肺水肿的典型表现,需紧急利尿扩血管处理。",
                "source": "开发示例题",
            },
            {
                "stem": "活动后胸骨后压榨样疼痛、休息可缓解,最可能的疾病是?",
                "answer": ["C"],
                "knowledge_point": "冠心病",
                "explanation": "活动诱发、休息缓解的胸骨后压榨样疼痛符合稳定型心绞痛的发作规律,提示冠心病心肌缺血。",
                "source": "开发示例题",
            },
        ],
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

        q_attached: list[tuple[Question, list[str]]] = []
        group_count = question_count = 0
        for g in QUESTION_GROUPS:
            group = QuestionGroup(kind=g["kind"], scenario=g.get("scenario"), options=g.get("options"))
            db.add(group)
            db.flush()
            group_count += 1
            for position, q in enumerate(g["questions"], start=1):
                kp_name = q.pop("knowledge_point")
                attached = q.pop("attached_knowledge_points", [])
                q_obj = Question(
                    **q,
                    group_id=group.id,
                    position=position,
                    knowledge_point_id=kp_by_name[kp_name].id,
                )
                db.add(q_obj)
                db.flush()
                q_attached.append((q_obj, attached))
                question_count += 1

        for q_obj, attached in q_attached:
            for name in attached:
                db.add(
                    QuestionKnowledgePoint(
                        question_id=q_obj.id,
                        knowledge_point_id=kp_by_name[name].id,
                    )
                )

        db.commit()
        attached_count = sum(len(a) for _, a in q_attached)
        print(
            f"已插入考点 {len(KNOWLEDGE_POINTS)} 条、题组 {group_count} 个、题目 {question_count} 条、"
            f"附加考点关联 {attached_count} 条。"
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed()

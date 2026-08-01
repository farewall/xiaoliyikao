"""薄弱点分析 API。

聚合用户答题记录,按考点输出薄弱点清单(正确率最低的排最前)。
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import WeakPoint
from app.services.weakness import analyze_weak_points

router = APIRouter(prefix="/weakness", tags=["weakness"])

# 开发期用户占位
DEV_USER_ID = 1


@router.get("", response_model=list[WeakPoint])
def list_weak_points(db: Session = Depends(get_db)) -> list[WeakPoint]:
    """当前用户的薄弱点清单。"""
    return analyze_weak_points(db, DEV_USER_ID)

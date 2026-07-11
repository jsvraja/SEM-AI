from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.report import Report
from app.routers.reports import get_current_user
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/api/admin", tags=["admin"])

def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.email != "jsvking@gmail.com":
        raise HTTPException(status_code=403, detail="Admin only")
    return current_user


@router.post("/stats")
def get_stats(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    users = db.query(User).all()
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    return {
        "total_users": len(users),
        "pro_users": sum(1 for u in users if u.plan == "pro"),
        "agency_users": sum(1 for u in users if u.plan == "agency"),
        "new_this_week": sum(1 for u in users if u.created_at and u.created_at >= week_ago),
    }


@router.post("/users")
def get_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return {
        "users": [
            {
                "id": str(u.id),
                "email": u.email,
                "name": u.full_name,
                "plan": u.plan,
                "reports_used": u.reports_used,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "is_active": u.is_active
            }
            for u in users
        ]
    }


@router.get("/user-activity")
def get_activity(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    reports = db.query(Report).order_by(Report.created_at.desc()).limit(50).all()
    users = {str(u.id): u.email for u in db.query(User).all()}
    return {
        "activity": [
            {
                "id": str(r.id),
                "user_email": users.get(str(r.user_id), "unknown"),
                "url": r.url,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in reports
        ]
    }


@router.put("/users/{user_id}/plan")
def update_user_plan(
    user_id: str,
    body: dict,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.plan = body.get("plan", user.plan)
    db.commit()
    return {"success": True, "plan": user.plan}


@router.post("/users/{user_id}/toggle")
def toggle_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = not user.is_active
    db.commit()
    return {"success": True, "is_active": user.is_active}


@router.get("/users/{user_id}")
def get_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.full_name,
        "plan": user.plan,
        "reports_used": user.reports_used,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }


@router.post("/feature-flags/{key}")
def update_flag(
    key: str,
    body: dict,
    current_user: User = Depends(require_admin)
):
    return {"success": True, "key": key, "value": body.get("value")}

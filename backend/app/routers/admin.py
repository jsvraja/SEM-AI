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


@router.get("/users")
def get_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    users = db.query(User).order_by(User.created_at.desc()).all()
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    
    return {
        "total": len(users),
        "pro": sum(1 for u in users if u.plan == "pro"),
        "agency": sum(1 for u in users if u.plan == "agency"),
        "new_this_week": sum(1 for u in users if u.created_at and u.created_at >= week_ago),
        "users": [
            {
                "id": str(u.id),
                "email": u.email,
                "full_name": u.full_name,
                "plan": u.plan,
                "reports_used": u.reports_used,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "is_active": u.is_active
            }
            for u in users
        ]
    }


@router.get("/activity")
def get_activity(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    reports = db.query(Report).order_by(Report.created_at.desc()).limit(50).all()
    return {
        "recent_reports": [
            {
                "id": str(r.id),
                "user_id": str(r.user_id),
                "url": r.url,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in reports
        ]
    }


@router.get("/flags")
def get_flags(current_user: User = Depends(require_admin)):
    return {
        "flags": {
            "stripe_billing": False,
            "team_workspaces": False,
            "white_label": False,
            "subscription_management": False
        }
    }


@router.post("/flags")
def update_flags(
    flags: dict,
    current_user: User = Depends(require_admin)
):
    return {"success": True, "flags": flags}


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

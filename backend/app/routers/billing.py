from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
import razorpay
import os
import hmac
import hashlib

from app.database import get_db
from app.models.user import User
from app.routers.reports import get_current_user

router = APIRouter(prefix="/api/billing", tags=["billing"])

RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")

PLANS = {
    "pro": {"amount": 99900, "name": "SEM AI Pro", "reports": 50},
    "agency": {"amount": 299900, "name": "SEM AI Agency", "reports": 999999}
}


class CreateOrderRequest(BaseModel):
    plan: str


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    plan: str


@router.post("/create-order")
def create_order(
    req: CreateOrderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if req.plan not in PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan")

    plan = PLANS[req.plan]
    client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

    order = client.order.create({
        "amount": plan["amount"],
        "currency": "INR",
        "receipt": f"receipt_{current_user.id}_{req.plan}",
        "notes": {
            "user_id": str(current_user.id),
            "plan": req.plan,
            "email": current_user.email
        }
    })

    return {
        "order_id": order["id"],
        "amount": plan["amount"],
        "currency": "INR",
        "plan": req.plan,
        "key_id": RAZORPAY_KEY_ID
    }


@router.post("/verify-payment")
def verify_payment(
    req: VerifyPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Signature verify
    body = f"{req.razorpay_order_id}|{req.razorpay_payment_id}"
    expected = hmac.new(
        RAZORPAY_KEY_SECRET.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()

    if expected != req.razorpay_signature:
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    if req.plan not in PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan")

    # Update user plan
    current_user.plan = req.plan
    current_user.reports_used = 0
    db.commit()

    return {
        "success": True,
        "plan": req.plan,
        "message": f"Successfully upgraded to {req.plan} plan!"
    }


@router.get("/plans")
def get_plans():
    return {
        "plans": [
            {
                "id": "free",
                "name": "Free",
                "price_inr": 0,
                "reports_per_month": 3,
                "features": ["3 reports/month", "SEO Analysis", "Ad Copy", "Basic support"]
            },
            {
                "id": "pro",
                "name": "Pro",
                "price_inr": 999,
                "reports_per_month": 50,
                "features": ["50 reports/month", "All Free features", "PageSpeed Analysis", "Priority support"]
            },
            {
                "id": "agency",
                "name": "Agency",
                "price_inr": 2999,
                "reports_per_month": -1,
                "features": ["Unlimited reports", "All Pro features", "White-label reports", "Dedicated support"]
            }
        ]
    }

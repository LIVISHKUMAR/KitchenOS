"""Customer feedback system."""

import uuid
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Integer, Text, DateTime, JSON
from sqlalchemy import func
from app.infrastructure.database import Base
from app.models import generate_uuid


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False, index=True)
    branch_id = Column(String(36), index=True)
    order_id = Column(String(36), index=True)
    customer_id = Column(String(36), index=True)
    customer_name = Column(String(100))
    rating = Column(Integer, nullable=False)  # 1-5
    food_rating = Column(Integer)
    service_rating = Column(Integer)
    ambiance_rating = Column(Integer)
    comment = Column(Text)
    tags = Column(JSON, default=[])  # ["food_quality", "service", "wait_time", ...]
    sentiment = Column(String(20))  # positive, neutral, negative
    response = Column(Text)
    responded_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class FeedbackService:
    def __init__(self, db: Session):
        self.db = db

    def submit_feedback(self, tenant_id: str, data: dict) -> Feedback:
        # Simple sentiment analysis
        rating = data.get("rating", 3)
        if rating >= 4:
            sentiment = "positive"
        elif rating == 3:
            sentiment = "neutral"
        else:
            sentiment = "negative"

        feedback = Feedback(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            sentiment=sentiment,
            **data
        )
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        return feedback

    def get_feedbacks(self, tenant_id: str, branch_id: Optional[str] = None,
                      sentiment: Optional[str] = None, skip: int = 0, limit: int = 50) -> List[Feedback]:
        query = self.db.query(Feedback).filter(Feedback.tenant_id == tenant_id)
        if branch_id:
            query = query.filter(Feedback.branch_id == branch_id)
        if sentiment:
            query = query.filter(Feedback.sentiment == sentiment)
        return query.order_by(Feedback.created_at.desc()).offset(skip).limit(limit).all()

    def respond_to_feedback(self, feedback_id: str, response: str) -> Optional[Feedback]:
        feedback = self.db.query(Feedback).filter(Feedback.id == feedback_id).first()
        if feedback:
            feedback.response = response
            feedback.responded_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(feedback)
        return feedback

    def get_analytics(self, tenant_id: str, branch_id: Optional[str] = None) -> dict:
        query = self.db.query(Feedback).filter(Feedback.tenant_id == tenant_id)
        if branch_id:
            query = query.filter(Feedback.branch_id == branch_id)

        feedbacks = query.all()

        if not feedbacks:
            return {"total": 0, "avg_rating": 0, "sentiment_breakdown": {}}

        total = len(feedbacks)
        avg_rating = sum(f.rating for f in feedbacks) / total
        avg_food = sum(f.food_rating or f.rating for f in feedbacks) / total
        avg_service = sum(f.service_rating or f.rating for f in feedbacks) / total

        sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
        for f in feedbacks:
            if f.sentiment in sentiment_counts:
                sentiment_counts[f.sentiment] += 1

        return {
            "total_feedbacks": total,
            "avg_rating": round(avg_rating, 1),
            "avg_food_rating": round(avg_food, 1),
            "avg_service_rating": round(avg_service, 1),
            "sentiment_breakdown": sentiment_counts,
            "positive_percentage": round((sentiment_counts["positive"] / total) * 100, 1)
        }

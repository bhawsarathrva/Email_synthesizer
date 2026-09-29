import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import or_, and_, func, desc
from sqlalchemy.orm import Session
from backend.app.database.models import Email

logger = logging.getLogger("email_agent.repository")


class EmailRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_email_by_id(self, email_id: int) -> Optional[Email]:
        """Fetch a single email by its primary key ID."""
        return self.db.query(Email).filter(Email.id == email_id).first()

    def get_emails(
        self,
        page: int = 1,
        limit: int = 20,
        category: Optional[str] = None,
        status: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> Tuple[List[Email], int]:
        """Fetch paginated emails with optional filters for category and verification status."""
        query = self.db.query(Email)

        if category:
            # Match against verified_category or ai_category or legacy Category
            query = query.filter(
                or_(
                    Email.verified_category == category,
                    and_(Email.verified_category.is_(None), Email.ai_category == category),
                    and_(Email.verified_category.is_(None), Email.ai_category.is_(None), Email.Category_legacy == category)
                )
            )

        if status:
            if status.lower() == "pending":
                query = query.filter(
                    or_(
                        Email.verification_status == "pending",
                        Email.verification_status.is_(None)
                    )
                )
            else:
                query = query.filter(Email.verification_status == status)

        if search_query:
            pattern = f"%{search_query}%"
            query = query.filter(
                or_(
                    Email.Subject_text.ilike(pattern),
                    Email.Body_text.ilike(pattern),
                    Email.From_email.ilike(pattern)
                )
            )

        total = query.count()
        offset = (page - 1) * limit
        emails = query.order_by(Email.id.asc()).offset(offset).limit(limit).all()
        return emails, total

    def search_emails(self, query_str: str, limit: int = 5) -> List[Email]:
        """Search emails using subject, body, or sender."""
        pattern = f"%{query_str}%"
        return (
            self.db.query(Email)
            .filter(
                or_(
                    Email.Subject_text.ilike(pattern),
                    Email.Body_text.ilike(pattern),
                    Email.From_email.ilike(pattern),
                )
            )
            .limit(limit)
            .all()
        )

    def find_similar_emails(self, email_id: int, limit: int = 3) -> List[Email]:
        """
        Find previously verified emails that share keywords with the target email.
        Provides few-shot context to the agent classifier.
        """
        target = self.get_email_by_id(email_id)
        if not target:
            return []

        # Find verified emails
        verified_query = self.db.query(Email).filter(
            Email.id != email_id,
            Email.verification_status.in_(["approved", "corrected"]),
            Email.verified_category.isnot(None),
        )

        verified_emails = verified_query.all()
        if not verified_emails:
            # Fall back to any verified or legacy categorized emails
            verified_emails = (
                self.db.query(Email)
                .filter(Email.id != email_id, Email.verified_category.isnot(None))
                .limit(limit)
                .all()
            )
            if not verified_emails:
                return []

        # Simple keyword overlap scoring between target subject+body and candidate subject+body
        target_words = set(f"{target.subject} {target.body}".lower().split())
        scored: List[Tuple[int, Email]] = []
        for cand in verified_emails:
            cand_words = set(f"{cand.subject} {cand.body}".lower().split())
            overlap = len(target_words.intersection(cand_words))
            scored.append((overlap, cand))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:limit]]

    def update_ai_classification(
        self,
        email_id: int,
        category: str,
        confidence: float,
        reasoning: str,
    ) -> Optional[Email]:
        """
        Persist AI's prediction, confidence, and reasoning.
        Never overwrites verified data.
        """
        email = self.get_email_by_id(email_id)
        if not email:
            return None

        email.ai_category = category
        email.ai_confidence = float(confidence)
        email.classification_reason = reasoning
        self.db.commit()
        self.db.refresh(email)
        return email

    def record_human_verification(
        self,
        email_id: int,
        decision: str,  # "YES" or "NO"
        correct_category: Optional[str] = None,
        feedback: Optional[str] = None,
        verified_by: str = "human_reviewer",
    ) -> Optional[Email]:
        """
        Records the human's verification decision.
        If YES: verified_category = ai_category, status = approved
        If NO: verified_category = correct_category, status = corrected, human_feedback = feedback
        Original AI prediction, confidence, and reason are strictly preserved.
        """
        email = self.get_email_by_id(email_id)
        if not email:
            return None

        now = datetime.now(timezone.utc)
        email.verified_at = now
        email.verified_by = verified_by

        if decision.upper() == "YES":
            email.verified_category = email.ai_category
            email.verification_status = "approved"
            email.human_feedback = feedback or "Approved by reviewer"
        else:
            email.verified_category = correct_category
            email.verification_status = "corrected"
            email.human_feedback = feedback or "Corrected by reviewer"

        # Also update legacy columns for full backwards compatibility
        email.Category_legacy = email.verified_category
        email.Verified_legacy = email.verification_status

        self.db.commit()
        self.db.refresh(email)
        return email

    def get_email_statistics(self) -> Dict[str, Any]:
        """
        Returns:
        - Total Emails
        - Payroll Emails
        - Benefits Emails
        - Tax Emails
        - Pending Verification
        - Approved
        - Corrected
        """
        total = self.db.query(func.count(Email.id)).scalar() or 0

        # Effective category counts (based on verified_category, or ai_category if pending)
        payroll_count = self.db.query(func.count(Email.id)).filter(
            or_(
                Email.verified_category == "Payroll",
                and_(Email.verified_category.is_(None), Email.ai_category == "Payroll"),
            )
        ).scalar() or 0

        benefits_count = self.db.query(func.count(Email.id)).filter(
            or_(
                Email.verified_category == "Benefits",
                and_(Email.verified_category.is_(None), Email.ai_category == "Benefits"),
            )
        ).scalar() or 0

        tax_count = self.db.query(func.count(Email.id)).filter(
            or_(
                Email.verified_category == "Tax",
                and_(Email.verified_category.is_(None), Email.ai_category == "Tax"),
            )
        ).scalar() or 0

        pending_count = self.db.query(func.count(Email.id)).filter(
            or_(
                Email.verification_status == "pending",
                Email.verification_status.is_(None)
            )
        ).scalar() or 0

        approved_count = self.db.query(func.count(Email.id)).filter(
            Email.verification_status == "approved"
        ).scalar() or 0

        corrected_count = self.db.query(func.count(Email.id)).filter(
            Email.verification_status == "corrected"
        ).scalar() or 0

        return {
            "total_emails": total,
            "payroll_emails": payroll_count,
            "benefits_emails": benefits_count,
            "tax_emails": tax_count,
            "pending_verification": pending_count,
            "approved": approved_count,
            "corrected": corrected_count,
        }

    def get_evaluation_metrics(self) -> Dict[str, Any]:
        """
        Calculates Accuracy, Precision, Recall, and F1 Score for Payroll, Benefits, Tax
        by comparing AI Prediction vs Human Verified Category on emails that have been verified.
        """
        verified_emails = self.db.query(Email).filter(
            Email.verification_status.in_(["approved", "corrected"]),
            Email.ai_category.isnot(None),
            Email.verified_category.isnot(None),
        ).all()

        if not verified_emails:
            return {
                "verified_count": 0,
                "accuracy": 0.0,
                "payroll": {"precision": 0.0, "recall": 0.0, "f1": 0.0, "support": 0},
                "benefits": {"precision": 0.0, "recall": 0.0, "f1": 0.0, "support": 0},
                "tax": {"precision": 0.0, "recall": 0.0, "f1": 0.0, "support": 0},
            }

        total_verified = len(verified_emails)
        correct_predictions = sum(
            1 for e in verified_emails if e.ai_category == e.verified_category
        )
        accuracy = round(correct_predictions / total_verified, 4)

        categories = ["Payroll", "Benefits", "Tax"]
        metrics: Dict[str, Any] = {
            "verified_count": total_verified,
            "accuracy": accuracy,
        }

        for cat in categories:
            # True Positives: AI predicted cat AND Human verified cat
            tp = sum(1 for e in verified_emails if e.ai_category == cat and e.verified_category == cat)
            # False Positives: AI predicted cat BUT Human verified something else
            fp = sum(1 for e in verified_emails if e.ai_category == cat and e.verified_category != cat)
            # False Negatives: AI predicted something else BUT Human verified cat
            fn = sum(1 for e in verified_emails if e.ai_category != cat and e.verified_category == cat)
            # Support: Total actual human-verified emails for this category
            support = sum(1 for e in verified_emails if e.verified_category == cat)

            precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
            recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
            f1 = round(2 * precision * recall / (precision + recall), 4) if (precision + recall) > 0 else 0.0

            metrics[cat.lower()] = {
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "support": support,
            }

        return metrics

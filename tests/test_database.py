from backend.app.database.connection import SessionLocal, test_connection as db_test_conn
from backend.app.database.repository import EmailRepository


def test_neon_connection():
    result = db_test_conn()
    assert result["status"] == "connected"
    assert "OrangeData" in result["database"]


def test_repository_get_emails():
    db = SessionLocal()
    try:
        repo = EmailRepository(db)
        emails, total = repo.get_emails(page=1, limit=5)
        assert total > 0
        assert len(emails) <= 5
        assert hasattr(emails[0], "subject")
        assert hasattr(emails[0], "body")
    finally:
        db.close()


def test_repository_get_email_by_id():
    db = SessionLocal()
    try:
        repo = EmailRepository(db)
        email = repo.get_email_by_id(1)
        assert email is not None
        assert email.id == 1
    finally:
        db.close()


def test_repository_statistics():
    db = SessionLocal()
    try:
        repo = EmailRepository(db)
        stats = repo.get_email_statistics()
        assert "total_emails" in stats
        assert "pending_verification" in stats
        assert "approved" in stats
        assert "corrected" in stats
        assert stats["total_emails"] >= 30
    finally:
        db.close()

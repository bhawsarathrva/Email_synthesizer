import pytest
from backend.app.agent.classifier import classify_email_content
from backend.app.schemas.classification import ClassificationResult


def test_classify_payroll():
    result = classify_email_content(
        subject="Monthly Salary Credited",
        body="Your salary for September has been deposited into your checking account.",
        sender="payroll@company.com"
    )
    assert isinstance(result, ClassificationResult)
    assert result.category == "Payroll"
    assert 0.0 <= result.confidence <= 1.0
    assert len(result.reasoning) > 0


def test_classify_benefits():
    result = classify_email_content(
        subject="Health and Dental Insurance Open Enrollment",
        body="Please review your 2026 employee benefits and health insurance election options.",
        sender="benefits@company.com"
    )
    assert isinstance(result, ClassificationResult)
    assert result.category == "Benefits"
    assert 0.0 <= result.confidence <= 1.0


def test_classify_tax():
    result = classify_email_content(
        subject="Your Form W-2 and Tax Withholding",
        body="Please find your annual W-2 tax statement and review your state income tax withholding.",
        sender="tax@company.com"
    )
    assert isinstance(result, ClassificationResult)
    assert result.category == "Tax"
    assert 0.0 <= result.confidence <= 1.0


def test_allowed_categories_only():
    allowed = {"Payroll", "Benefits", "Tax"}
    result = classify_email_content(
        subject="Generic Inquiry",
        body="Can you please check the details of my reimbursement and paycheck?",
        sender="worker@company.com"
    )
    assert result.category in allowed

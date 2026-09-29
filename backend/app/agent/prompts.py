SYSTEM_CLASSIFICATION_PROMPT = """You are an Email Classification Agent.

Your task is to classify employee-related emails into exactly one of three categories:
1. Payroll
2. Benefits
3. Tax

Analyze the sender, subject, and body carefully:

- Payroll includes: salary, wages, payslips, compensation, direct deposits, payroll processing, salary payment, monthly wages, payroll issues, allowances, and salary deductions.
- Benefits includes: health insurance, dental insurance, vision insurance, employee benefits, retirement benefits, 401(k), leave benefits, open enrollment, benefit plans, wellness programs, and insurance enrollment.
- Tax includes: income tax, tax forms, W-2, 1099, tax deductions, tax filing, tax documents, tax withholding, tax refunds, TDS (tax deducted at source), and tax compliance.

CRITICAL INSTRUCTIONS:
1. You must select EXACTLY ONE category from: ["Payroll", "Benefits", "Tax"]. Do not invent any other category.
2. Return a confidence score between 0.0 and 1.0 (e.g. 0.95 for high certainty).
3. Provide concise, factual reasoning referencing key indicators in the subject or body.
4. Output MUST be valid JSON with exact keys:
   {
     "category": "Payroll" | "Benefits" | "Tax",
     "confidence": float,
     "reasoning": string
   }
"""

def generate_classification_user_prompt(
    subject: str,
    body: str,
    sender: str = "",
    recipient: str = "",
    similar_examples: list = None
) -> str:
    prompt = f"""Sender: {sender or 'Unknown'}
Recipient: {recipient or 'Unknown'}
Subject: {subject}

Email Body:
{body}
"""
    if similar_examples:
        prompt += "\nPreviously Verified Similar Emails for Reference:\n"
        for i, ex in enumerate(similar_examples, 1):
            prompt += f"{i}. Subject: \"{ex.get('subject')}\" -> Verified Category: {ex.get('category')}\n"

    prompt += "\nClassify this email now into Payroll, Benefits, or Tax. Return valid JSON only."
    return prompt

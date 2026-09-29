import logging
from sqlalchemy import text
from backend.app.database.connection import engine, SessionLocal
from backend.app.database.models import Email

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")

SAMPLE_EMAILS = [
    # 10 Payroll Emails
    {
        "to": "employee1@company.com",
        "from": "payroll@company.com",
        "subject": "Monthly Salary Update - September",
        "body": "Your monthly payroll has been processed successfully. Your basic salary, allowances, deductions, and net salary are detailed in this month's payroll statement."
    },
    {
        "to": "employee2@company.com",
        "from": "finance@company.com",
        "subject": "September Payslip Available for Download",
        "body": "Your official payslip for September is now ready on the employee portal. Please verify your overtime pay and net compensation."
    },
    {
        "to": "employee3@company.com",
        "from": "hr-payroll@company.com",
        "subject": "Direct Deposit Verification for Upcoming Paycheck",
        "body": "We have updated your bank account details for direct deposit. Your upcoming bi-weekly paycheck will be deposited to this account."
    },
    {
        "to": "employee4@company.com",
        "from": "compensation@company.com",
        "subject": "Annual Compensation and Wage Adjustment Notice",
        "body": "Following your performance appraisal, your base salary and hourly wages have been revised effective from the next pay cycle."
    },
    {
        "to": "employee5@company.com",
        "from": "payroll-ops@company.com",
        "subject": "Resolution: Salary Deduction Query",
        "body": "We have investigated your query regarding the voluntary salary deductions on your recent payslip. The excess deduction has been adjusted."
    },
    {
        "to": "employee6@company.com",
        "from": "finance-disburse@company.com",
        "subject": "Bonus and Incentive Payout Schedule",
        "body": "Your quarterly performance incentive has been approved and will be disbursed alongside your regular monthly salary in this pay period."
    },
    {
        "to": "employee7@company.com",
        "from": "payroll@company.com",
        "subject": "Important Notice: Year-End Payroll Processing Deadlines",
        "body": "Please submit all pending timesheets and expense reimbursements by Friday to ensure inclusion in the upcoming payroll processing cycle."
    },
    {
        "to": "employee8@company.com",
        "from": "hr@company.com",
        "subject": "Confirmation of Final Settlement and Severance Pay",
        "body": "Your full and final settlement statement, including accrued leave encashment and severance wages, has been finalized by the payroll team."
    },
    {
        "to": "employee9@company.com",
        "from": "payroll-support@company.com",
        "subject": "Notification of Direct Deposit Delay",
        "body": "Due to a banking holiday, monthly salary deposits may reflect in your account 24 hours later than usual. We apologize for the inconvenience."
    },
    {
        "to": "employee10@company.com",
        "from": "compensation@company.com",
        "subject": "Overtime Compensation Disbursement",
        "body": "Your approved overtime hours for the past month have been calculated and will be added to your upcoming paycheck."
    },

    # 10 Benefits Emails
    {
        "to": "employee1@company.com",
        "from": "benefits@company.com",
        "subject": "Health Insurance Open Enrollment Begins Next Week",
        "body": "The annual open enrollment window for employee health benefits will open on Monday. Review medical, dental, and vision insurance plan options."
    },
    {
        "to": "employee2@company.com",
        "from": "hr-benefits@company.com",
        "subject": "401(k) Retirement Plan Matching Contribution Update",
        "body": "The company has updated its 401(k) matching policy. You can increase your retirement contribution percentage directly on the benefits portal."
    },
    {
        "to": "employee3@company.com",
        "from": "wellness@company.com",
        "subject": "Enrollment in Employee Wellness and Fitness Program",
        "body": "You are eligible to participate in the corporate wellness benefit program offering subsidized gym memberships and annual preventive health checkups."
    },
    {
        "to": "employee4@company.com",
        "from": "benefits@company.com",
        "subject": "Confirmation of Dental and Vision Insurance Election",
        "body": "Your enrollment selection for comprehensive dental and vision family coverage has been processed and your membership cards will be mailed shortly."
    },
    {
        "to": "employee5@company.com",
        "from": "hr@company.com",
        "subject": "Parental Leave Policy and Paid Family Benefits",
        "body": "Please read our updated parental leave benefits guide detailing paid time off, maternal health support, and child care assistance benefits."
    },
    {
        "to": "employee6@company.com",
        "from": "benefits-provider@company.com",
        "subject": "Flexible Spending Account (FSA) Balance Reminder",
        "body": "Remember to submit eligible healthcare and dependent care receipts to utilize your remaining Flexible Spending Account benefit balance."
    },
    {
        "to": "employee7@company.com",
        "from": "insurance@company.com",
        "subject": "Group Life and Disability Coverage Summary",
        "body": "Attached is your annual certificate of coverage for employer-sponsored group term life insurance and short-term disability benefits."
    },
    {
        "to": "employee8@company.com",
        "from": "benefits@company.com",
        "subject": "Employee Assistance Program (EAP) Mental Health Resources",
        "body": "Our employee assistance benefit provides confidential counseling, legal consultations, and work-life wellness support at no cost to you."
    },
    {
        "to": "employee9@company.com",
        "from": "hr-leaves@company.com",
        "subject": "Annual Vacation and Paid Leave Balance Notification",
        "body": "Here is the summary of your accrued paid time off (PTO) and sick leave benefits. Check the rollover rules before the year ends."
    },
    {
        "to": "employee10@company.com",
        "from": "benefits@company.com",
        "subject": "Health Savings Account (HSA) Employer Contribution",
        "body": "The company's quarterly seed contribution to your Health Savings Account has been credited to help cover qualified medical expenses."
    },

    # 10 Tax Emails
    {
        "to": "employee1@company.com",
        "from": "tax-compliance@company.com",
        "subject": "Important: Your Form W-2 Wage and Tax Statement is Ready",
        "body": "Your annual Form W-2 Wage and Tax Statement is now available online. Use this tax document for filing your federal and state income tax returns."
    },
    {
        "to": "employee2@company.com",
        "from": "finance-tax@company.com",
        "subject": "TDS Deduction and Tax Computation Sheet",
        "body": "The tax deducted at source (TDS) for the current financial quarter has been calculated. Review your taxable income and tax exemptions."
    },
    {
        "to": "employee3@company.com",
        "from": "payroll-tax@company.com",
        "subject": "Update Your Form W-4 Tax Withholding Allowances",
        "body": "If you experienced life events such as marriage or child birth, please update your Form W-4 to ensure proper federal tax withholding from your salary."
    },
    {
        "to": "employee4@company.com",
        "from": "tax@company.com",
        "subject": "Form 1099-MISC Available for Independent Services",
        "body": "Your Form 1099-MISC tax document for consulting stipends is available for download on the corporate finance document portal."
    },
    {
        "to": "employee5@company.com",
        "from": "hr-compliance@company.com",
        "subject": "Annual Tax Exemption Declarations and Investment Proofs",
        "body": "Please upload receipts and investment certificates for Section 80C or local tax deduction allowances to minimize excess tax withholding."
    },
    {
        "to": "employee6@company.com",
        "from": "tax-advisory@company.com",
        "subject": "FICA and Medicare Tax Withholding Threshold Notice",
        "body": "This notification explains the Social Security wage base limit and additional Medicare tax withholding applicable to high earners this calendar year."
    },
    {
        "to": "employee7@company.com",
        "from": "finance@company.com",
        "subject": "Corrected W-2 (Form W-2c) Issued for Previous Tax Year",
        "body": "An amended Form W-2c has been generated to correct state tax reporting from the prior calendar year. Please file this with your amended return."
    },
    {
        "to": "employee8@company.com",
        "from": "tax-support@company.com",
        "subject": "State Income Tax Nexus Update for Remote Employees",
        "body": "Since your work location has changed, your state income tax withholding jurisdiction has been updated to reflect your resident state tax regulations."
    },
    {
        "to": "employee9@company.com",
        "from": "tax@company.com",
        "subject": "Year-End Capital Gains and Stock Option Tax Statement",
        "body": "Your equity incentive tax documentation detailing taxable gains and disqualifying dispositions is available for your tax advisor."
    },
    {
        "to": "employee10@company.com",
        "from": "payroll-tax@company.com",
        "subject": "Notice: Quarterly Tax Reconciliation and Refund Adjustment",
        "body": "Our quarterly reconciliation identified an over-withholding of local tax. The adjusted tax refund credit has been applied to your ledger."
    },
]


def seed_database(reset: bool = False):
    """Seeds the Neon database with 30 realistic emails initialized to pending status."""
    db = SessionLocal()
    try:
        if reset:
            logger.info("Resetting existing email data...")
            with engine.connect() as conn:
                with conn.begin():
                    conn.execute(text('TRUNCATE TABLE "Email_data" RESTART IDENTITY;'))

        existing_count = db.query(Email).count()
        if existing_count >= 30 and not reset:
            logger.info(f"Database already contains {existing_count} emails. Ensuring pending status.")
            return

        logger.info(f"Seeding {len(SAMPLE_EMAILS)} sample emails into NeonDB...")
        for item in SAMPLE_EMAILS:
            email = Email(
                To_email=item["to"],
                From_email=item["from"],
                Subject_text=item["subject"],
                Body_text=item["body"],
                verification_status="pending",
                ai_category=None,
                ai_confidence=None,
                verified_category=None,
                human_feedback=None,
            )
            db.add(email)
        db.commit()
        logger.info("Seeding completed successfully!")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

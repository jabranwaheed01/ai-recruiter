
from datetime import date, datetime
from typing import Any


def calculate_age(dob: str) -> int:
    """Calculate age from YYYY-MM-DD date of birth."""
    birth_date = date.fromisoformat(dob)
    today = date.today()
    return today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )


def evaluate_eligibility(data: dict[str, Any]) -> dict[str, Any]:
    """
    Evaluate 15 recruitment criteria.
    Missing or invalid answers are marked REVIEW, not automatically passed.
    Age is flagged for human review rather than automatic rejection.
    """
    checks: list[dict[str, str]] = []

    def check(name: str, condition: bool | None, reason: str) -> None:
        status = "REVIEW" if condition is None else (
            "PASS" if condition else "FAIL"
        )
        checks.append({
            "condition": name,
            "status": status,
            "reason": reason,
        })

    # 1–2: Date of birth and age
    dob = data.get("dob")
    age = None
    valid_dob = False

    if isinstance(dob, str):
        try:
            age = calculate_age(dob)
            valid_dob = 0 <= age <= 120
        except (ValueError, TypeError):
            pass

    check(
        "Valid date of birth",
        valid_dob,
        "Valid YYYY-MM-DD date supplied" if valid_dob
        else "DOB missing or invalid; verify candidate identity",
    )

    age_ok = None if age is None else 21 <= age <= 55
    check(
        "Age range (21–55)",
        age_ok,
        f"Calculated age: {age}" if age is not None
        else "Age cannot be calculated; human review required",
    )

    # 3–15: Job-related criteria
    experience = data.get("experience_years")
    check(
        "Minimum 2 years relevant experience",
        None if experience is None else (
            isinstance(experience, (int, float))
            and not isinstance(experience, bool)
            and experience >= 2
        ),
        "Relevant experience must be at least 2 years",
    )

    check(
        "Legally authorized to work",
        data.get("legally_authorized"),
        "Confirm work authorization requirements for the role",
    )

    start_days = data.get("start_within_days")
    check(
        "Available to start within 30 days",
        None if start_days is None else (
            isinstance(start_days, (int, float))
            and not isinstance(start_days, bool)
            and 0 <= start_days <= 30
        ),
        "Confirm expected joining date",
    )

    check(
        "Willing to work full-time",
        data.get("full_time"),
        "Confirm full-time availability",
    )

    check(
        "No job abandonment in last 12 months",
        data.get("no_job_abandonment"),
        "Review relevant employment history consistently",
    )

    check(
        "Meets role-specific education requirement",
        data.get("education_qualified"),
        "Compare qualifications with the published job requirements",
    )

    check(
        "All required screening questions answered",
        data.get("all_questions_answered"),
        "Required screening answers must be complete",
    )

    check(
        "Accepts advertised salary range",
        data.get("salary_accepted"),
        "Confirm agreement with the disclosed salary range",
    )

    check(
        "Meets job-related language requirement",
        data.get("language_qualified"),
        "Assess only the language level required for the role",
    )

    check(
        "Location/work arrangement is suitable",
        data.get("location_suitable"),
        "Confirm commute or remote-work requirements",
    )

    experience_cap = data.get("experience_cap")
    cap_result = None
    if experience is not None and experience_cap is not None:
        if (
            isinstance(experience, (int, float))
            and not isinstance(experience, bool)
            and isinstance(experience_cap, (int, float))
            and not isinstance(experience_cap, bool)
            and experience_cap >= 0
        ):
            cap_result = experience <= experience_cap

    check(
        "Within role's maximum experience cap (if applicable)",
        cap_result,
        "Supply a maximum only when objectively required for the role",
    )

    check(
        "Accepts required working hours",
        data.get("hours_accepted"),
        "Confirm the role's disclosed working hours",
    )

    check(
        "Agrees to interview scheduling",
        data.get("willing_to_interview"),
        "Confirm candidate consent to proceed",
    )

    statuses = [item["status"] for item in checks]
    failed = sum(status == "FAIL" for status in statuses)
    review = sum(status == "REVIEW" for status in statuses)
    passed = sum(status == "PASS" for status in statuses)

    # This is a recommendation, not an autonomous hiring decision.
    if failed:
        recommendation = "RECRUITER_REVIEW_REQUIRED"
    elif review:
        recommendation = "PENDING_INFORMATION"
    else:
        recommendation = "READY_FOR_RECRUITER_REVIEW"

    return {
        "age": age,
        "passed_count": passed,
        "failed_count": failed,
        "review_count": review,
        "recommendation": recommendation,
        "checks": checks,
    }

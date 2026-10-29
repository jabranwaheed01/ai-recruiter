
from contextlib import asynccontextmanager
from datetime import date, datetime
from typing import Literal
import json
import logging

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import Candidate, Call, CallResult
from app.tools.eligibility import evaluate_eligibility
from app.services.vapi_service import client
from app.config import (
    VAPI_GREETING_ASSISTANT_ID,
    VAPI_VERIFICATION_ASSISTANT_ID,
    VAPI_SCREENING_ASSISTANT_ID,
    VAPI_SCHEDULING_ASSISTANT_ID,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="AI Recruiter API",
    version="1.2.0",
    description="Candidate management and AI recruitment call tracking",
    lifespan=lifespan,
)


class CandidateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    phone: str = Field(min_length=3, max_length=30)
    email: str | None = None
    job_title: str | None = None
    dob: date | None = None


class CandidateResponse(CandidateCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DOBVerificationRequest(BaseModel):
    dob: date
    call_id: int | None = None


class CallCreate(BaseModel):
    candidate_id: int
    assistant_id: str | None = None
    vapi_call_id: str | None = None


class CallResponse(BaseModel):
    id: int
    candidate_id: int
    assistant_id: str | None
    vapi_call_id: str | None
    status: str
    transcript: str | None
    recording_url: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CallUpdate(BaseModel):
    status: Literal[
        "LVM", "HungUp", "NotEligible", "Eligible", "PreBooked",
        "Booked", "Transferred", "RCB", "NotInterested", "Busy",
        "Failed", "NoAnswer", "Pending", "InProgress", "Completed"
    ]
    transcript: str | None = None
    recording_url: str | None = None
    outcome: str | None = None
    notes: str | None = None


class StartCallRequest(BaseModel):
    candidate_id: int
    stage: Literal[
        "greeting", "verification", "screening", "scheduling"
    ] = "greeting"


ASSISTANT_IDS = {
    "greeting": VAPI_GREETING_ASSISTANT_ID,
    "verification": VAPI_VERIFICATION_ASSISTANT_ID,
    "screening": VAPI_SCREENING_ASSISTANT_ID,
    "scheduling": VAPI_SCHEDULING_ASSISTANT_ID,
}



@app.get("/")
def health_check():
    return {
        "status": "running",
        "service": "AI Recruiter API",
        "version": "1.2.0",
    }


@app.post(
    "/candidates",
    response_model=CandidateResponse,
    status_code=201,
)
def create_candidate(
    data: CandidateCreate,
    db: Session = Depends(get_db),
):
    candidate_data = data.model_dump()

    # Store DOB as ISO YYYY-MM-DD text in SQLite.
    if candidate_data["dob"] is not None:
        candidate_data["dob"] = candidate_data["dob"].isoformat()

    candidate = Candidate(**candidate_data)
    db.add(candidate)

    try:
        db.commit()
        db.refresh(candidate)
    except Exception:
        db.rollback()
        logger.exception("Could not create candidate")
        raise HTTPException(
            status_code=500,
            detail="Could not save candidate",
        )

    return candidate


@app.get("/candidates", response_model=list[CandidateResponse])
def list_candidates(db: Session = Depends(get_db)):
    return db.query(Candidate).order_by(Candidate.id.desc()).all()


@app.get(
    "/candidates/{candidate_id}",
    response_model=CandidateResponse,
)
def get_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
):
    candidate = db.get(Candidate, candidate_id)

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found",
        )

    return candidate


@app.post("/candidates/{candidate_id}/verify-dob")
def verify_candidate_dob(
    candidate_id: int,
    data: DOBVerificationRequest,
    db: Session = Depends(get_db),
):
    candidate = db.get(Candidate, candidate_id)

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found",
        )

    if not candidate.dob:
        raise HTTPException(
            status_code=409,
            detail=(
                "No DOB is stored for this candidate. "
                "Verification cannot be completed."
            ),
        )

    verified = candidate.dob == data.dob.isoformat()

    call = None
    result = None

    if data.call_id is not None:
        call = db.get(Call, data.call_id)

        if call is None or call.candidate_id != candidate_id:
            raise HTTPException(
                status_code=404,
                detail="Call not found for this candidate",
            )

        result = (
            db.query(CallResult)
            .filter(CallResult.call_id == call.id)
            .first()
        )

        if result is None:
            result = CallResult(
                call_id=call.id,
                outcome=call.status,
            )
            db.add(result)

        result.dob_verified = "true" if verified else "false"

    try:
        if data.call_id is not None:
            db.commit()
    except Exception:
        db.rollback()
        logger.exception("Could not save DOB verification result")
        raise HTTPException(
            status_code=500,
            detail="Could not save DOB verification result",
        )

    return {
        "candidate_id": candidate.id,
        "verified": verified,
        "result_saved": data.call_id is not None,
        "message": (
            "DOB verified successfully"
            if verified
            else "DOB did not match the saved record"
        ),
    }



@app.post("/calls", response_model=CallResponse, status_code=201)
def create_call(
    data: CallCreate,
    db: Session = Depends(get_db),
):
    candidate = db.get(Candidate, data.candidate_id)

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found",
        )

    call = Call(
        **data.model_dump(),
        status="Pending",
    )
    db.add(call)

    try:
        db.flush()
        result = CallResult(
            call_id=call.id,
            outcome="Pending",
        )
        db.add(result)
        db.commit()
        db.refresh(call)
    except Exception:
        db.rollback()
        logger.exception("Could not create call record")
        raise HTTPException(
            status_code=500,
            detail="Could not save call record",
        )

    return call


@app.post("/calls/start", status_code=201)
def start_outbound_call(
    data: StartCallRequest,
    db: Session = Depends(get_db),
):
    candidate = db.get(Candidate, data.candidate_id)

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found",
        )

    assistant_id = ASSISTANT_IDS[data.stage]

    try:
        phone_numbers = client.phone_numbers.list()
    except Exception as exc:
        logger.exception("Could not retrieve VAPI phone numbers")
        raise HTTPException(
            status_code=502,
            detail="Could not retrieve phone numbers from VAPI.",
        ) from exc

    if not phone_numbers:
        raise HTTPException(
            status_code=503,
            detail=(
                "No VAPI phone number is configured. "
                "Configure an outbound-capable phone number first."
            ),
        )

    phone_number_id = getattr(phone_numbers[0], "id", None)

    if not phone_number_id:
        raise HTTPException(
            status_code=503,
            detail="VAPI phone number has no usable ID.",
        )

    try:
        vapi_call = client.calls.create(
            assistant_id=assistant_id,
            phone_number_id=phone_number_id,
            customer={
                "number": candidate.phone,
                "name": candidate.name,
            },
        )
    except Exception as exc:
        logger.exception("VAPI outbound call creation failed")
        raise HTTPException(
            status_code=502,
            detail=(
                "VAPI could not start the call. "
                "Check phone number and assistant configuration."
            ),
        ) from exc

    vapi_call_id = getattr(vapi_call, "id", None)

    try:
        call = Call(
            candidate_id=candidate.id,
            assistant_id=assistant_id,
            vapi_call_id=vapi_call_id,
            status="InProgress",
        )
        db.add(call)
        db.flush()

        result = CallResult(
            call_id=call.id,
            outcome="InProgress",
        )
        db.add(result)
        db.commit()
        db.refresh(call)

    except Exception as exc:
        db.rollback()
        logger.exception(
            "VAPI call started but database persistence failed"
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "The VAPI call may have started, but its database "
                "record could not be saved. Check VAPI call history."
            ),
        ) from exc

    return {
        "message": "VAPI call initiated",
        "call_id": call.id,
        "vapi_call_id": call.vapi_call_id,
        "candidate_id": candidate.id,
        "stage": data.stage,
        "assistant_id": assistant_id,
        "status": call.status,
    }


@app.get("/calls", response_model=list[CallResponse])
def list_calls(db: Session = Depends(get_db)):
    return db.query(Call).order_by(Call.id.desc()).all()


@app.patch("/calls/{call_id}", response_model=CallResponse)
def update_call(
    call_id: int,
    data: CallUpdate,
    db: Session = Depends(get_db),
):
    call = db.get(Call, call_id)

    if not call:
        raise HTTPException(
            status_code=404,
            detail="Call not found",
        )

    call.status = data.status

    if data.transcript is not None:
        call.transcript = data.transcript

    if data.recording_url is not None:
        call.recording_url = data.recording_url

    result = (
        db.query(CallResult)
        .filter(CallResult.call_id == call_id)
        .first()
    )

    if not result:
        result = CallResult(
            call_id=call_id,
            outcome="Pending",
        )
        db.add(result)

    if data.outcome is not None:
        result.outcome = data.outcome

    if data.notes is not None:
        result.notes = data.notes

    if data.status in {"Booked", "PreBooked"}:
        result.outcome = data.status

    try:
        db.commit()
        db.refresh(call)
    except Exception:
        db.rollback()
        logger.exception("Could not update call")
        raise HTTPException(
            status_code=500,
            detail="Could not update call",
        )

    return call


@app.get("/calls/{call_id}/result")
def get_call_result(
    call_id: int,
    db: Session = Depends(get_db),
):
    call = db.get(Call, call_id)

    if not call:
        raise HTTPException(
            status_code=404,
            detail="Call not found",
        )

    result = (
        db.query(CallResult)
        .filter(CallResult.call_id == call_id)
        .first()
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Call result not found",
        )

    return {
        "call_id": call.id,
        "candidate_id": call.candidate_id,
        "status": call.status,
        "outcome": result.outcome,
        "dob_verified": result.dob_verified,
        "eligible": result.eligible,
        "notes": result.notes,
        "interview_datetime": result.interview_datetime,
        "transcript": call.transcript,
        "recording_url": call.recording_url,
    }



@app.post("/eligibility/evaluate")
def evaluate_candidate_eligibility(data: dict):
    """Evaluate screening answers for recruiter review."""
    try:
        return evaluate_eligibility(data)
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc



class ScheduleInterviewRequest(BaseModel):
    interview_datetime: datetime


@app.post("/calls/{call_id}/schedule")
def schedule_interview(
    call_id: int,
    data: ScheduleInterviewRequest,
    db: Session = Depends(get_db),
):
    call = db.get(Call, call_id)

    if not call:
        raise HTTPException(
            status_code=404,
            detail="Call not found",
        )

    if call.status not in {"Eligible", "PreBooked", "Booked"}:
        raise HTTPException(
            status_code=400,
            detail="Only eligible candidates can be scheduled",
        )

    if data.interview_datetime <= datetime.now():
        raise HTTPException(
            status_code=422,
            detail="Interview datetime must be in the future",
        )

    result = (
        db.query(CallResult)
        .filter(CallResult.call_id == call_id)
        .first()
    )

    if not result:
        result = CallResult(
            call_id=call_id,
            outcome="Pending",
        )
        db.add(result)

    result.interview_datetime = data.interview_datetime
    result.outcome = "Booked"
    result.notes = (
        f"{result.notes}\nInterview scheduled for "
        f"{data.interview_datetime.isoformat()}"
        if result.notes
        else f"Interview scheduled for {data.interview_datetime.isoformat()}"
    )
    call.status = "Booked"

    try:
        db.commit()
        db.refresh(call)
        db.refresh(result)
    except Exception:
        db.rollback()
        logger.exception("Could not schedule interview")
        raise HTTPException(
            status_code=500,
            detail="Could not schedule interview",
        )

    return {
        "message": "Interview scheduled successfully",
        "call_id": call.id,
        "candidate_id": call.candidate_id,
        "status": call.status,
        "interview_datetime": result.interview_datetime,
        "outcome": result.outcome,
    }




@app.post("/vapi/tools")
def vapi_tools_webhook(
    payload: dict,
    db: Session = Depends(get_db),
):
    """Handle VAPI function-tool calls."""
    message = payload.get("message", {})
    tool_calls = message.get("toolCallList", [])
    results = []

    for item in tool_calls:
        tool_call_id = item.get("id", "")
        function = item.get("function", {})
        name = function.get("name", "")
        arguments = function.get("arguments", {})

        try:
            if isinstance(arguments, str):
                arguments = json.loads(arguments)

            if not isinstance(arguments, dict):
                raise ValueError("Tool arguments must be a JSON object.")

            if name == "evaluate_eligibility":
                evaluation = evaluate_eligibility(arguments)

                results.append({
                    "toolCallId": tool_call_id,
                    "result": json.dumps(evaluation),
                })

            elif name == "schedule_interview":
                call_id = arguments.get("call_id")
                interview_datetime = arguments.get("interview_datetime")

                if call_id is None or not interview_datetime:
                    raise ValueError(
                        "call_id and interview_datetime are required."
                    )

                try:
                    parsed_datetime = datetime.fromisoformat(
                        str(interview_datetime).replace("Z", "+00:00")
                    )
                except (ValueError, TypeError) as exc:
                    raise ValueError(
                        "interview_datetime must be valid ISO 8601."
                    ) from exc

                call = db.get(Call, int(call_id))

                if call is None:
                    raise ValueError("Call not found.")

                if call.status not in {"Eligible", "PreBooked", "Booked"}:
                    raise ValueError(
                        "Only eligible candidates can be scheduled."
                    )

                if parsed_datetime.tzinfo is not None:
                    from datetime import timezone

                    parsed_datetime = parsed_datetime.astimezone(
                        timezone.utc
                    ).replace(tzinfo=None)

                if parsed_datetime <= datetime.utcnow():
                    raise ValueError(
                        "Interview datetime must be in the future."
                    )

                result = (
                    db.query(CallResult)
                    .filter(CallResult.call_id == call.id)
                    .first()
                )

                if result is None:
                    result = CallResult(
                        call_id=call.id,
                        outcome="Pending",
                    )
                    db.add(result)

                result.interview_datetime = parsed_datetime
                result.outcome = "Booked"
                result.notes = (
                    f"{result.notes}\nInterview scheduled for "
                    f"{parsed_datetime.isoformat()}"
                    if result.notes
                    else f"Interview scheduled for "
                    f"{parsed_datetime.isoformat()}"
                )
                call.status = "Booked"

                db.commit()

                results.append({
                    "toolCallId": tool_call_id,
                    "result": json.dumps({
                        "success": True,
                        "call_id": call.id,
                        "candidate_id": call.candidate_id,
                        "status": "Booked",
                        "interview_datetime": parsed_datetime.isoformat(),
                        "message": "Interview booking saved successfully."
                    }),
                })


            elif name == "verify_dob":
                candidate_id = arguments.get("candidate_id")
                call_id = arguments.get("call_id")
                submitted_dob = arguments.get("dob")

                if candidate_id is None or call_id is None or not submitted_dob:
                    raise ValueError(
                        "candidate_id, call_id, and dob are required."
                    )

                try:
                    parsed_dob = date.fromisoformat(str(submitted_dob))
                except (ValueError, TypeError) as exc:
                    raise ValueError(
                        "dob must use YYYY-MM-DD format."
                    ) from exc

                candidate = db.get(Candidate, int(candidate_id))
                call = db.get(Call, int(call_id))

                if candidate is None:
                    raise ValueError("Candidate not found.")

                if call is None or call.candidate_id != candidate.id:
                    raise ValueError(
                        "Call does not belong to this candidate."
                    )

                if not candidate.dob:
                    raise ValueError(
                        "No saved DOB exists for this candidate."
                    )

                verified = candidate.dob == parsed_dob.isoformat()

                result = (
                    db.query(CallResult)
                    .filter(CallResult.call_id == call.id)
                    .first()
                )

                if result is None:
                    result = CallResult(
                        call_id=call.id,
                        outcome=call.status,
                    )
                    db.add(result)

                result.dob_verified = "true" if verified else "false"
                db.commit()

                tool_result = {
                    "candidate_id": candidate.id,
                    "call_id": call.id,
                    "verified": verified,
                    "message": (
                        "DOB verified successfully"
                        if verified
                        else "DOB did not match the saved record"
                    ),
                }

                results.append({
                    "toolCallId": tool_call_id,
                    "result": json.dumps(tool_result),
                })

            else:
                results.append({
                    "toolCallId": tool_call_id,
                    "error": f"Unknown tool: {name}",
                })

        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            db.rollback()
            results.append({
                "toolCallId": tool_call_id,
                "error": str(exc),
            })

        except Exception:
            db.rollback()
            logger.exception("VAPI tool execution failed")
            results.append({
                "toolCallId": tool_call_id,
                "error": "Tool execution failed.",
            })

    return {"results": results}


@app.post("/vapi/events")
def vapi_call_events(
    payload: dict,
    db: Session = Depends(get_db),
):
    """Persist VAPI call status, transcript, and recording events."""
    message = payload.get("message", payload)
    event_type = message.get("type", "")

    if event_type not in {"status-update", "end-of-call-report"}:
        return {
            "received": True,
            "processed": False,
            "event_type": event_type,
        }

    vapi_call = message.get("call") or {}
    vapi_call_id = vapi_call.get("id")

    if not vapi_call_id:
        raise HTTPException(
            status_code=422,
            detail="VAPI event is missing call.id",
        )

    call = (
        db.query(Call)
        .filter(Call.vapi_call_id == vapi_call_id)
        .first()
    )

    if not call:
        return {
            "received": True,
            "processed": False,
            "reason": "No matching local call record",
        }

    artifact = message.get("artifact") or {}
    call_status = vapi_call.get("status") or message.get("status")

    if call_status == "in-progress":
        call.status = "InProgress"
        if call.started_at is None:
            call.started_at = datetime.utcnow()

    elif call_status in {"ended", "completed"}:
        call.status = "Completed"
        if call.ended_at is None:
            call.ended_at = datetime.utcnow()

    elif call_status in {"queued", "ringing"}:
        call.status = "Pending"

    transcript = (
        artifact.get("transcript")
        or vapi_call.get("transcript")
        or message.get("transcript")
    )
    recording_url = (
        artifact.get("recordingUrl")
        or artifact.get("recording_url")
        or vapi_call.get("recordingUrl")
    )

    if transcript:
        call.transcript = transcript

    if recording_url:
        call.recording_url = recording_url

    result = (
        db.query(CallResult)
        .filter(CallResult.call_id == call.id)
        .first()
    )

    if result is None:
        result = CallResult(
            call_id=call.id,
            outcome=call.status,
        )
        db.add(result)

    if call_status in {"ended", "completed"}:
        result.outcome = "Completed"

        ended_reason = (
            message.get("endedReason")
            or vapi_call.get("endedReason")
        )
        if ended_reason:
            result.notes = f"VAPI ended reason: {ended_reason}"[:5000]

    try:
        db.commit()
        db.refresh(call)
    except Exception:
        db.rollback()
        logger.exception("Failed to save VAPI call event")
        raise HTTPException(
            status_code=500,
            detail="Could not save VAPI call event",
        )

    return {
        "received": True,
        "processed": True,
        "call_id": call.id,
        "status": call.status,
    }


from app.services.vapi_service import client


def create_scheduling_assistant():
    assistant = client.assistants.create(
        name="AI Recruiter - Interview Scheduling",
        first_message=(
            "Thank you for completing the screening. "
            "Would you like to discuss a suitable time for an interview?"
        ),
        model={
            "provider": "openai",
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a professional interview scheduling assistant. "
                        "Ask the candidate for their preferred interview date and time. "
                        "Offer only time slots explicitly provided by the scheduling system. "
                        "Never invent availability or claim a booking is confirmed unless "
                        "the booking tool confirms it. "

                        "Before booking, repeat the selected date and time with its timezone "
                        "and get confirmation from the candidate. "

                        "After confirmation, call the schedule_interview tool. "
                        "Use the actual internal call_id provided by the backend context. "
                        "Never invent or guess a call_id. "
                        "Pass the confirmed interview date and time in ISO 8601 format. "

                        "Only tell the candidate that the interview is booked if the tool "
                        "returns success=true. If the tool fails, explain that the booking "
                        "could not be confirmed. "

                        "If no scheduling tool or slots are available, collect the "
                        "candidate's preference and explain that the recruitment team "
                        "will confirm the appointment. "
                        "Be polite and concise."
                    ),
                }
            ],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "schedule_interview",
                        "description": (
                            "Save the candidate's confirmed interview date and time "
                            "in the AI Recruiter backend database."
                        ),
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "call_id": {
                                    "type": "integer",
                                    "description": (
                                        "Existing internal database Call ID. "
                                        "Must be provided by backend context."
                                    ),
                                },
                                "interview_datetime": {
                                    "type": "string",
                                    "format": "date-time",
                                    "description": (
                                        "Confirmed interview date and time in ISO 8601 "
                                        "format, including timezone."
                                    ),
                                },
                            },
                            "required": [
                                "call_id",
                                "interview_datetime",
                            ],
                        },
                    },
                    "server": {
                        "url": (
                            "https://skydiver-spinout-depict.ngrok-free.dev/vapi/tools"
                        ),
                    },
                }
            ],
            "temperature": 0.2,
            "max_tokens": 300,
        },
        voice={
            "provider": "vapi",
            "voice_id": "Elliot",
        },
        transcriber={
            "provider": "deepgram",
            "model": "nova-2",
            "language": "en",
        },
        first_message_mode="assistant-speaks-first",
        end_call_message="Thank you. Have a nice day!",
        max_duration_seconds=300,
    )

    print("Scheduling Assistant created successfully.")
    print("Assistant ID:", assistant.id)

    return assistant


if __name__ == "__main__":
    create_scheduling_assistant()

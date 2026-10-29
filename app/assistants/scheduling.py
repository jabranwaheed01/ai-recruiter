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
                        "the booking tool confirms it. Repeat the selected date and time "
                        "with its timezone before booking. If no scheduling tool or slots "
                        "are available, collect the candidate's preference and explain "
                        "that the recruitment team will confirm the appointment. "
                        "Be polite and concise."
                    ),
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
        end_call_message="Thank you. We will follow up about your interview schedule.",
        max_duration_seconds=300,
    )

    print("Scheduling Assistant created successfully.")
    print("Assistant ID:", assistant.id)
    return assistant


if __name__ == "__main__":
    create_scheduling_assistant()

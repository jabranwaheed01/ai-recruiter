from app.services.vapi_service import client


def create_verification_assistant():
    assistant = client.assistants.create(
        name="AI Recruiter - DOB Verification",
        first_message=(
            "Thank you. Before we continue, I need to verify your date of birth. "
            "Could you please provide your date of birth?"
        ),
        model={
            "provider": "openai",
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a professional recruitment verification assistant. "
                        "Ask the candidate for their date of birth only when needed "
                        "for authorized identity verification. Confirm the date clearly "
                        "and compare it only with an authorized verification record "
                        "when one is provided by the system. Never invent or assume "
                        "the candidate's date of birth. If no verification record or "
                        "verification tool is available, explain that verification "
                        "cannot be completed yet. Keep personal information private."
                    ),
                }
            ],
            "temperature": 0.2,
            "max_tokens": 250,
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
        end_call_message="Thank you for your time.",
        max_duration_seconds=300,
    )

    print("DOB Verification Assistant created successfully.")
    print("Assistant ID:", assistant.id)
    return assistant


if __name__ == "__main__":
    create_verification_assistant()

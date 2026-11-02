from app.services.vapi_service import client
from app.config import VAPI_SCREENING_ASSISTANT_ID


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
                        "You are a professional and friendly recruitment assistant. "
                        "Your job is to verify the candidate's identity using their "
                        "authorized date-of-birth record. "
                        "Ask the candidate for their date of birth when needed. "
                        "Repeat the date to confirm that you understood it correctly. "
                        "Never invent or assume personal information. "
                        "Compare the provided date only with the authorized verification "
                        "record or verification tool result. "
                        "If verification is successful, smoothly continue the recruitment "
                        "conversation with eligibility-related questions. "
                        "Never mention internal assistants, agents, handoffs, transfers, "
                        "or AI squad architecture. "
                        "Never say 'I'll connect you to the screening assistant' or "
                        "similar phrases. "
                        "Keep the transition natural, as if this is one continuous conversation. "
                        "If verification fails, do not proceed to eligibility screening. "
                        "Politely explain that identity verification could not be completed."
                    )
                }
            ],

            "tools": [         
                {
                "type": "handoff",
                "messages": [],
                "destinations": [
                    {
                    "type": "assistant",
                    "assistantId": VAPI_SCREENING_ASSISTANT_ID,
                    "description": (
                        "Use silently after successful identity verification. "
                        "Continue the candidate's recruitment conversation naturally. "
                        "Do not announce the handoff."
                    ),
                    "contextEngineeringPlan": {
                        "type": "all"
                    }
                    }
                ]
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

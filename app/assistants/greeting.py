from app.services.vapi_service import client
from app.config import VAPI_VERIFICATION_ASSISTANT_ID


def create_greeting_assistant():
    assistant = client.assistants.create(
        name="AI Recruiter - Greeting",
        first_message="Hello, this is the AI recruiting assistant calling regarding your job application. Is this a good time to speak?",
        model={
            "provider": "openai",
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a professional and friendly AI recruiting assistant. "
                        "Introduce yourself clearly, explain that you are calling about "
                        "the candidate's job application, and ask whether they can speak. "
                        "Respect the candidate's choice if they are busy or do not want "
                        "to continue. Never invent candidate information. "
                        "Do not ask for sensitive personal information during the greeting. "
                        "If the candidate agrees, explain that you will proceed with "
                        "identity verification and eligibility screening. "
                        "If the candidate agrees to continue, briefly explain that "
                        "identity verification is the next step, then invoke the "
                        "handoff_to_verification tool. Do not invoke the handoff if "
                        "the candidate declines, is busy, or does not consent to continue. "
                        "If the handoff fails, politely explain that the transfer could "
                        "not be completed."
                    ),
                }
            ],

            "tools": [
                            
                            {
                            "type": "handoff",
                            "destinations": [
                                {
                                "type": "assistant",
                                "assistantId": "VAPI_VERIFICATION_ASSISTANT_ID",
                                "description": 
                                    "Use when the candidate agrees to continue and "
                                    "is ready for identity verification.",
                                "contextEngineeringPlan": {
                                    "type": "all"
                                }
                                }
                            ]
                            }
            ],

            "temperature": 0.3,
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
        end_call_message="Thank you for your time. Have a nice day!",
        max_duration_seconds=600,
    )

    print("Greeting Assistant created successfully.")
    print("Assistant ID:", assistant.id)
    return assistant


if __name__ == "__main__":
    create_greeting_assistant()

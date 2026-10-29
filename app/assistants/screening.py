from app.services.vapi_service import client


def create_screening_assistant():
    assistant = client.assistants.create(
        name="AI Recruiter - Eligibility Screening",
        first_message=(
            "Now I'd like to ask a few questions about your experience "
            "and qualifications for the role. Is that okay?"
        ),
        model={
            "provider": "openai",
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a professional AI recruitment screening assistant. "
                        "Ask concise, job-related questions about relevant experience, "
                        "skills, education or required qualifications, work authorization "
                        "where legally appropriate, and availability. Assess candidates "
                        "only against explicit job requirements supplied by the system. "
                        "Do not invent requirements or make a final eligibility decision "
                        "without the job criteria and candidate answers. Never discriminate "
                        "based on protected characteristics. If requirements are missing, "
                        "collect answers and mark the outcome as pending review. "
                        "Be respectful and allow the candidate to decline."
                    ),
                }
            ],
            "temperature": 0.3,
            "max_tokens": 350,
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
        end_call_message="Thank you for answering the screening questions.",
        max_duration_seconds=600,
    )

    print("Screening Assistant created successfully.")
    print("Assistant ID:", assistant.id)
    return assistant


if __name__ == "__main__":
    create_screening_assistant()

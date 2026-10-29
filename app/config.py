import os
from dotenv import load_dotenv

load_dotenv()

VAPI_API_KEY = os.getenv("VAPI_API_KEY")

if not VAPI_API_KEY:
    raise ValueError("VAPI_API_KEY .env file mein set nahi hai")



VAPI_GREETING_ASSISTANT_ID = "ef4569b3-3101-4c2b-a419-23d2522ceb3f"
VAPI_VERIFICATION_ASSISTANT_ID = "ccb4ac50-58c3-40a3-b9d9-4081aaf441d6"
VAPI_SCREENING_ASSISTANT_ID = "08bbcb03-e0c0-4aee-981a-c463c767c710"
VAPI_SCHEDULING_ASSISTANT_ID = "c4296a18-8448-4b7e-bb00-13c9962151b7"

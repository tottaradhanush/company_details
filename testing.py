import google.generativeai as genai

from dotenv import load_dotenv

# Load API Key from .env file
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure API key
genai.configure(api_key=GEMINI_API_KEY)

# Check available models
available_models = genai.list_models()
print("Available Models:", [model.name for model in available_models])

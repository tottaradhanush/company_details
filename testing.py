import google.generativeai as genai

# Configure API key
genai.configure(api_key="AIzaSyCdBk2we_8zBFhzhi_QJqzr1qywXMGqqxo")

# Check available models
available_models = genai.list_models()
print("Available Models:", [model.name for model in available_models])

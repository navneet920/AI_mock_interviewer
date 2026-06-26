from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


class LLMService:

    @staticmethod
    def get_llm():
        llm=ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.7
        )
        return llm

# from langchain_groq import ChatGroq
# from dotenv import load_dotenv
# load_dotenv()
#
# class LLMService:
#
#     @staticmethod
#     def get_llm():
#         llm = ChatGroq(
#             model="openai/gpt-oss-120b",
#             temperature=0.3,
#             reasoning_format="hidden",
#             model_kwargs={
#                 "response_format": {
#                     "type": "json_object"
#                 }
#             },
#             #groq_api_key="YOUR_API_KEY"
#         )
#         return llm
#

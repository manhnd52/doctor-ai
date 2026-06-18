from typing import Optional
from langchain.chat_models import BaseChatModel, init_chat_model
from langchain_openai import ChatOpenAI
from langchain_gradient import ChatGradient  

model = init_chat_model("gpt-5-nano", temperature=0.0)

inference_server_url = "http://liacara-dev-ai-service-alb-405568302.eu-central-1.elb.amazonaws.com/v1"

digital_ocean_url = "https://inference.do-ai.run/v1/"

# free_model = ChatOpenAI(
#     model="Qwen/Qwen3-14B",
#     temperature=0.0,
#     base_url=inference_server_url,
# )

def get_model():
    return model
    


from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from tools import get_all_tools
from dotenv import load_dotenv
import os

load_dotenv()





llm = ChatGroq(
    model="qwen/qwen3-32b",
    temperature=0,
    max_tokens=None,
    reasoning_format="parsed",
    timeout=None,
    max_retries=2,
    # other params...
)

prompte_template="""

you are dodge ai your task is to perform data opreations  and provided answer based on data you have multimple tools you can use please only  answer for data operations and  question about data
not anything else you can only read the data  you cannot edit  or alter the data

"""
agent = create_agent(model=llm, tools=get_all_tools(),system_prompt=prompte_template)


def llm_response(query):
    response=agent.invoke({"input": query})
    return response["messages"][-1].content



# Test run
if __name__ == "__main__":
    query = "Show me all data from the sales table for the last month."
    result = llm_response(query)
    print(result)













# src/tools/tool_selection.py

from typing import List
from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Initialize the LLM
llm = ChatOllama(model_name="llama3.2", temperature=0)

# Define the prompt template for tool selection
prompt_template = PromptTemplate(
    input_variables=["task_description"],
    template=(
        "You are an AI assistant that selects the appropriate tools based on user queries.\n\n"
        "Task Description:\n{task_description}\n\n"
        "Available Tools:\n"
        "1. Vector Store Search: For historical error data and resolutions.\n"
        "2. Datadog Logs Fetcher: For real-time logs and traces.\n"
        "3. API Documentation Retriever: For fetching relevant API documentation.\n\n"
        "Determine which tools are necessary to address the user's query and provide a brief explanation for each selection."
    )
)

# Create the LLMChain for tool selection
tool_selection_chain = LLMChain(llm=llm, prompt=prompt_template)

def select_tools(task_description: str) -> List[str]:
    """
    Analyze the user query and select appropriate tools.

    Args:
        task_description (str): The user's query regarding an error or issue.

    Returns:
        List[str]: A list of selected tools to address the query.
    """
    # Run the tool selection chain
    tool_selection_response = tool_selection_chain.invoke(task_description=task_description)

    # Parse the response to extract selected tools
    selected_tools = []
    if "Vector Store Search" in tool_selection_response:
        selected_tools.append("vector_store")
    if "Datadog Logs Fetcher" in tool_selection_response:
        selected_tools.append("datadog")
    if "API Documentation Retriever" in tool_selection_response:
        selected_tools.append("api_docs")

    return selected_tools

# src/tools/tool_selection.py

from typing import List
from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel
from typing import List

# Initialize the LLM
llm = ChatOllama(model="llama3.2", temperature=0)

# Define the prompt template for tool selection


# Define a Pydantic model for the output
class ToolSelectionOutput(BaseModel):
    tools: List[str]

# Define the Pydantic output parser
output_parser = PydanticOutputParser(pydantic_object=ToolSelectionOutput)

prompt_template = PromptTemplate(
    
    template=(
        "You are an AI assistant that selects the appropriate tools based on user queries.\n\n"
        "Task Description:\n{task_description}\n\n"
        "Available Tools:\n"
        "1. vector_store_search: For historical error data and resolutions.\n"
        "2. datadog_fetch: For real-time logs and traces.\n"
        "3. retrieve_knowledge: For fetching relevant API documentation.\n\n"
        "Determine which tools are necessary to address the user's query and provide a structured output with only "
        "the tool names in a list."
        "{format_instructions}\n"
    ),
    input_variables=["task_description"],
    partial_variables={"format_instructions": output_parser.get_format_instructions()}
)

# Create the LLMChain for tool selection with the Pydantic output parser
tool_selection_chain = prompt_template | llm | output_parser


def select_tools(task_description: str) -> List[str]:
    """
    Analyze the user query and select appropriate tools.

    Args:
        task_description (str): The user's query regarding an error or issue.

    Returns:
        List[str]: A list of selected tools to address the query.
    """
    # Run the tool selection chain
    tool_selection_response = tool_selection_chain.invoke({"task_description": task_description})
    
    # Parse the response to extract selected tools
    selected_tools = []
    if "vector_store_search" in tool_selection_response.tools:
        selected_tools.append("vector_store")
    if "datadog_fetch" in tool_selection_response.tools:
        selected_tools.append("datadog")
    if "retrieve_knowledge" in tool_selection_response.tools:
        selected_tools.append("api_docs")

    return selected_tools

from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchResults
import json

@tool
def web_search(query: str) -> str:
    """Χρησιμοποιείται για αναζήτηση πληροφοριών στο διαδίκτυο. Δέχεται ένα search query."""
    search = DuckDuckGoSearchResults()
    try:
        return search.invoke(query)
    except Exception as e:
        return f"Error during web search: {str(e)}"

@tool
def calculator(expression: str) -> str:
    """Χρησιμοποιείται για μαθηματικούς υπολογισμούς. Δέχεται ένα μαθηματικό string, π.χ. '5 * (10 + 2)'."""
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error calculating: {str(e)}"

@tool
def file_reader(file_path: str) -> str:
    """Διαβάζει το περιεχόμενο ενός τοπικού αρχείου. Δέχεται το path του αρχείου."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

# leksiko gia na kaloume ta ergaleia
TOOLS_MAP = {
    "web_search": web_search,
    "calculator": calculator,
    "file_reader": file_reader
}
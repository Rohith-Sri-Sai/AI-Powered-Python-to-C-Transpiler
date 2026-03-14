import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_cohere import ChatCohere
from langchain_core.prompts import PromptTemplate

def get_llm(model_choice):
    """Instantiates the selected LLM via LangChain using free-tier APIs."""
    if model_choice == "groq":
        return ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.1)
    
    elif model_choice == "cohere":
        return ChatCohere(model="command-r-08-2024", temperature=0.1)
        
    else: 
        return ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1)

def generate_cpp(ast_string, error_feedback="None", model_choice="gemini"):
    llm = get_llm(model_choice)
    
    template = """
    You are an autonomous Python-to-C++ transpiler.
    Convert this Python AST into highly optimized C++ code.
    
    CRITICAL RULES:
    1. Output ONLY valid C++ code. No markdown blocks, no explanations.
    2. You MUST include these headers at the very top: <iostream>, <vector>, <queue>.
    3. You MUST declare `using namespace std;` globally at the top.
    4. You MUST NOT use the `std::` prefix anywhere in the code. 
    5. Translate Python's `if __name__ == "__main__":` logic directly into a standard C++ `int main()` function. Do not invent macros or use `__name__` in C++.
    
    Previous Compiler Error (Fix this if present):
    {error_feedback}
    
    Python AST:
    {ast_string}
    """
    
    prompt = PromptTemplate.from_template(template)
    chain = prompt | llm
    
    response = chain.invoke({"ast_string": ast_string, "error_feedback": error_feedback})
    
    # Strip markdown if the LLM accidentally includes it in the output
    clean_code = response.content.replace("```cpp", "").replace("```", "").strip()
    return clean_code
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_cohere import ChatCohere
from langchain_core.prompts import PromptTemplate

def get_llm(model_choice):
    """Instantiates the selected LLM via LangChain using free-tier APIs."""
    if model_choice == "groq":
        return ChatGroq(model_name="openai/gpt-oss-120b", temperature=0.1)
    
    elif model_choice == "cohere":
        return ChatCohere(model="command-r-08-2024", temperature=0.1)
        
    else: 
        return ChatGoogleGenerativeAI(model="gemini-3.8-flash", temperature=0.1)

def generate_cpp(ast_string, error_feedback="None", model_choice="gemini"):
    llm = get_llm(model_choice)
    
    
    template = """
    You are an optimizing Python-to-C++ compiler.

    Translate the provided Python AST into correct, efficient,
    readable C++17 code.

    CORRECTNESS:
    1. Preserve Python program semantics and edge cases.
    2. Preserve loop boundaries exactly. Python range(a, b)
    excludes b.
    3. Preserve integer arithmetic, conditions, and return values.
    4. Do not omit special cases or silently change algorithms.
    5. Produce deterministic output for equivalent inputs.
    6. Never sacrifice correctness for speed.

    PERFORMANCE:
    1. Analyze the algorithm's time and space complexity.
    2. Avoid unnecessary allocations and repeated calculations.
    3. Use native C++ types when their ranges are safe.
    4. Reserve vector capacity when the final size is known.
    5. Use cache-friendly loop ordering for array operations.
    6. Avoid unnecessary copies and temporary objects.
    7. Prefer a better algorithm when it preserves semantics
    and is appropriate for the input constraints.
    8. Do not introduce parallelism or unsafe optimizations
    without evidence that they are beneficial.

    OUTPUT:
    1. Output only valid C++17 source code.
    2. Include every required standard-library header.
    3. Include a standard int main() when the Python program
    has executable top-level logic or a main function.
    4. Do not invent inputs, outputs, or functionality.
    5. Do not use undefined behavior.
    6. Ensure the program compiles with g++ -O3.

    Previous compiler feedback:
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
import os
from translator.cpp_generator import generate_cpp
from optimizer.compile import compile_and_test

def autonomous_compilation_loop(ast_data, cpp_output_path, exe_output_path, model_choice, max_retries=3):
    """
    Handles the generate -> compile -> feedback cycle.
    Returns True if successful, False if it fails after max_retries.
    """
    error_log = "None"
    
    for attempt in range(max_retries):
        print(f"   [Loop {attempt+1}/{max_retries}] Generating C++ using {model_choice.upper()}...")
        
        # Generate code, passing any previous error logs back to LangChain
        cpp_code = generate_cpp(ast_data, error_log, model_choice)
        
        # Save the code to the generated/ folder
        with open(cpp_output_path, "w") as f:
            f.write(cpp_code)
            
        print("   Compiling with g++ -O3...")
        success, msg = compile_and_test(cpp_output_path, exe_output_path)
        
        if success:
            print("   Compilation Successful!")
            return True
        else:
            print("    Compilation Failed. Extracting error logs...")
            print(f"      -> Error snippet: {msg[:100]}...") # Show a tiny preview in terminal
            error_log = msg # Feed this exact error back into the next LLM prompt
            
    print("\n Reached maximum retries. The LLM could not resolve the syntax errors.")
    return False
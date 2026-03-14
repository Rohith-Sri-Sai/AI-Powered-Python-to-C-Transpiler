import os
import ast
from dotenv import load_dotenv
load_dotenv()

# Suppress PyTorch/TensorFlow warnings
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

from optimizer.feedback_loop import autonomous_compilation_loop
from optimizer.benchmark import run_benchmark

def get_ast(filepath):
    with open(filepath, 'r') as f:
        tree = ast.parse(f.read())
        return ast.dump(tree, indent=4)

def run_pipeline(python_file, model_choice):
    print(f"\n Starting Pipeline for {python_file} using [{model_choice.upper()}]...")
    
    ast_data = get_ast(python_file)
    os.makedirs("generated", exist_ok=True)
    cpp_output_path = "generated/output.cpp"
    exe_output_path = "generated/program"
    
    # Trigger the autonomous feedback loop
    success = autonomous_compilation_loop(ast_data, cpp_output_path, exe_output_path, model_choice)

    # If it survived the loop, run the benchmark
    if success:
        print("\n Running Benchmarks...")
        run_benchmark(f"./{exe_output_path}", python_file)
    else:
        print("\n Pipeline failed to produce valid C++ code. Check generated/output.cpp to debug.")

if __name__ == "__main__":
    print("   AI-Powered Python to C++ Transpiler Engine")
    
    # 1. Ask for the file path
    default_file = "examples/matrix_mult.py"
    user_file = input(f"\nEnter the path to the Python file [Press Enter for '{default_file}']: ").strip()
    target_file = user_file if user_file else default_file

    # 2. Interactive Model Menu
    print("\nAvailable LLM Backends:")
    print("  1. Gemini 2.5 Flash (Default)")
    print("  2. Groq (Llama-3.3-70b - Ultra Fast)")
    print("  3. Cohere (Command-R)")
    
    choice = input("\nSelect a model by number (1/2/3): ").strip()
    
    # 3. Route the choice
    if choice == '2':
        selected_model = "groq"
    elif choice == '3':
        selected_model = "cohere"
    else:
        selected_model = "gemini"
        
    # Run the engine
    run_pipeline(target_file, selected_model)
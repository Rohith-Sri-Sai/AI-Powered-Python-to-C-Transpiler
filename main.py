import os
import ast
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# Suppress PyTorch/TensorFlow warnings
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

from optimizer.feedback_loop import autonomous_compilation_loop
from optimizer.benchmark import run_benchmark

def get_ast(filepath):
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        tree = ast.parse(f.read())
        return ast.dump(tree, indent=4)

def run_pipeline(python_file, model_choice, *, function_cases=None, warmups=2, repetitions=10):
    """Generate, validate, then benchmark; never time a rejected candidate."""
    python_file = Path(python_file).resolve()
    print(f"\n Starting Pipeline for {python_file} using [{model_choice.upper()}]...")
    ast_data = get_ast(python_file)
    generated = Path("generated").resolve()
    generated.mkdir(parents=True, exist_ok=True)
    cpp_output_path = generated / "output.cpp"
    exe_output_path = generated / ("program.exe" if os.name == "nt" else "program")
    success = autonomous_compilation_loop(
        ast_data, cpp_output_path, exe_output_path, model_choice,
        python_file_path=python_file, function_cases=function_cases,
    )
    if success:
        print("\n Running Benchmarks...")
        return run_benchmark(exe_output_path, python_file, warmups=warmups, repetitions=repetitions)
    print("\n Pipeline failed validation. Check generated/output.cpp and the feedback above.")
    return 0.0

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
import subprocess
import os

def compile_and_test(cpp_file_path, output_exe_path):
    """Compiles the generated C++ code using g++."""
    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_exe_path), exist_ok=True)
    
    # Command to compile with O3 optimization
    compile_cmd = ["g++", "-O3", cpp_file_path, "-o", output_exe_path]
    
    # Run the command and capture output directly
    process = subprocess.run(compile_cmd, capture_output=True, text=True)
    
    if process.returncode != 0:
        # Return False and the exact compiler error message
        return False, process.stderr
        
    return True, "Compilation successful."
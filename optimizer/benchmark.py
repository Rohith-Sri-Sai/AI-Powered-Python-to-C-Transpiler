import time
import subprocess
import csv
import os

def run_benchmark(executable_path, python_file_path):
    print(f"   -> Benchmarking original Python script ({python_file_path})...")
    
    # 1. Benchmark Python
    py_start = time.time()
    try:
        py_process = subprocess.run(["python", python_file_path], capture_output=True, text=True, timeout=10)
        py_time = time.time() - py_start
        py_status = "Success" if py_process.returncode == 0 else "Error"
    except subprocess.TimeoutExpired:
        py_time = 10.0
        py_status = "Timeout"

    print(f"   -> Benchmarking generated C++ executable ({executable_path})...")
    
    # 2. Benchmark C++
    cpp_start = time.time()
    try:
        cpp_process = subprocess.run([executable_path], capture_output=True, text=True, timeout=10)
        cpp_time = time.time() - cpp_start
        cpp_status = "Success" if cpp_process.returncode == 0 else "Error"
    except subprocess.TimeoutExpired:
        cpp_time = 10.0
        cpp_status = "Timeout"

    # 3. Calculate Speedup Multiplier
    if py_status == "Success" and cpp_status == "Success" and cpp_time > 0:
        speedup = py_time / cpp_time
        print(f"\n RESULTS: C++ output is {speedup:.2f}x faster than Python!")
        print(f"   Python Time: {py_time:.6f}s")
        print(f"   C++ Time:    {cpp_time:.6f}s")
    else:
        speedup = 0.0
        print(f"\n Could not calculate speedup. Py: {py_status}, C++: {cpp_status}")

    # 4. Save results to CSV
    os.makedirs("results", exist_ok=True)
    csv_file = "results/benchmarks.csv"
    file_exists = os.path.isfile(csv_file)
    
    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        # Write headers if it's a new file
        if not file_exists:
            writer.writerow(["Algorithm", "Python Time (s)", "C++ Time (s)", "Speedup", "Status"])
        
        algo_name = os.path.basename(python_file_path)
        writer.writerow([algo_name, f"{py_time:.6f}", f"{cpp_time:.6f}", f"{speedup:.2f}x", f"Py:{py_status}|C++:{cpp_status}"])
        
    return speedup
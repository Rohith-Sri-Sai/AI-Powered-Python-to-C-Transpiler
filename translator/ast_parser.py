import ast

def extract_ast(source_code):
    """Parses Python source code and returns a formatted AST string."""
    try:
        tree = ast.parse(source_code)
        # Using indent=4 makes it readable for both user and the LLM
        return ast.dump(tree, indent=4)
    except SyntaxError as e:
        return f"Syntax Error in source code: {e}"

# Sample code
sample_python_code = """
def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)
"""

python_ast = extract_ast(sample_python_code)
print(" Extracted Python AST")
print(python_ast)
"""Generation-contract tests inject a model; no external API is called."""
from types import SimpleNamespace


def test_repair_prompt_contains_previous_candidate_and_numeric_contract(monkeypatch):
    from translator import cpp_generator

    seen = []

    class Model:
        def invoke(self, prompt):
            seen.append(prompt)
            return SimpleNamespace(content='```cpp\nint main(){return 0;}\n```')

    monkeypatch.setattr(cpp_generator, "get_llm", lambda choice: Model())
    code = cpp_generator.generate_cpp(
        'Module(body=[])', 'Expected 9; got -1', 'groq',
        previous_cpp='int main(){return -1;}',
    )
    assert code == 'int main(){return 0;}'
    assert 'int main(){return -1;}' in seen[0]
    assert 'Expected 9; got -1' in seen[0]
    assert 'int64_t' in seen[0] and 'cpp_int' in seen[0]
    assert 'function names' in seen[0]

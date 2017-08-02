import os.path


def test_readme():
    readme_path = os.path.join(
        os.path.dirname(__file__),
        '../README.rst',
    )
    with open(readme_path, encoding='utf-8') as f:
        lines = f.readlines()

    codes = []

    code = []
    for line in lines:
        if not code and line.startswith('.. code:: python'):
            code.append('')
        elif code and (line.startswith('    ') or line == '\n'):
            code.append(line[4:])
        elif code:
            assert any(code)
            codes.append(''.join(code))
            code.clear()

    def calculate_result(x):
        return x * 2

    for code in codes:
        exec(code)

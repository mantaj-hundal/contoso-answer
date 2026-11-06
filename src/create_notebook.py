"""Execute the readable notebook and export matching full/preparation scripts."""
from pathlib import Path
import os

import nbformat
from nbclient import NotebookClient

case_folder = Path(__file__).resolve().parent.parent
notebook = nbformat.read(case_folder / 'notebook_template.ipynb', as_version=4)
kernel_name = os.environ.get('CONTOSO_KERNEL', 'python3')

if __name__ == '__main__':
    client = NotebookClient(
        notebook,
        timeout=120,
        kernel_name=kernel_name,
        resources={'metadata': {'path': str(case_folder)}},
    )
    try:
        client.execute()
    except Exception:
        nbformat.write(notebook, case_folder / 'outputs/readability/failed-execution.ipynb')
        raise
    nbformat.validate(notebook)
    code_cells = [cell for cell in notebook.cells if cell.cell_type == 'code']
    assert all(cell.execution_count is not None for cell in code_cells)
    assert not any(output.output_type == 'error' for cell in code_cells for output in cell.outputs)
    nbformat.write(notebook, case_folder / 'analysis.ipynb')

    stages = {
        'analysis.py': code_cells,
        'prepare_data.py': [cell for cell in code_cells if cell.metadata.get('stage') == 'preparation'],
    }
    for filename, cells in stages.items():
        source = '# Generated from analysis.ipynb. Implementation functions are in case_helpers/.\n\n'
        source += '\n\n'.join('# %%\n' + cell.source for cell in cells)
        (case_folder / filename).write_text(source + '\n', encoding='utf-8')
    print(f'Saved readable notebook: {len(code_cells)} executed code cells, no cell errors.')

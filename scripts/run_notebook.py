"""Run a notebook from start to finish without opening it, the same way Colab's "Run all" does.

Usage: python scripts/run_notebook.py work/cbb_model.ipynb [--fail-if-printed "some text" ...]

The notebook runs inside its own folder, so the files it saves land next to it.
Everything the notebook prints is copied to the log. If a cell fails, the error is
printed and the script exits with code 1 so the GitHub job is marked as failed.
--fail-if-printed also marks the run as failed when the notebook printed that text
(used to catch a data refresh that failed while the notebook carried on with old data).
"""
import argparse
import os
import sys
import time

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

TIMEOUT_SECONDS = 50 * 60


def printed_output(nb):
    parts = []
    for cell in nb.cells:
        if cell.cell_type != "code":
            continue
        for out in cell.get("outputs", []):
            if out.get("output_type") == "stream":
                parts.append(out.get("text", ""))
            elif out.get("output_type") == "error":
                parts.append("\n".join(out.get("traceback", [])) + "\n")
    return "".join(parts)


def main(path, fail_texts):
    path = os.path.abspath(path)
    folder = os.path.dirname(path)
    nb = nbformat.read(path, as_version=4)
    client = NotebookClient(nb, timeout=TIMEOUT_SECONDS, kernel_name="python3",
                            resources={"metadata": {"path": folder}})
    started = time.time()
    print(f"Running {os.path.basename(path)} in {folder}", flush=True)
    try:
        client.execute()
        ok = True
    except CellExecutionError as e:
        ok = False
        print(f"\nA cell failed:\n{e}", flush=True)
    text = printed_output(nb)
    sys.stdout.write(text)
    for bad in fail_texts:
        if bad in text:
            ok = False
            print(f"\nThe notebook printed \"{bad}\", so this run counts as failed.", flush=True)
    nbformat.write(nb, path.replace(".ipynb", "_run.ipynb"))
    print(f"\nFinished in {time.time() - started:.0f}s: {'OK' if ok else 'FAILED'}", flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("notebook")
    parser.add_argument("--fail-if-printed", action="append", default=[])
    args = parser.parse_args()
    sys.exit(main(args.notebook, args.fail_if_printed))

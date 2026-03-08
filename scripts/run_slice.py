"""Helper: load a slice by ID from a saved plan and execute it via slicer.py."""
import json, pathlib, subprocess, sys

SLICER  = str(pathlib.Path(__file__).parent.parent / "devteam-workflow/skills/task-slicer/scripts/slicer.py")
ROOT    = str(pathlib.Path(__file__).parent.parent)

def run(plan_file: str, slice_id: str) -> tuple[str, str, int]:
    plan = json.loads(pathlib.Path(plan_file).read_text())["plan"]
    slices = {s["id"]: s for s in plan["slices"]}
    if slice_id not in slices:
        print(f"Unknown slice: {slice_id}. Available: {list(slices)}", file=sys.stderr)
        sys.exit(1)
    r = subprocess.run(
        ["python", SLICER, json.dumps(slices[slice_id]), ROOT],
        capture_output=True, text=True, timeout=400,
    )
    return r.stdout, r.stderr, r.returncode

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: run_slice.py <plan_json> <slice_id>")
        sys.exit(1)
    out, err, rc = run(sys.argv[1], sys.argv[2])
    print(out)
    if err.strip():
        print("STDERR:", err, file=sys.stderr)
    sys.exit(rc)

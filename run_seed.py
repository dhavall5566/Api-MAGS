import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WINDOW_DIR = ROOT.parent / "MAGS-Window-"


def export_mock_data() -> None:
    script = WINDOW_DIR / "scripts" / "export-seed-data.ts"
    if not script.exists():
        raise FileNotFoundError(f"Export script not found: {script}")

    print("Exporting mock data from MAGS-Window-...")
    subprocess.run(
        ["npx", "tsx", str(script)],
        cwd=str(WINDOW_DIR),
        check=True,
    )


def main() -> None:
    if "--skip-export" not in sys.argv:
        export_mock_data()

    sys.path.insert(0, str(ROOT))
    from seed.seed import run_seed

    run_seed()


if __name__ == "__main__":
    main()

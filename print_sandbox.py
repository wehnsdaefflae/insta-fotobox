# coding=utf-8

import subprocess
from pathlib import Path


def print_text(filepath: Path):
    completed_process: subprocess.CompletedProcess = subprocess.run(["lp", filepath.as_posix()], capture_output=True)
    print(f"out: {completed_process.stdout:s}")
    print(f"err: {completed_process.stderr:s}")
    print(f"returncode: {completed_process.returncode:d}")


def main():
    print_text(Path("/home/pi/WhatsApp Image 2022-06-04 at 21.40.41.jpeg"))


if __name__ == "__main__":
    main()

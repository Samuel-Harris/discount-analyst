import argparse
import os
import re
import shutil
from pathlib import Path
from typing import Optional, TextIO, List, Tuple


def sanitize_filename(name: str) -> str:
    """
    Sanitize a string to be safe for use as a filename.
    Converts to lowercase, replaces non-alphanumeric chars with underscores,
    and handles multiple underscores.
    """
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9\-]", "_", name)
    name = re.sub(r"_+", "_", name)
    name = name.strip("_")
    return name or "untitled"


def write_index(directory: Path, title: str, children: List[Tuple[str, str]]) -> None:
    """
    Writes an index.md file in the given directory with a table of contents.
    """
    if not children:
        return

    index_path = directory / "index.md"
    print(f"Generating Index: {index_path}")
    with open(index_path, "w", encoding="utf-8") as f:
        for name, link_title in children:
            f.write(f"- [{link_title}]({name})\n")


def parse_markdown(*, input_file: str, output_dir: str) -> None:
    """
    Parses a markdown file and splits it into directories and files.
    - H1 (#) -> New Directory
    - H2 (##) or H3 (###) -> New File within current Directory
    - Intro text -> introduction.md
    - TOC -> index.md
    """
    input_path = Path(input_file)
    output_path = Path(output_dir)

    if not input_path.exists():
        print(f"Error: Input file '{input_file}' not found.")
        return

    # Clean output directory if it exists
    if output_path.exists():
        shutil.rmtree(output_path)
        print(f"Removed existing output directory: {output_dir}")

    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)

    current_dir = output_path
    current_file: Optional[TextIO] = None

    # State tracking
    # root_children: List of (dirname/index.md, title) for the root index
    root_children: List[Tuple[str, str]] = []

    # current_dir_children: List of (filename, title) for the current H1 directory index
    current_dir_children: List[Tuple[str, str]] = []

    # Track current H1 title to use for index generation later
    current_h1_title = ""

    def close_current_file():
        nonlocal current_file
        if current_file:
            current_file.close()
            current_file = None

    def get_file(filename: str):
        nonlocal current_file
        close_current_file()
        f_path = current_dir / filename
        print(f"Created File: {f_path}")
        current_file = open(f_path, "w", encoding="utf-8")
        return current_file

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            for line in f:
                # check for H1
                if line.startswith("# "):
                    title = line[2:].strip()
                    dirname = sanitize_filename(title)

                    # If we were in a directory, write its index before moving on
                    if current_dir != output_path:
                        write_index(current_dir, current_h1_title, current_dir_children)

                    # Reset for new directory
                    current_h1_title = title
                    current_dir_children = []

                    # Create new directory
                    current_dir = output_path / dirname
                    current_dir.mkdir(exist_ok=True)

                    # Add this directory to root index
                    # We link to the directory, implied index.md
                    root_children.append((f"{dirname}/index.md", title))

                    close_current_file()

                # Check for H2 or H3
                elif line.startswith("## ") or line.startswith("### "):
                    # Determine prefix length (3 for ##, 4 for ###)
                    prefix_len = 3 if line.startswith("## ") else 4
                    title = line[prefix_len:].strip()
                    filename = sanitize_filename(title) + ".md"

                    get_file(filename)
                    current_file.write(line)

                    # Add to current directory index
                    # Note: We rely on the order of parsing, which matches original order
                    current_dir_children.append((filename, title))

                else:
                    # Content line
                    if not current_file:
                        if line.strip():  # Only open if there is actual content
                            # If we are in the output_path (root) and haven't seen H1,
                            # we could put it in introduction.md in root?
                            # Or if we are in an H1 dir, it's introduction.md

                            filename = "introduction.md"
                            get_file(filename)

                            # Add to index if not already there
                            if (filename, "Introduction") not in current_dir_children:
                                # Insert at beginning if possible, or append?
                                # Usually intro is first.
                                current_dir_children.insert(
                                    0, (filename, "Introduction")
                                )

                    if current_file:
                        current_file.write(line)

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback

        traceback.print_exc()
    finally:
        close_current_file()

    # Write index for the last directory
    if current_dir != output_path:
        write_index(current_dir, current_h1_title, current_dir_children)

    # Write root index
    # Filter out empty children if any?
    if root_children:
        write_index(output_path, "Root", root_children)

    # Post-processing cleanup: Remove empty files and directories
    print("Cleaning up empty artifacts...")
    for root, dirs, files in os.walk(output_dir, topdown=False):
        for name in files:
            p = Path(root) / name
            if p.stat().st_size == 0:
                p.unlink()
                print(f"Removed empty file: {p}")

        for name in dirs:
            p = Path(root) / name
            try:
                p.rmdir()
                print(f"Removed empty directory: {p}")
            except OSError:
                pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Split a markdown file into a directory structure."
    )
    parser.add_argument("input_file", help="Path to the input markdown file")
    parser.add_argument("output_dir", help="Path to the output directory")

    args = parser.parse_args()
    # Use keyword args explicitly
    parse_markdown(input_file=args.input_file, output_dir=args.output_dir)

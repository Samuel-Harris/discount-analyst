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


class MarkdownParser:
    """Parses a markdown file and splits it into directories and files."""

    def __init__(self, *, input_file: str, output_dir: str) -> None:
        self.input_path = Path(input_file)
        self.output_path = Path(output_dir)

        # State variables (previously nonlocal)
        self.current_dir: Path = self.output_path
        self.current_file: Optional[TextIO] = None
        self.root_children: List[Tuple[str, str]] = []
        self.current_dir_children: List[Tuple[str, str]] = []
        self.current_h1_title = ""

    def close_current_file(self) -> None:
        """Close the currently open file if any."""
        if self.current_file:
            self.current_file.close()
            self.current_file = None

    def get_file(self, filename: str) -> TextIO:
        """Close current file and open a new one."""
        self.close_current_file()
        f_path = self.current_dir / filename
        print(f"Created File: {f_path}")
        self.current_file = open(f_path, "w", encoding="utf-8")
        return self.current_file

    def parse(self) -> None:
        """
        Parses a markdown file and splits it into directories and files.
        - H1 (#) -> New Directory
        - H2 (##) or H3 (###) -> New File within current Directory
        - Intro text -> introduction.md
        - TOC -> index.md
        """
        if not self.input_path.exists():
            print(f"Error: Input file '{self.input_path}' not found.")
            return

        # Clean output directory if it exists
        if self.output_path.exists():
            shutil.rmtree(self.output_path)
            print(f"Removed existing output directory: {self.output_path}")

        # Create output directory
        self.output_path.mkdir(parents=True, exist_ok=True)

        # Initialize state
        self.current_dir = self.output_path

        try:
            with open(self.input_path, "r", encoding="utf-8") as f:
                for line in f:
                    # check for H1
                    if line.startswith("# "):
                        title = line[2:].strip()
                        dirname = sanitize_filename(title)

                        # If we were in a directory, write its index before moving on
                        if self.current_dir != self.output_path:
                            write_index(
                                self.current_dir,
                                self.current_h1_title,
                                self.current_dir_children,
                            )

                        # Reset for new directory
                        self.current_h1_title = title
                        self.current_dir_children = []

                        # Create new directory
                        self.current_dir = self.output_path / dirname
                        self.current_dir.mkdir(exist_ok=True)

                        # Add this directory to root index
                        # We link to the directory, implied index.md
                        self.root_children.append((f"{dirname}/index.md", title))

                        self.close_current_file()

                    # Check for H2 or H3
                    elif line.startswith("## ") or line.startswith("### "):
                        # Determine prefix length (3 for ##, 4 for ###)
                        prefix_len = 3 if line.startswith("## ") else 4
                        title = line[prefix_len:].strip()
                        filename = sanitize_filename(title) + ".md"

                        file_obj = self.get_file(filename)
                        file_obj.write(line)

                        # Add to current directory index
                        # Note: We rely on the order of parsing, which matches original order
                        self.current_dir_children.append((filename, title))

                    else:
                        # Content line
                        if not self.current_file:
                            if line.strip():  # Only open if there is actual content
                                # If we are in the output_path (root) and haven't seen H1,
                                # we could put it in introduction.md in root?
                                # Or if we are in an H1 dir, it's introduction.md

                                filename = "introduction.md"
                                self.get_file(filename)

                                # Add to index if not already there
                                if (
                                    filename,
                                    "Introduction",
                                ) not in self.current_dir_children:
                                    # Insert at beginning if possible, or append?
                                    # Usually intro is first.
                                    self.current_dir_children.insert(
                                        0, (filename, "Introduction")
                                    )

                        if self.current_file:
                            self.current_file.write(line)

        except Exception as e:
            print(f"An error occurred: {e}")
            import traceback

            traceback.print_exc()
        finally:
            self.close_current_file()

        # Write index for the last directory
        if self.current_dir != self.output_path:
            write_index(
                self.current_dir, self.current_h1_title, self.current_dir_children
            )

        # Write root index
        # Filter out empty children if any?
        if self.root_children:
            write_index(self.output_path, "Root", self.root_children)

        # Post-processing cleanup: Remove empty files and directories
        print("Cleaning up empty artifacts...")
        for root, dirs, files in os.walk(self.output_path, topdown=False):
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


def parse_markdown(*, input_file: str, output_dir: str) -> None:
    """Parse a markdown file using the MarkdownParser class."""
    parser = MarkdownParser(input_file=input_file, output_dir=output_dir)
    parser.parse()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Split a markdown file into a directory structure."
    )
    parser.add_argument("input_file", help="Path to the input markdown file")
    parser.add_argument("output_dir", help="Path to the output directory")

    args = parser.parse_args()
    # Use keyword args explicitly
    parse_markdown(input_file=args.input_file, output_dir=args.output_dir)

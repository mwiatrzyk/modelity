#!/bin/env python

import argparse
import io
import os

from typing import TextIO


def remove_extension(path: str) -> str:
    index = path.rfind(".")
    if index < 0:
        return path
    return path[:index]


def replace_extension(path: str, new_ext: str) -> str:
    return remove_extension(path) + new_ext


def write_file(path: str, content: str):
    dirname = os.path.dirname(path)
    os.makedirs(dirname, exist_ok=True)
    with open(path, "w") as fd:
        fd.write(content)


def write_module_doc(out_path: str, module_name: str):
    buf = io.StringIO()
    buf.write(f"{module_name}\n")
    buf.write("-" * len(module_name) + "\n\n")
    buf.write(f".. automodule:: {module_name}\n")
    for opt in (":members:", ":undoc-members:", ":show-inheritance:", ":special-members: __call__, __loc__"):
        buf.write(f"  {opt}\n")
    write_file(out_path, buf.getvalue())


def extract_root_pkg_name_from_path(path: str) -> str:
    return os.path.basename(path.rstrip(os.path.sep))


def walk(src: str, dest: str, pkg_name: str, index_file: TextIO):
    for name in sorted(os.listdir(src)):
        if name.startswith("_"):
            continue
        full_src = os.path.join(src, name)
        if os.path.isdir(full_src):
            return walk(full_src, os.path.join(dest, name), f"{pkg_name}.{name}", index_file)
        full_dest = os.path.join(dest, replace_extension(name, ".rst"))
        full_module_name = f"{pkg_name}.{remove_extension(name)}"
        full_module_path = full_module_name.replace(".", os.path.sep)
        index_file.write(f"  {full_module_path}\n")
        write_module_doc(full_dest, full_module_name)


def begin_index_file(title: str) -> io.StringIO:
    buf = io.StringIO()
    buf.write(f"{title}\n")
    buf.write("=" * len(title) + "\n\n")
    buf.write(".. toctree::\n")
    buf.write("  :maxdepth: 2\n\n")
    return buf


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("src", help="Path to the package root directory")
    parser.add_argument("dest", help="Destination directory where Sphinx API docs will be created")
    parser.add_argument(
        "--title", type=str, help="Set the title for the index document [default: %(default)s]", default="API Reference"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    root_pkg_name = extract_root_pkg_name_from_path(args.src)
    index_file = begin_index_file(args.title)
    walk(args.src, os.path.join(args.dest, root_pkg_name), root_pkg_name, index_file)
    write_file(os.path.join(args.dest, "index.rst"), index_file.getvalue())


if __name__ == "__main__":
    main()

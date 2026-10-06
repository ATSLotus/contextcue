from __future__ import annotations

from pathlib import Path

from contextcue.scanner import (
    OUTPUT_FILENAME,
    is_supported_text_file,
)


SEPARATOR = "=" * 80


def read_text_file(path: Path) -> str:
    """
    尝试读取文本文件。

    优先 UTF-8，然后尝试 UTF-8 BOM。
    最后使用 errors=replace，避免整个程序因为编码问题退出。
    """

    encodings = [
        "utf-8",
        "utf-8-sig",
    ]

    for encoding in encodings:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
        except (PermissionError, OSError) as exc:
            return f"[读取文件失败: {exc}]"

    try:
        return path.read_text(
            encoding="utf-8",
            errors="replace",
        )
    except (PermissionError, OSError) as exc:
        return f"[读取文件失败: {exc}]"


def export_context(
    root: Path,
    selected_files: set[Path],
) -> Path:
    """
    将选择的文件导出到 contextcue.txt。
    """

    root = root.resolve()

    output_path = root / OUTPUT_FILENAME

    files = sorted(
        {
            path.resolve()
            for path in selected_files
            if path.is_file()
            and path.resolve() != output_path.resolve()
        },
        key=lambda p: str(p).lower(),
    )

    with output_path.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as fp:

        fp.write(f"ROOT: {root}\n\n")

        fp.write(SEPARATOR)
        fp.write("\nSELECTED FILES\n")
        fp.write(SEPARATOR)
        fp.write("\n\n")

        if not files:
            fp.write("[没有选择文件]\n")
        else:
            for path in files:
                fp.write(f"{path}\n")

        fp.write("\n\n")

        supported_files = [
            path
            for path in files
            if is_supported_text_file(path)
        ]

        fp.write(SEPARATOR)
        fp.write("\nFILE CONTENTS\n")
        fp.write(SEPARATOR)
        fp.write("\n\n")

        if not supported_files:
            fp.write("[没有支持读取正文的文件]\n")
        else:
            for path in supported_files:
                content = read_text_file(path)

                fp.write(SEPARATOR)
                fp.write("\n")
                fp.write(f"FILE: {path}\n")
                fp.write(SEPARATOR)
                fp.write("\n\n")

                fp.write(content)

                if not content.endswith("\n"):
                    fp.write("\n")

                fp.write("\n")

    return output_path
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


OUTPUT_FILENAME = "contextcue.txt"


SUPPORTED_EXTENSIONS = {
    ".vue",
    ".html",
    ".ts",
    ".js",
    ".css",
    ".sass",
    ".java",
    ".xml",
    ".yml",
    ".yaml",
    ".json",
    ".md",
    ".R",
    ".py"
}


DEFAULT_IGNORE_DIRS = {
    ".git",
    ".idea",
    ".vscode",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "target",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}


@dataclass
class FileNode:
    path: Path
    is_dir: bool
    children: list["FileNode"] = field(default_factory=list)

    @property
    def name(self) -> str:
        return self.path.name


def should_ignore(path: Path) -> bool:
    """
    判断目录/文件是否需要忽略。
    """

    if path.name == OUTPUT_FILENAME:
        return True

    if path.is_dir() and path.name in DEFAULT_IGNORE_DIRS:
        return True

    return False


def scan_directory(root: Path) -> FileNode:
    """
    深度扫描指定目录。

    返回整个目录树。
    """

    root = root.resolve()

    root_node = FileNode(
        path=root,
        is_dir=True,
    )

    _scan_children(root_node)

    return root_node


def _scan_children(node: FileNode) -> None:
    """
    递归扫描目录。
    """

    if not node.is_dir:
        return

    try:
        items = list(node.path.iterdir())
    except (PermissionError, OSError):
        return

    # 文件夹优先，然后按照名称排序
    items.sort(
        key=lambda p: (
            not p.is_dir(),
            p.name.lower(),
        )
    )

    for path in items:
        try:
            if should_ignore(path):
                continue

            # 不跟随符号链接目录，防止循环
            if path.is_symlink():
                child = FileNode(
                    path=path,
                    is_dir=False,
                )
                node.children.append(child)
                continue

            child = FileNode(
                path=path,
                is_dir=path.is_dir(),
            )

            node.children.append(child)

            if child.is_dir:
                _scan_children(child)

        except (PermissionError, OSError):
            continue


def collect_all_paths(node: FileNode) -> set[Path]:
    """
    获取节点及其全部后代路径。
    """

    result: set[Path] = {node.path}

    for child in node.children:
        result.update(collect_all_paths(child))

    return result


def collect_files(node: FileNode) -> list[Path]:
    """
    获取节点下全部文件。
    """

    result: list[Path] = []

    if not node.is_dir:
        return [node.path]

    for child in node.children:
        if child.is_dir:
            result.extend(collect_files(child))
        else:
            result.append(child.path)

    return result


def is_supported_text_file(path: Path) -> bool:
    """
    判断文件是否属于支持读取正文的类型。
    """

    return (
        path.is_file()
        and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )
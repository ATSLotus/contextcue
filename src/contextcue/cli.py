from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Footer, Header, Static, Tree
from textual.widgets.tree import TreeNode

from contextcue.exporter import export_context
from contextcue.scanner import (
    FileNode,
    collect_files,
    scan_directory,
)


class ContextCueApp(App):
    """
    ContextCue 文件选择器。
    """

    TITLE = "ContextCue"

    SUB_TITLE = "Project Context Exporter"

    CSS = """
    Screen {
        layout: vertical;
    }

    #current-path {
        height: 3;
        padding: 1 2;
    }

    #status {
        height: 3;
        padding: 1 2;
    }

    #tree {
        height: 1fr;
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding(
            "space",
            "toggle_select",
            "选择/取消",
            show=True,
            priority=True,
        ),
        Binding(
            "a",
            "select_all",
            "全选",
            show=True,
        ),
        Binding(
            "n",
            "clear_selection",
            "清空",
            show=True,
        ),
        Binding(
            "e",
            "export",
            "导出",
            show=True,
        ),
        Binding(
            "q",
            "quit",
            "退出",
            show=True,
        ),
    ]
    
    def __init__(self) -> None:
        super().__init__()

        # 非常重要：
        # 使用命令执行时的当前目录
        self.root_path = Path.cwd().resolve()

        self.file_tree = scan_directory(
            self.root_path
        )

        # 保存真正选中的文件
        self.selected_files: set[Path] = set()

        # Path -> Textual TreeNode
        self.path_nodes: dict[
            Path,
            TreeNode
        ] = {}

    def compose(self) -> ComposeResult:
        yield Header()

        with Vertical():

            yield Static(
                f"当前目录: {self.root_path}",
                id="current-path",
            )

            tree = Tree(
                self.root_path.name or str(
                    self.root_path
                ),
                id="tree",
            )

            tree.root.data = self.file_tree

            self.path_nodes[
                self.file_tree.path
            ] = tree.root

            self._build_tree(
                tree.root,
                self.file_tree,
            )

            tree.root.expand()

            yield tree

            yield Static(
                "已选择 0 个文件",
                id="status",
            )

        yield Footer()

    def _build_tree(
        self,
        parent_tree_node: TreeNode,
        file_node: FileNode,
    ) -> None:
        """
        将 FileNode 转换成 Textual Tree。
        """

        for child in file_node.children:

            label = self._make_label(
                child,
                selected=False,
            )

            tree_node = parent_tree_node.add(
                label,
                data=child,
            )

            self.path_nodes[
                child.path
            ] = tree_node

            if child.is_dir:
                self._build_tree(
                    tree_node,
                    child,
                )

    def _make_label(
        self,
        node: FileNode,
        selected: bool,
    ) -> str:
        """
        生成节点显示文本。
        """

        mark = "[x]" if selected else "[ ]"

        icon = "📁" if node.is_dir else "📄"

        return (
            f"{mark} {icon} {node.name}"
        )

    def action_toggle_select(self) -> None:
        """
        Space:
        选择/取消当前节点。
        """

        tree = self.query_one(
            "#tree",
            Tree,
        )

        tree_node = tree.cursor_node

        if tree_node is None:
            return

        file_node = tree_node.data

        if not isinstance(
            file_node,
            FileNode,
        ):
            return

        if file_node.is_dir:
            files = set(
                collect_files(file_node)
            )
        else:
            files = {
                file_node.path
            }

        # 如果全部已经选择，则取消
        if (
            files
            and files.issubset(
                self.selected_files
            )
        ):
            self.selected_files.difference_update(
                files
            )

        else:
            self.selected_files.update(
                files
            )

        self._refresh_labels()
        self._update_status()

    def action_select_all(self) -> None:
        """
        全选。
        """

        self.selected_files = set(
            collect_files(
                self.file_tree
            )
        )

        self._refresh_labels()
        self._update_status()

    def action_clear_selection(self) -> None:
        """
        清空选择。
        """

        self.selected_files.clear()

        self._refresh_labels()
        self._update_status()

    def action_export(self) -> None:
        """
        导出 contextcue.txt。
        """

        if not self.selected_files:
            self.notify(
                "当前没有选择任何文件",
                severity="warning",
            )
            return

        try:
            output = export_context(
                self.root_path,
                self.selected_files,
            )

        except Exception as exc:
            self.notify(
                f"导出失败: {exc}",
                severity="error",
            )
            return

        self.notify(
            f"导出成功: {output}",
            severity="information",
            timeout=5,
        )

    def _refresh_labels(self) -> None:
        """
        刷新整棵树的选择状态。
        """

        for path, tree_node in (
            self.path_nodes.items()
        ):

            file_node = tree_node.data

            if not isinstance(
                file_node,
                FileNode,
            ):
                continue

            if file_node.is_dir:

                files = set(
                    collect_files(
                        file_node
                    )
                )

                if (
                    files
                    and files.issubset(
                        self.selected_files
                    )
                ):
                    mark = "[x]"

                elif (
                    files
                    and files.intersection(
                        self.selected_files
                    )
                ):
                    mark = "[-]"

                else:
                    mark = "[ ]"

                icon = "📁"

                tree_node.set_label(
                    f"{mark} {icon} "
                    f"{file_node.name}"
                )

            else:

                selected = (
                    file_node.path
                    in self.selected_files
                )

                tree_node.set_label(
                    self._make_label(
                        file_node,
                        selected,
                    )
                )

    def _update_status(self) -> None:
        """
        更新底部选择数量。
        """

        status = self.query_one(
            "#status",
            Static,
        )

        total = len(
            self.selected_files
        )

        supported = sum(
            1
            for path
            in self.selected_files
            if path.suffix.lower()
            in {
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
            }
        )

        status.update(
            f"已选择 {total} 个文件 | "
            f"其中 {supported} 个文件将读取正文"
        )


def main() -> None:
    app = ContextCueApp()
    app.run()
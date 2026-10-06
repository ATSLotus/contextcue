#!/usr/bin/env bash

set -e

APP_NAME="contextcue"
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

DIST_DIR="$PROJECT_ROOT/dist"
BUILD_DIR="$PROJECT_ROOT/build"

# 用户本地命令目录
LOCAL_BIN="$HOME/.local/bin"

echo "========================================"
echo " ContextCue 本地发布"
echo "========================================"
echo
echo "项目目录: $PROJECT_ROOT"
echo "安装目录: $LOCAL_BIN"
echo

cd "$PROJECT_ROOT"

# --------------------------------------------------
# 1. 检查 uv
# --------------------------------------------------

if ! command -v uv >/dev/null 2>&1; then
    echo "错误: 未找到 uv"
    exit 1
fi

echo "[1/5] 同步依赖..."

uv sync


# --------------------------------------------------
# 2. 检查 PyInstaller
# --------------------------------------------------

echo
echo "[2/5] 检查 PyInstaller..."

if ! uv run pyinstaller --version >/dev/null 2>&1; then
    echo "未找到 PyInstaller，正在安装..."
    uv add --dev pyinstaller
fi


# --------------------------------------------------
# 3. 清理旧构建
# --------------------------------------------------

echo
echo "[3/5] 清理旧构建..."

rm -rf "$DIST_DIR"
rm -rf "$BUILD_DIR"
rm -f "$PROJECT_ROOT/$APP_NAME.spec"


# --------------------------------------------------
# 4. 打包
# --------------------------------------------------

echo
echo "[4/5] 正在构建 $APP_NAME.exe ..."

uv run pyinstaller \
    --onefile \
    --name "$APP_NAME" \
    --clean \
    "$PROJECT_ROOT/src/contextcue/__main__.py"


# --------------------------------------------------
# 5. 安装到本地 bin
# --------------------------------------------------

echo
echo "[5/5] 安装到 $LOCAL_BIN ..."

mkdir -p "$LOCAL_BIN"

if [ -f "$DIST_DIR/$APP_NAME.exe" ]; then

    cp "$DIST_DIR/$APP_NAME.exe" \
       "$LOCAL_BIN/$APP_NAME.exe"

    echo
    echo "========================================"
    echo " 发布成功"
    echo "========================================"
    echo
    echo "程序位置:"
    echo "  $LOCAL_BIN/$APP_NAME.exe"
    echo

else

    echo "错误: 未找到:"
    echo "$DIST_DIR/$APP_NAME.exe"
    exit 1

fi


# --------------------------------------------------
# PATH 检查
# --------------------------------------------------

case ":$PATH:" in

    *":$LOCAL_BIN:"*)
        echo "$LOCAL_BIN 已存在于 PATH"
        ;;

    *)
        echo "警告: $LOCAL_BIN 尚未加入 PATH"
        echo
        echo "请执行:"
        echo
        echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
        echo
        echo "并添加到 ~/.bashrc 或 ~/.zshrc"
        ;;

esac

echo
echo "现在可以尝试:"
echo
echo "  contextcue"
echo
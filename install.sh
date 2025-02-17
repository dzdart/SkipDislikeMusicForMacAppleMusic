#!/bin/bash
clear
# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_SCRIPT="$SCRIPT_DIR/SkipAppleMusic.py"

# 设定模板路径和生成的 plist 文件路径
TEMPLATE_PATH="$SCRIPT_DIR/com.user.AutoSkipMusic.template.plist"
PLIST_PATH="/Library/LaunchDaemons/com.user.AutoSkipMusic.plist"

# 需要 root 权限来写入 /Library/LaunchAgents/
# if [ "$(id -u)" -ne 0 ]; then
#     echo "错误: 需要 root 权限才能写入 $PLIST_PATH"
#     echo "请使用 sudo 重新运行此脚本"
#     exit 1
# fi

# 判断 Python 脚本是否存在，不存在则退出
if [ ! -f "$PY_SCRIPT" ]; then
    echo "错误: Python 脚本 $PY_SCRIPT 不存在！"
    exit 1
fi

# 判断 Plist 模板是否存在，不存在则退出
if [ ! -f "$TEMPLATE_PATH" ]; then
    echo "错误: Plist 模板文件 $TEMPLATE_PATH 不存在！"
    exit 1
fi

# 提示用户输入 Python 解释器路径
default_python=$(which python)
read -p "请输入 Python 路径 [$default_python]: " PYTHON_EXEC
PYTHON_EXEC=${PYTHON_EXEC:-$default_python}

# 检查 Python 解释器是否存在并可执行
if [ ! -x "$PYTHON_EXEC" ]; then
    echo "错误: 解释器 $PYTHON_EXEC 不存在或不可执行！"
    exit 1
fi

# 获取 Python 版本
PYTHON_VERSION=$("$PYTHON_EXEC" -c "import sys; print(sys.version_info.major)")

# 检查是否是 Python 3 及以上
if [ "$PYTHON_VERSION" -lt 3 ]; then
    echo "错误: 需要 Python 3.0 及以上版本，当前版本: $PYTHON_VERSION"
    exit 1
fi

# 提升权限
sudo bash <<EOF
echo "已切换到 root，当前用户: $(whoami)"

#移除plist服务
launchctl unload -w "$PLIST_PATH"
launchctl stop com.user.skipmusic
launchctl remove com.user.skipmusic

# 生成新的 plist 文件，并替换 PYTHON_PATH 和 PYSCRIPT_PATH
sed -e "s|PYTHON_PATH|$PYTHON_EXEC|g" -e "s|PYSCRIPT_PATH|$PY_SCRIPT|g" "$TEMPLATE_PATH" > "$PLIST_PATH"

echo "执行完成，退出 root"
EOF

HOME_DIR="$HOME"
SKIPMUSIC_DIR="$HOME_DIR/SkipMusic"


# 判断日志和关键字目录是否存在，不存在则创建
if [ ! -d "$SKIPMUSIC_DIR" ]; then
    echo "📂 目录 $SKIPMUSIC_DIR 不存在，正在创建..."
    mkdir -p "$SKIPMUSIC_DIR"
else
    echo "✅ 目录 $SKIPMUSIC_DIR 已存在"
fi

#创建关键字文件夹
keywords_path="$SKIPMUSIC_DIR/keywords.txt"
printf "你可以在本文件内创建关键字列表，每行一个。本行内容需要删除\n" > "$keywords_path"

# 确保 plist 文件的权限正确
chown root:wheel "$PLIST_PATH"
chmod 644 "$PLIST_PATH"

echo "✅ 已生成 Plist 文件: $PLIST_PATH"


# 加载 plist 文件
launchctl load -w "$PLIST_PATH"

# 启动服务
launchctl start com.user.AutoSkipMusic

echo "✅ AutoSkipMusic服务已启动"
echo "关键字路径：$SKIPMUSIC_DIR/keywords.txt"
echo "日志路径：$SKIPMUSIC_DIR/log.txt"
#!/bin/bash
set -e

echo "🔄 正在同步 docs/wiki/ 到 GitHub Wiki..."

# 清理旧的临时目录
rm -rf /tmp/eaagent-wiki

# 克隆 Wiki 仓库
git clone https://github.com/adoocoke/eaagent.wiki.git /tmp/eaagent-wiki

# 复制所有 Markdown 文件
cp docs/wiki/*.md /tmp/eaagent-wiki/

cd /tmp/eaagent-wiki

# 提交并推送
git add .
if git diff --cached --quiet; then
  echo "ℹ️ 没有内容变化，跳过提交"
else
  git commit -m "docs: sync wiki from main repo at $(date '+%Y-%m-%d %H:%M:%S')"
  git push
  echo "✅ Wiki 同步完成！"
fi
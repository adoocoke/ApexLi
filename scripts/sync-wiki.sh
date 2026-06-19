#!/bin/bash
set -e

echo "🔄 正在同步 docs/wiki/ 到 GitHub Wiki..."

WIKI_REPO="https://x-access-token:${GITHUB_TOKEN}@github.com/adoocoke/eaagent.wiki.git"

rm -rf /tmp/eaagent-wiki
git clone "$WIKI_REPO" /tmp/eaagent-wiki

cp docs/wiki/*.md /tmp/eaagent-wiki/

cd /tmp/eaagent-wiki

git config user.name "github-actions[bot]"
git config user.email "github-actions[bot]@users.noreply.github.com"

git add .
if git diff --cached --quiet; then
  echo "ℹ️ 没有内容变化，跳过提交"
else
  git commit -m "docs: sync wiki from main repo at $(date '+%Y-%m-%d %H:%M:%S')"
  git push
  echo "✅ Wiki 同步完成！"
fi
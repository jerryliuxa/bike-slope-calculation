# 一键推送到 GitHub(https://github.com/jerryliuxa/bike-slope-calculation)
# 用法:
#   bash push-github.sh              # SSH 方式(需先在 GitHub 添加下方公钥)
#   bash push-github.sh <你的Token>  # PAT 方式(在 GitHub Settings → Developer settings 生成)
cd "$(dirname "$0")" || exit 1

if [ -n "$1" ]; then
  echo "== 使用 Token 通过 HTTPS 推送 =="
  git remote set-url origin "https://jerryliuxa:$1@github.com/jerryliuxa/bike-slope-calculation.git"
  git push -u origin main && echo "✅ 推送成功(建议随后执行: git remote set-url origin https://github.com/jerryliuxa/bike-slope-calculation.git 移除 Token)"
else
  echo "== SSH 方式推送(443端口)=="
  echo "若尚未添加公钥,请先复制下面这行到 https://github.com/settings/keys → New SSH key:"
  cat ~/.ssh/id_ed25519_github.pub 2>/dev/null
  git push -u origin main && echo "✅ 推送成功: https://github.com/jerryliuxa/bike-slope-calculation"
fi

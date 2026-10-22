# pan — 夸克分享链接跳转层

个人夸克网盘分享链接的 GitHub Pages 跳转索引：每个分享 ID 一个页面
（`s/<ID>/`），打开后自动跳到对应的 `https://pan.quark.cn/s/<ID>`。

线上地址：https://sunjiali.github.io/pan/
点击统计：https://sunjiali.github.io/pan/stats.html

## 页面生成

所有页面由 `generate.py` 从链接清单统一生成，不要手改单个 HTML：

1. 在 `~/workspace/quark-promo/share-links.md` 里按格式加一行
   （`N. 名称 → https://pan.quark.cn/s/<ID>`）
2. 运行 `python3 generate.py`
3. commit + push，Pages 自动更新

## 点击统计

- 用 Abacus 免费计数 API（免注册），命名空间 `sunjiali-pan`，
  每条链接一个以分享 ID 命名的计数器，索引页用 `index-total`。
- 跳转页在跳转前用 `fetch(keepalive)` 发一次 hit（不阻塞跳转），
  meta refresh 1 秒仅作 JS 失效时的兜底。
- 计数器靠 hit 自动创建，所以新链接零配置即带统计；
  取值与排序在 `stats.html` 里完成（分批拉取，避免触发 API 限速）。
- 计数自 2026-10-22 上线之日起算，为近似值（第三方免费服务，
  无可用性保证）。计数器的 admin key 存在仓库外的
  `~/workspace/quark-promo/abacus-counters.json`，不要提交进仓库。

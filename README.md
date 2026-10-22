# pan — 夸克分享链接跳转层

个人夸克网盘分享链接的 GitHub Pages 跳转索引：每个分享 ID 一个页面
（`s/<ID>/`），打开后自动跳到对应的 `https://pan.quark.cn/s/<ID>`。

线上地址：https://sunjiali.github.io/pan/

## 新增一条

1. 复制任意一个 `s/<ID>/index.html` 到新目录 `s/<新ID>/index.html`
2. 把文件里的三处旧 ID 换成新 ID（meta refresh、JS、兜底链接）
3. 在根目录 `index.html` 的列表里加一行
4. commit + push，Pages 自动更新

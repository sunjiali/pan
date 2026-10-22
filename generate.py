#!/usr/bin/env python3
"""生成 pan 跳转站的全部页面（跳转页 + 索引页 + 统计页 + 404）。

数据源：~/workspace/quark-promo/share-links.md（格式：`N. 名称 → https://pan.quark.cn/s/<ID>`）
新增链接：在 share-links.md 里加一行，然后运行 `python3 generate.py`，再 commit + push。

点击统计：Abacus 免费计数 API（免注册），命名空间 sunjiali-pan，
每条链接一个以分享 ID 命名的计数器，索引页用 index-total。
跳转页在跳转前用 fetch(keepalive) 发一次 hit，不阻塞跳转；
meta refresh 设为 1 秒兜底（JS 正常时用 location.replace 立即跳，不等 meta）。
"""
import html
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = Path.home() / "workspace" / "quark-promo" / "share-links.md"
SITE = "https://sunjiali.github.io/pan"
QUARK = "https://pan.quark.cn/s/"
ABACUS = "https://abacus.jasoncameron.dev"
NAMESPACE = "sunjiali-pan"
STATS_SINCE = "2026-10-22"

STYLE = 'body{font-family:system-ui,-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;margin:2em;line-height:1.6;color:#222}a{color:#0b57d0}'


def parse_links():
    text = SOURCE.read_text(encoding="utf-8")
    links = []
    for m in re.finditer(r"^\d+\.\s*(.+?)\s*→\s*https://pan\.quark\.cn/s/([0-9a-f]{12})\s*$", text, re.M):
        links.append((m.group(1).strip(), m.group(2)))
    if not links:
        sys.exit("no links parsed from %s" % SOURCE)
    return links


def beacon_js(counter):
    """返回一段在页面上发一次 hit 的 JS（不阻塞后续动作）。"""
    return (
        '(function(){var u="%s/hit/%s/%s";'
        'try{if(window.fetch){fetch(u,{keepalive:true,mode:"no-cors"}).catch(function(){});}'
        'else{new Image().src=u;}}catch(e){try{new Image().src=u;}catch(_){}}})();'
        % (ABACUS, NAMESPACE, counter)
    )


def redirect_page(name, sid):
    target = QUARK + sid
    esc = html.escape(name)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc}</title>
<meta http-equiv="refresh" content="1; url={target}">
<script>
{beacon_js(sid)}
location.replace("{target}");
</script>
<style>{STYLE}</style>
</head>
<body>
<p>正在跳转到「{esc}」的夸克网盘分享页…</p>
<p>如果没有自动跳转，请点这里：<a href="{target}">{target}</a></p>
</body>
</html>
"""


def index_page(links, with_beacon=True, title="分享索引"):
    items = "\n".join(
        f'<li><a href="s/{sid}/">{html.escape(name)}</a> — <code>{SITE}/s/{sid}</code></li>'
        for name, sid in links
    )
    beacon = f"<script>\n{beacon_js('index-total')}\n</script>\n" if with_beacon else ""
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
{beacon}<style>body{{font-family:system-ui,-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;margin:2em;line-height:1.7;color:#222;max-width:56em}}a{{color:#0b57d0}}code{{background:#f2f2f2;padding:.1em .35em;border-radius:4px;font-size:.9em}}</style>
</head>
<body>
<h1>分享索引</h1>
<p>个人分享索引：以下链接会跳转到对应的夸克网盘分享页。</p>
<p><a href="stats.html">📊 查看点击统计</a></p>
<ol>
{items}
</ol>
</body>
</html>
"""


def stats_page(links):
    data = json.dumps(
        [{"name": name, "id": sid} for name, sid in links], ensure_ascii=False
    )
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>点击统计</title>
<style>body{{font-family:system-ui,-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;margin:2em;line-height:1.6;color:#222;max-width:64em}}a{{color:#0b57d0}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ddd;padding:.45em .6em;text-align:left;vertical-align:top}}th{{background:#f7f7f7}}td.n{{text-align:right;font-variant-numeric:tabular-nums}}code{{background:#f2f2f2;padding:.1em .35em;border-radius:4px;font-size:.85em;word-break:break-all}}.muted{{color:#666;font-size:.9em}}</style>
</head>
<body>
<h1>点击统计</h1>
<p class="muted">计数来自 Abacus 免费计数服务，自 {STATS_SINCE} 本功能上线之日起算；计数为近似值。取不到的条目显示「—」。<a href="index.html">← 返回索引</a></p>
<p id="summary">正在加载…</p>
<table>
<thead><tr><th>资源名</th><th>新链接</th><th>点击数</th><th>原链接</th></tr></thead>
<tbody id="rows"></tbody>
</table>
<script>
var ENTRIES = {data};
var API = "{ABACUS}/get/{NAMESPACE}/";
var SITE = "{SITE}/s/", QUARK = "{QUARK}";
var tbody = document.getElementById("rows");
var results = {{}};

function esc(s){{var d=document.createElement("div");d.textContent=s;return d.innerHTML;}}
function render(){{
  var sorted = ENTRIES.slice().sort(function(a,b){{
    var va = results[a.id], vb = results[b.id];
    if (va == null && vb == null) return 0;
    if (va == null) return 1;
    if (vb == null) return -1;
    return vb - va;
  }});
  var sum = 0, done = 0;
  tbody.innerHTML = sorted.map(function(e){{
    var v = results[e.id];
    if (typeof v === "number") {{ sum += v; done++; }}
    var shown = v === undefined ? "…" : (v === null ? "—" : String(v));
    return "<tr><td>" + esc(e.name) + "</td>" +
      '<td><a href="' + SITE + e.id + '/"><code>' + SITE + e.id + "</code></a></td>" +
      '<td class="n">' + shown + "</td>" +
      '<td><a href="' + QUARK + e.id + '"><code>' + QUARK + e.id + "</code></a></td></tr>";
  }}).join("");
  var idx = results["__index"];
  document.getElementById("summary").textContent =
    "已加载 " + done + " / " + ENTRIES.length + " 条，链接点击合计 " + sum + " 次" +
    (typeof idx === "number" ? "；索引页访问 " + idx + " 次。" : "。");
}}
function getOne(id, retry){{
  return fetch(API + encodeURIComponent(id)).then(function(r){{
    if (!r.ok) throw new Error(r.status);
    return r.json();
  }}).then(function(j){{
    results[id] = (typeof j.value === "number") ? j.value : null;
  }}).catch(function(){{
    if (!retry) return new Promise(function(res){{ setTimeout(res, 1200); }}).then(function(){{ return getOne(id, true); }});
    results[id] = null;
  }});
}}
function loadAll(){{
  var i = 0;
  function batch(){{
    var slice = ENTRIES.slice(i, i + 6); i += 6;
    if (!slice.length) {{ render(); return; }}
    Promise.all(slice.map(function(e){{ return getOne(e.id, false); }})).then(function(){{
      render();
      setTimeout(batch, 250);
    }});
  }}
  render(); batch();
  fetch(API + "index-total").then(function(r){{ return r.json(); }}).then(function(j){{
    if (typeof j.value === "number") {{ results["__index"] = j.value; render(); }}
  }}).catch(function(){{}});
}}
loadAll();
</script>
</body>
</html>
"""


def main():
    links = parse_links()
    for name, sid in links:
        d = HERE / "s" / sid
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(redirect_page(name, sid), encoding="utf-8")
    (HERE / "index.html").write_text(index_page(links), encoding="utf-8")
    (HERE / "404.html").write_text(
        index_page(links, with_beacon=False), encoding="utf-8"
    )
    (HERE / "stats.html").write_text(stats_page(links), encoding="utf-8")
    print("generated %d redirect pages + index + 404 + stats" % len(links))


if __name__ == "__main__":
    main()

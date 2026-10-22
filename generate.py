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


CATEGORIES = [
    ("ai", "🤖 AI 与编程"),
    ("money", "💰 搞钱与运营"),
    ("video", "🎬 影视与娱乐"),
    ("book", "📚 书籍与学习"),
    ("misc", "🧰 工具与合集"),
]
CAT_OF = {
    # AI 与编程
    "684716459942": "ai", "2d6064362cb6": "ai", "8e349455bf5e": "ai",
    "fff3ae440b4c": "ai", "79b32fb3837c": "ai", "ffdbd5b7e199": "ai",
    "36ed0c3b3bca": "ai", "cfa4cc181146": "ai", "5c19b5bc0b71": "ai",
    "aa2579dd4f48": "ai",
    # 搞钱与运营
    "fcbf1f0a10ca": "money", "4d01fbdd4857": "money", "6697d76abc2d": "money",
    "359fd9aae3ac": "money", "f124c534a9ff": "money", "9c07858604fd": "money",
    "da325c42742d": "money", "186c4b86e623": "money", "8e32cafa2e48": "money",
    "9eb71ee5f329": "money", "acd9043fcae0": "money", "af4690b5d4ef": "money",
    "b9c984c70f69": "money", "927ca16ad3f8": "money", "a3a12a9d1aa2": "money",
    "b4be8a777076": "money", "93f002d29517": "money",
    # 影视与娱乐
    "5984c9a429b4": "video", "442b55df5410": "video", "b785709a7caf": "video",
    "b2a7156b90fa": "video", "6272a0a53cd6": "video", "35857c4c76b2": "video",
    "f6bfcb365629": "video", "ac0166680f92": "video", "17e1286b6dfd": "video",
    "0112ae84217f": "video",
    # 书籍与学习
    "541436d3f73c": "book", "35ba85d668e5": "book", "68aa58075bfa": "book",
    "46ab4ed43e18": "book", "c23c1895b7a6": "book", "8c0df96cc99b": "book",
    "3c46a1623cbc": "book", "e7242c58ccd9": "book", "13dea72ee522": "book",
    "ad59011dabac": "book",
    # 工具与其他合集 → misc（默认）
}

INDEX_CSS = """
:root{--bg:#F5F1E8;--ink:#16171A;--card:#FFFEF8;--matcha:#A6CF5F;--acid:#D9F24F;--mut:#6B675C;--line:#16171A}
@media (prefers-color-scheme:dark){:root{--bg:#1C1B17;--ink:#EFE9DA;--card:#29271F;--mut:#A49E8E;--line:#EFE9DA}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:system-ui,-apple-system,"PingFang SC","Microsoft YaHei",sans-serif}
.wrap{max-width:880px;margin:0 auto;padding:28px 16px 56px}
header.top{display:flex;gap:16px;align-items:center;flex-wrap:wrap}
.logo{width:56px;height:56px;border:3px solid var(--line);border-radius:14px;background:var(--matcha);display:flex;align-items:center;justify-content:center;font-size:30px;box-shadow:4px 4px 0 var(--line)}
h1{font-size:26px;margin:0;font-weight:900;letter-spacing:.5px}
.sub{color:var(--mut);margin:4px 0 0;font-size:14px}
.toolbar{position:sticky;top:0;background:var(--bg);padding:14px 0 10px;z-index:5}
.search{width:100%;padding:12px 14px;font-size:16px;border:3px solid var(--line);border-radius:12px;background:var(--card);color:var(--ink);box-shadow:4px 4px 0 var(--line);outline:none}
.search:focus{box-shadow:4px 4px 0 var(--matcha)}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
.chip{border:2.5px solid var(--line);background:var(--card);color:var(--ink);border-radius:999px;padding:5px 13px;font-size:13.5px;cursor:pointer;font-weight:700}
.chip.on{background:var(--acid);color:#16171A}
h2.cat{font-size:18px;margin:26px 0 10px;display:flex;align-items:center;gap:8px}
h2.cat .n{font-size:12.5px;color:var(--mut);font-weight:600}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px}
.card{border:3px solid var(--line);border-radius:14px;background:var(--card);padding:13px 14px;box-shadow:4px 4px 0 var(--line);display:flex;flex-direction:column;gap:10px}
.card .name{font-weight:800;font-size:15.5px;line-height:1.45;word-break:break-word}
.card .row{display:flex;gap:8px;margin-top:auto}
.btn{flex:1;text-align:center;text-decoration:none;border:2.5px solid var(--line);border-radius:9px;padding:7px 0;font-size:13.5px;font-weight:800;color:#16171A;background:var(--matcha);cursor:pointer}
.btn.copy{flex:0 0 86px;background:var(--card);color:var(--ink)}
.btn:active{transform:translate(2px,2px)}
.empty{display:none;text-align:center;color:var(--mut);padding:34px 0;font-size:15px}
footer{margin-top:36px;color:var(--mut);font-size:13px;line-height:1.8}
footer a{color:var(--ink);font-weight:700}
#toast{position:fixed;left:50%;bottom:26px;transform:translateX(-50%) translateY(80px);background:var(--ink);color:var(--bg);padding:9px 20px;border-radius:999px;font-size:14px;font-weight:700;transition:transform .25s;z-index:9}
#toast.show{transform:translateX(-50%) translateY(0)}
"""


def index_page(links, with_beacon=True, title="资源索引 · Robin"):
    cat_names = dict(CATEGORIES)
    grouped = {k: [] for k, _ in CATEGORIES}
    for name, sid in links:
        grouped[CAT_OF.get(sid, "misc")].append((name, sid))
    chips = ['<button class="chip on" data-cat="all">全部 %d</button>' % len(links)]
    for key, label in CATEGORIES:
        if grouped[key]:
            chips.append(
                '<button class="chip" data-cat="%s">%s %d</button>'
                % (key, label, len(grouped[key]))
            )
    sections = []
    for key, label in CATEGORIES:
        group = grouped[key]
        if not group:
            continue
        cards = []
        for name, sid in group:
            esc = html.escape(name)
            short = f"{SITE}/s/{sid}"
            cards.append(
                f'<div class="card" data-name="{html.escape(name.lower())}">'
                f'<div class="name">{esc}</div>'
                f'<div class="row"><a class="btn" href="s/{sid}/">打开资源</a>'
                f'<button class="btn copy" data-url="{short}">复制链接</button></div></div>'
            )
        sections.append(
            f'<section data-cat="{key}"><h2 class="cat">{label}'
            f'<span class="n">{len(group)} 个</span></h2>'
            f'<div class="grid">{"".join(cards)}</div></section>'
        )
    beacon = f"<script>\n{beacon_js('index-total')}\n</script>\n" if with_beacon else ""
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="Robin 的资源索引：AI 课程、搞钱玩法、影视与书籍合集，全部永久有效。">
{beacon}<style>{INDEX_CSS}</style>
</head>
<body>
<div class="wrap">
<header class="top">
<div class="logo">📦</div>
<div>
<h1>资源索引</h1>
<p class="sub">by Robin（@robin_playbooks）· 共 {len(links)} 个资源 · 全部永久有效、无需提取码</p>
</div>
</header>
<div class="toolbar">
<input class="search" id="q" type="search" placeholder="🔍 搜资源名，如：编程 / 小红书 / 英语…" autocomplete="off">
<div class="chips">{"".join(chips)}</div>
</div>
<main id="list">
{"".join(sections)}
<div class="empty" id="empty">没找到匹配的资源，换个词试试。</div>
</main>
<footer>
点「打开资源」会跳转到夸克网盘分享页；「复制链接」可把短链发给朋友。<br>
📊 <a href="stats.html">点击统计</a> · 关注 X：<a href="https://x.com/robin_playbooks">@robin_playbooks</a>
</footer>
</div>
<div id="toast">链接已复制</div>
<script>
var q = document.getElementById('q'), empty = document.getElementById('empty'), curCat = 'all';
function apply(){{
  var kw = q.value.trim().toLowerCase(), any = false;
  document.querySelectorAll('section[data-cat]').forEach(function(sec){{
    if (curCat !== 'all' && sec.dataset.cat !== curCat) {{ sec.style.display = 'none'; return; }}
    var vis = 0;
    sec.querySelectorAll('.card').forEach(function(c){{
      var hit = !kw || c.dataset.name.indexOf(kw) >= 0;
      c.style.display = hit ? '' : 'none'; if (hit) vis++;
    }});
    sec.style.display = vis ? '' : 'none'; if (vis) any = true;
  }});
  empty.style.display = any ? 'none' : 'block';
}}
q.addEventListener('input', apply);
document.querySelectorAll('.chip').forEach(function(ch){{
  ch.addEventListener('click', function(){{
    document.querySelectorAll('.chip').forEach(function(x){{ x.classList.remove('on'); }});
    ch.classList.add('on'); curCat = ch.dataset.cat; apply();
  }});
}});
document.querySelectorAll('.copy').forEach(function(b){{
  b.addEventListener('click', function(){{
    var url = b.dataset.url, done = function(){{
      var t = document.getElementById('toast'); t.classList.add('show');
      setTimeout(function(){{ t.classList.remove('show'); }}, 1600);
    }};
    if (navigator.clipboard && navigator.clipboard.writeText) {{
      navigator.clipboard.writeText(url).then(done).catch(function(){{ fallback(); }});
    }} else fallback();
    function fallback(){{
      var ta = document.createElement('textarea'); ta.value = url;
      document.body.appendChild(ta); ta.select();
      try {{ document.execCommand('copy'); }} catch(e) {{}}
      document.body.removeChild(ta); done();
    }}
  }});
}});
</script>
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
/* Abacus 限速约 30 次/10 秒/IP：严格节流（最多 3 并发、启动间隔 ≥350ms），
   失败进重试队列（退避 3s/8s，最多 3 次），避免整表一起被 429。 */
function fetchValue(id){{
  return fetch(API + encodeURIComponent(id)).then(function(r){{
    if (!r.ok) throw new Error(r.status);
    return r.json();
  }}).then(function(j){{
    if (typeof j.value !== "number") throw new Error("bad value");
    return j.value;
  }});
}}
function loadAll(){{
  var queue = ENTRIES.map(function(e){{ return {{id: e.id, tries: 0}}; }});
  queue.push({{id: "index-total", tries: 0, key: "__index"}});
  var inFlight = 0, lastStart = 0;
  function pump(){{
    while (inFlight < 3 && queue.length){{
      var wait = Math.max(0, 350 - (Date.now() - lastStart));
      if (wait > 0) {{ setTimeout(pump, wait); return; }}
      var item = queue.shift();
      inFlight++; lastStart = Date.now();
      (function(item){{
        fetchValue(item.id).then(function(v){{
          results[item.key || item.id] = v;
        }}).catch(function(){{
          item.tries++;
          if (item.tries < 3) {{
            setTimeout(function(){{ queue.push(item); pump(); }}, item.tries === 1 ? 3000 : 8000);
          }} else {{
            results[item.key || item.id] = null;
          }}
        }}).then(function(){{
          inFlight--; render(); pump();
        }});
      }})(item);
    }}
  }}
  render(); pump();
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

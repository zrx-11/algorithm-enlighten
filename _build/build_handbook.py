#!/usr/bin/env python3
"""把四本书的点化学习系统 + 跨书总览整合为单文件 index.html 总学习手册。

输入：_build/data_hello.json / data_tujie.json / data_fourth.json / data_clrs.json
      + 算法专项-点化学习系统/00-跨书总览/*.md
输出：算法专项-点化学习系统/index.html（单文件、无外部依赖，可离线打开、可直接部署 GitHub Pages）
"""
import json
import os
import re
import html as html_mod

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(ROOT)  # 项目目录
SYS_DIR = os.path.join(BASE, "算法专项-点化学习系统")

ALLOWED_RAW_TAGS = {
    "div", "span", "svg", "path", "rect", "circle", "line", "polyline",
    "polygon", "g", "text", "tspan", "defs", "lineargradient", "stop",
    "ellipse", "marker", "use", "a", "img", "details", "summary",
    "b", "i", "u", "br", "hr", "strong", "em", "code", "pre",
    "sub", "sup", "table", "thead", "tbody", "tr", "td", "th",
    "ul", "ol", "li", "p", "h1", "h2", "h3", "h4", "h5", "h6",
    "blockquote", "figure", "figcaption", "center",
}


def esc(t):
    return html_mod.escape(t, quote=True)


def san_url(u):
    return esc(u) if re.match(r"^(https?://|mailto:|#|/|\.\.?/)", u, re.I) else "#"


def inline(t):
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)",
               lambda m: f'<a href="{san_url(m.group(2))}" target="_blank" rel="noopener">{m.group(1)}</a>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", t)
    return t


def is_raw(l):
    m = re.match(r"^\s*</?([a-zA-Z0-9]+)", l)
    return m and m.group(1).lower() in ALLOWED_RAW_TAGS


def md2html(md):
    lines = md.replace("\r\n", "\n").split("\n")
    out, para, i, n = [], [], 0, len(lines)
    in_code, code_buf, code_lang = False, [], ""
    lists = []

    def flush_para():
        nonlocal para
        if para:
            t = inline(esc(" ".join(para).strip()))
            if t:
                out.append(f"<p>{t}</p>")
            para = []

    def close_lists(mini=0):
        while lists and lists[-1][1] >= mini:
            typ, _ = lists.pop()
            out.append("</ol>" if typ == "ol" else "</ul>")

    while i < n:
        line = lines[i]
        if line.lstrip().startswith("```"):
            if in_code:
                lang = code_lang or ""
                if lang.lower() == "mermaid":
                    out.append(f'<div class="mermaid" data-src="1">{esc(chr(10).join(code_buf))}</div>'
                               f'<p class="mermaid-hint">↑ Mermaid 图示：联网时自动渲染；离线则阅读源码与正文。</p>')
                else:
                    cls = f' class="lang-{lang}"' if lang else ""
                    out.append(f"<pre{cls}><code>{esc(chr(10).join(code_buf))}</code></pre>")
                in_code = False
                code_buf = []
            else:
                flush_para()
                close_lists()
                in_code = True
                code_lang = line.lstrip()[3:].strip()
                code_buf = []
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue
        if is_raw(line):
            flush_para()
            close_lists()
            buf = [line]
            j = i + 1
            while j < n and is_raw(lines[j]):
                buf.append(lines[j])
                j += 1
            out.append("\n".join(buf))
            i = j
            continue
        s = line.strip()
        if not s:
            flush_para()
            close_lists()
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            flush_para()
            close_lists()
            out.append(f"<h{len(m.group(1))}>{inline(esc(m.group(2)))}</h{len(m.group(1))}>")
            i += 1
            continue
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", s):
            flush_para()
            close_lists()
            out.append("<hr>")
            i += 1
            continue
        if s.startswith(">"):
            flush_para()
            out.append(f"<blockquote>{inline(esc(re.sub(r'^>\\s?', '', s)))}</blockquote>")
            i += 1
            continue
        if s.startswith("|") and i + 1 < n and re.match(r"^\s*\|?[\s:\-|]+\|?\s*$", lines[i + 1]):
            flush_para()
            close_lists()
            head = [c.strip() for c in s.strip("|").split("|")]
            rows, j = [], i + 2
            while j < n and lines[j].strip().startswith("|"):
                rows.append([c.strip() for c in lines[j].strip().strip("|").split("|")])
                j += 1
            t = ["<table><thead><tr>"] + [f"<th>{inline(esc(c))}</th>" for c in head] + ["</tr></thead><tbody>"]
            for r in rows:
                t.append("<tr>" + "".join(f"<td>{inline(esc(c))}</td>" for c in r) + "</tr>")
            t.append("</tbody></table>")
            out.append("".join(t))
            i = j
            continue
        m = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", line)
        if m:
            ind = len(m.group(1).replace("\t", "    "))
            typ = "ol" if re.match(r"\d", m.group(2)) else "ul"
            if not lists or lists[-1][1] < ind:
                flush_para()
                close_lists(ind)
                if lists and lists[-1][1] < ind:
                    out[-1] = out[-1].rstrip("</li>") + f"\n<{typ}>\n<li>"
                else:
                    out.append(f"<{typ}><li>")
                lists.append((typ, ind))
            elif lists[-1][1] == ind and lists[-1][0] != typ:
                close_lists(ind)
                out.append(f"<{typ}><li>")
                lists.append((typ, ind))
            else:
                out.append("</li><li>")
            out.append(inline(esc(m.group(3))))
            i += 1
            continue
        para.append(s)
        i += 1
    flush_para()
    close_lists()
    return "\n".join(out)


# ---------------------------------------------------------------------------

BOOK_FILES = {
    "hello": "data_hello.json",
    "tujie": "data_tujie.json",
    "fourth": "data_fourth.json",
    "clrs": "data_clrs.json",
}
BOOK_TABS = [
    ("cross", "跨书总览"),
    ("hello", "Hello 算法"),
    ("tujie", "算法图解"),
    ("fourth", "算法 第四版"),
    ("clrs", "算法导论"),
]
# 单独学习伴侣文件（相对 index.html）
COMPANIONS = {
    "hello": "01-hello算法/hello算法学习伴侣.html",
    "tujie": "02-算法图解/算法图解学习伴侣.html",
    "fourth": "03-算法第四版/算法第四版学习伴侣.html",
    "clrs": "04-算法导论/算法导论学习伴侣.html",
}
CROSS_DOCS = [
    ("readme", "README.md", "总览 · 四书推荐学习顺序"),
    ("mapping", "跨书概念映射表.md", "跨书概念映射表"),
    ("checks", "综合检验建议.md", "综合检验建议"),
]


def normalize_book(key, data):
    """统一化：改写内部链接为带书名的路由；测验 id 加章节前缀去重；聚合综合测验页。"""
    man = data["manifest"]
    rendered = data["rendered"]

    # ① 内部链接 #/xxx => #/book/<key>/xxx
    rendered = {pid: re.sub(r'href="#/', f'href="#/book/{key}/', h) for pid, h in rendered.items()}

    # ①b Mermaid 节点标签内的 " | " 会破坏语法，替换为全角竖线
    rendered = {pid: re.sub(
        r'(<div class="mermaid" data-src="1">)(.*?)(</div>)',
        lambda m: m.group(1) + m.group(2).replace(" | ", " ｜ ") + m.group(3),
        h, flags=re.S) for pid, h in rendered.items()}

    # ② 测验 id 去重：按章节重写 data-qid / name / manifest.id
    chapter_with_quiz = {}
    for ch in man.get("chapters", []):
        cid = ch["id"]
        pid = f"__quiz_{cid}__"
        if pid not in rendered:
            continue
        h = rendered[pid]
        h = re.sub(r"data-qid='([^']+)'", lambda m: f"data-qid='{cid}-{m.group(1)}'", h)
        h = re.sub(r"name='([^']+)'", lambda m: f"name='{cid}-{m.group(1)}'", h)
        rendered[pid] = h
        chapter_with_quiz[cid] = True

    for q in man.get("quizzes", []):
        cid = q.get("chapterId")
        if cid and chapter_with_quiz.get(cid):
            qid = str(q.get("id", ""))
            if not qid.startswith(cid + "-"):
                q["id"] = f"{cid}-{qid}"

    # ③ 聚合「全部测验」页：按章节顺序拼接（标题降为 h2）
    all_parts = ["<h1>全部测验</h1><p>下方为全书各章测验，逐题作答、即时反馈并显示解析。</p>"]
    for ch in man.get("chapters", []):
        cid = ch["id"]
        pid = f"__quiz_{cid}__"
        if pid not in rendered:
            continue
        h = rendered[pid]
        h = re.sub(r"^\s*<h1>.*?</h1>", "", h, count=1, flags=re.S)
        all_parts.append(f"<h2>测验：{esc(ch.get('title', cid))}</h2>" + h)
    rendered["__quiz_all__"] = "".join(all_parts)

    data["rendered"] = rendered
    data["quizCoverage"] = chapter_with_quiz
    return data


def main():
    books = {}
    for key, fn in BOOK_FILES.items():
        with open(os.path.join(ROOT, fn), encoding="utf-8") as f:
            books[key] = normalize_book(key, json.load(f))

    meta = []
    for key in ("hello", "tujie", "fourth", "clrs"):
        man = books[key]["manifest"]
        meta.append({
            "key": key,
            "title": man.get("title", key),
            "subtitle": man.get("subtitle", ""),
            "chapters": len(man.get("chapters", [])),
            "concepts": len(man.get("concepts", [])),
            "quizzes": len(man.get("quizzes", [])),
            "cards": len(man.get("flashcards", [])),
            "companion": COMPANIONS[key],
        })

    cross = {}
    for key, fn, _ in CROSS_DOCS:
        p = os.path.join(SYS_DIR, "00-跨书总览", fn)
        with open(p, encoding="utf-8") as f:
            cross[key] = md2html(f.read())

    # 数据序列化（转义 </ 防止截断脚本）
    def dump(o):
        return json.dumps(o, ensure_ascii=False).replace("</", "<\\/")

    payload = "{" + ",".join(
        f'"{k}":{{"manifest":{dump(v["manifest"])},"rendered":{dump(v["rendered"])},"nav":{dump(v["nav"])},"quizCoverage":{dump(v.get("quizCoverage", {}))}}}'
        for k, v in books.items()) + "}"

    html = _SHELL
    html = html.replace("__BOOKS__", payload)
    html = html.replace("__META__", dump(meta))
    html = html.replace("__CROSS__", dump(cross))
    html = html.replace("__TABS__", dump([{"key": k, "label": l} for k, l in BOOK_TABS]))
    out_path = os.path.join(SYS_DIR, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"生成完成: {out_path}  ({os.path.getsize(out_path)/1024:.0f} KB)")


_SHELL = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>算法四书 · 总学习手册</title>
<style>
:root{
  --bg:#f7f7f8; --panel:#ffffff; --text:#1f2328; --muted:#6b7280;
  --accent:#2563eb; --accent-soft:#dbeafe; --border:#e5e7eb;
  --ok:#16a34a; --bad:#dc2626; --code-bg:#f3f4f6;
}
[data-theme="dark"]{
  --bg:#111318; --panel:#1a1d24; --text:#e5e7eb; --muted:#9ca3af;
  --accent:#60a5fa; --accent-soft:#1e3a5f; --border:#2d333d;
  --ok:#4ade80; --bad:#f87171; --code-bg:#20242c;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  background:var(--bg);color:var(--text);line-height:1.7;font-size:15px}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
header{position:sticky;top:0;z-index:20;background:var(--panel);border-bottom:1px solid var(--border);padding:10px 18px}
.brand{font-size:17px;font-weight:700;display:inline-block;margin-right:18px}
.brand span{color:var(--muted);font-weight:400;font-size:12px;margin-left:6px}
.tabs{display:inline-flex;gap:6px;flex-wrap:wrap;vertical-align:middle}
.tab{border:1px solid var(--border);background:var(--bg);color:var(--text);border-radius:999px;padding:4px 14px;cursor:pointer;font-size:13px}
.tab.active{background:var(--accent);border-color:var(--accent);color:#fff}
.hdr-right{float:right;display:flex;gap:8px;align-items:center;margin-top:2px}
#q{width:260px;padding:6px 10px;border:1px solid var(--border);border-radius:8px;background:var(--bg);color:var(--text);font-size:13px}
#theme-btn{border:1px solid var(--border);background:var(--panel);color:var(--text);border-radius:8px;padding:5px 12px;cursor:pointer}
.layout{display:flex;min-height:calc(100vh - 60px)}
.sidebar{width:290px;flex:none;background:var(--panel);border-right:1px solid var(--border);
  padding:14px;position:sticky;top:60px;height:calc(100vh - 60px);overflow-y:auto}
#progress-bar{height:5px;background:var(--border);border-radius:3px;margin:6px 0;overflow:hidden}
#progress-bar>div{height:100%;width:0;background:var(--accent);transition:width .3s}
#progress-label{font-size:12px;color:var(--muted);margin-bottom:8px}
.nav-sec{font-size:12px;color:var(--muted);margin:12px 0 4px;text-transform:uppercase;letter-spacing:.4px}
.nav-item{display:block;padding:5px 10px;border-radius:6px;color:var(--text);font-size:14px}
.nav-item:hover{background:var(--accent-soft);text-decoration:none}
.nav-item.active{background:var(--accent-soft);color:var(--accent);font-weight:600}
.nav-item .done{float:right;color:var(--ok);font-size:12px}
.main{flex:1;min-width:0;padding:28px 40px 80px;max-width:920px}
.page h1{font-size:26px;border-bottom:2px solid var(--border);padding-bottom:8px;margin-top:0}
.page h2{font-size:20px;margin-top:26px}
.page h3{font-size:17px;margin-top:22px}
.page table{border-collapse:collapse;width:100%;margin:12px 0;font-size:14px}
.page th,.page td{border:1px solid var(--border);padding:6px 10px;text-align:left}
.page th{background:var(--code-bg)}
.page code{background:var(--code-bg);padding:2px 5px;border-radius:4px;font-size:.9em}
.page pre{background:var(--code-bg);padding:12px;border-radius:8px;overflow-x:auto;font-size:13px}
.page pre code{background:none;padding:0}
.page blockquote{border-left:4px solid var(--accent);margin:12px 0;padding:6px 14px;background:var(--accent-soft);border-radius:0 6px 6px 0}
.page img{max-width:100%}
.mermaid{background:var(--code-bg);padding:14px;border-radius:8px;overflow-x:auto;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12.5px;white-space:pre;color:var(--muted)}
.mermaid-hint{font-size:12px;color:var(--muted);margin:4px 0 14px}
svg{max-width:100%;height:auto}
.quiz-item{border:1px solid var(--border);border-radius:10px;padding:14px 16px;margin:14px 0;background:var(--panel)}
.quiz-q{margin:0 0 8px;font-weight:500}
.quiz-opts label{display:block;padding:4px 0;cursor:pointer}
.quiz-blank{width:60%;padding:6px 10px;border:1px solid var(--border);border-radius:6px;background:var(--bg);color:var(--text)}
.quiz-check{margin-top:10px;padding:6px 16px;border:none;border-radius:6px;background:var(--accent);color:#fff;cursor:pointer}
.quiz-feedback{margin-left:12px;font-size:13px}
.fb-ok{color:var(--ok)}.fb-bad{color:var(--bad)}
.quiz-explain{margin-top:8px;font-size:13px;color:var(--muted);border-top:1px dashed var(--border);padding-top:6px}
.flashcard{perspective:1200px;margin:24px auto;max-width:520px;cursor:pointer;user-select:none}
.fc-inner{position:relative;width:100%;height:240px;transform-style:preserve-3d;transition:transform .5s}
.flashcard.flip .fc-inner{transform:rotateY(180deg)}
.fc-front,.fc-back{position:absolute;inset:0;backface-visibility:hidden;display:flex;align-items:center;justify-content:center;
  padding:22px;border-radius:14px;border:1px solid var(--border);background:var(--panel);font-size:16px;text-align:center}
.fc-back{transform:rotateY(180deg);background:var(--accent-soft);color:var(--text)}
.card-controls{display:flex;gap:14px;align-items:center;margin:12px 0;flex-wrap:wrap}
.card-actions{display:flex;gap:12px;justify-content:center}
.card-actions button{padding:8px 22px;border:none;border-radius:8px;cursor:pointer;font-size:14px}
#card-known-btn{background:var(--ok);color:#fff}
#card-again-btn{background:var(--bad);color:#fff}
.card-counts{color:var(--muted);font-size:13px}
.path-step{margin:8px 0;padding:10px 12px;border:1px solid var(--border);border-radius:8px;background:var(--panel)}
.path-step.passed{border-color:var(--ok)}
#glossary-filter{width:100%;max-width:380px;padding:7px 10px;border:1px solid var(--border);border-radius:8px;background:var(--bg);color:var(--text);margin-bottom:10px}
#glossary-list li{padding:6px 0;border-bottom:1px dashed var(--border)}
.glossary-ref{color:var(--muted);font-size:12px}
.search-hit{margin:10px 0}
.book-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:14px;margin:16px 0}
.book-card{border:1px solid var(--border);border-radius:12px;padding:16px;background:var(--panel)}
.book-card h3{margin:0 0 6px;font-size:16px}
.book-card .meta{font-size:13px;color:var(--muted);margin-bottom:10px}
.book-card .enter{font-size:13px}
.empty{color:var(--muted);padding:20px 0}
@media print{header,.sidebar,.quiz-actions,.card-actions,.card-controls{display:none!important}.main{max-width:none;padding:0}}
@media (max-width:820px){.sidebar{width:100%;height:auto;position:static}.layout{flex-direction:column}.main{padding:16px}
  .hdr-right{float:none;margin-top:8px}#q{width:100%}}
</style>
</head>
<body>
<header>
  <span class="brand">算法四书 · 总学习手册<span>算法图解 / Hello 算法 / 算法第四版 / 算法导论</span></span>
  <span class="tabs" id="tabs"></span>
  <span class="hdr-right">
    <input id="q" type="search" placeholder="全书搜索（四本书 + 跨书总览）…">
    <button id="theme-btn">🌙 深色</button>
  </span>
</header>
<div class="layout">
  <aside class="sidebar">
    <div id="progress-bar"><div id="progress-fill"></div></div>
    <div id="progress-label">进度 0%</div>
    <nav id="nav"></nav>
  </aside>
  <main><div id="view" class="page"></div></main>
</div>
<script>
const BOOKS = __BOOKS__;
const META = __META__;
const CROSS = __CROSS__;
const TABS = __TABS__;
const $ = s => document.querySelector(s);
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

const CROSS_LABELS = {readme:'总览 · 四书推荐学习顺序', mapping:'跨书概念映射表', checks:'综合检验建议'};

let cur = {book:'cross', doc:'readme', page:'cross'};
const store = {
  get(k){ try{ return JSON.parse(localStorage.getItem(k)||'null') }catch(e){ return null } },
  set(k,v){ try{ localStorage.setItem(k, JSON.stringify(v)) }catch(e){} }
};
function stKey(book,k){ return 'hb:'+book+':'+k; }
function getState(book){
  return { visited: store.get(stKey(book,'visited'))||[], quiz: store.get(stKey(book,'quiz'))||{}, cards: store.get(stKey(book,'cards'))||{} };
}

/* ---------- 路由 ---------- */
function parseHash(){
  let h = location.hash.replace(/^#\//,'');
  if(!h) return {book:'cross', doc:'readme', page:'cross'};
  const p = h.split('/');
  if(p[0]==='cross') return {book:'cross', doc:p[1]||'readme', page:'cross'};
  if(p[0]==='book'){
    const key=p[1], page=p.slice(2).join('/')||'path';
    return {book:key, page:page, doc:null};
  }
  return {book:'cross', doc:'readme', page:'cross'};
}
function pageIdOf(page){
  if(page==='path') return '__path__';
  if(page==='cards') return '__cards__';
  if(page==='glossary') return '__glossary__';
  if(page==='patterns') return '__patterns__';
  if(page==='cheatsheet') return '__cheatsheet__';
  if(page.startsWith('quiz/')) return '__quiz_'+(page.split('/')[1]||'all')+'__';
  if(page.startsWith('chapter/')) return page.slice(8);   // chapter/ch01 => ch01
  if(page.startsWith('concept/')) return page.slice(8);   // concept/c01 => c01
  return page;
}

/* ---------- 顶栏 tabs ---------- */
function renderTabs(){
  const el = $('#tabs'); el.innerHTML='';
  TABS.forEach(t=>{
    const b=document.createElement('button');
    b.className='tab'+(cur.book===t.key?' active':'');
    b.textContent=t.label;
    b.onclick=()=>{ location.hash = t.key==='cross' ? '#/cross/readme' : '#/book/'+t.key+'/path'; };
    el.appendChild(b);
  });
}

/* ---------- 侧边栏 ---------- */
function renderNav(){
  const nav=$('#nav'); nav.innerHTML='';
  const add=(label,href,cls)=>{
    const a=document.createElement('a'); a.className='nav-item'+(cls?' '+cls:''); a.href=href; a.textContent=label;
    nav.appendChild(a); return a;
  };
  const sec=t=>{ const d=document.createElement('div'); d.className='nav-sec'; d.textContent=t; nav.appendChild(d); };

  if(cur.book==='cross'){
    sec('跨书总览');
    Object.entries(CROSS_LABELS).forEach(([k,l])=>{
      add(l, '#/cross/'+k, cur.doc===k?'active':'');
    });
    sec('四本书入口');
    META.forEach(m=> add(m.title, '#/book/'+m.key+'/path'));
    updateProgress(0,'跨书总览');
    return;
  }
  const B=BOOKS[cur.book];
  const S=getState(cur.book);
  const man=B.manifest;
  // 学习路径
  add('学习路径','#/book/'+cur.book+'/path', cur.page==='path'?'active':'');
  // 章节
  sec('章节');
  (man.chapters||[]).forEach(c=>{
    const id=c.id;
    const a=add(c.title, '#/book/'+cur.book+'/chapter/'+id, cur.page==='chapter/'+id?'active':'');
    if(S.visited.includes(cur.book+'/chapter/'+id)){
      const s=document.createElement('span'); s.className='done'; s.textContent='✓'; a.appendChild(s);
    }
  });
  // 概念
  if((man.concepts||[]).length){
    sec('概念');
    man.concepts.forEach(c=>{
      const a=add(c.title, '#/book/'+cur.book+'/concept/'+c.id, cur.page==='concept/'+c.id?'active':'');
      if(S.visited.includes(cur.book+'/concept/'+c.id)){
        const s=document.createElement('span'); s.className='done'; s.textContent='✓'; a.appendChild(s);
      }
    });
  }
  // 测验
  sec('测验');
  add('综合测验（全书）','#/book/'+cur.book+'/quiz/all', cur.page==='quiz/all'?'active':'');
  (man.chapters||[]).forEach(c=>{
    const qc=(B.quizCoverage||{})[c.id];
    if(!qc) return;
    add('测验：'+c.title, '#/book/'+cur.book+'/quiz/'+c.id, cur.page==='quiz/'+c.id?'active':'');
  });
  // 其他
  sec('复习工具');
  add('抽认卡','#/book/'+cur.book+'/cards', cur.page==='cards'?'active':'');
  add('术语表','#/book/'+cur.book+'/glossary', cur.page==='glossary'?'active':'');
  if(B.rendered['__patterns__']) add('模式库','#/book/'+cur.book+'/patterns', cur.page==='patterns'?'active':'');
  if(B.rendered['__cheatsheet__']) add('速查表','#/book/'+cur.book+'/cheatsheet', cur.page==='cheatsheet'?'active':'');
  // 单独伴侣入口
  sec('其他');
  const m=META.find(x=>x.key===cur.book);
  if(m) add('单独打开《'+m.title.replace(/点化学习(系统|伴侣)/,'')+'》学习伴侣 ↗', encodeURI(m.companion));

  updateProgressBook(cur.book);
}

/* ---------- 进度 ---------- */
function updateProgress(pct,label){
  $('#progress-fill').style.width=pct+'%';
  $('#progress-label').textContent=label;
}
function updateProgressBook(book){
  const B=BOOKS[book], S=getState(book);
  const chs=(B.manifest.chapters||[]).length;
  const done=(B.manifest.chapters||[]).filter(c=>S.visited.includes(book+'/chapter/'+c.id)).length;
  const pct=chs?Math.round(done/chs*100):0;
  $('#progress-fill').style.width=pct+'%';
  $('#progress-label').textContent=`《${(META.find(x=>x.key===book)||{}).title||book}》 进度 ${pct}% · 已学 ${done}/${chs} 章`;
}

/* ---------- 渲染 ---------- */
function renderCross(){
  const v=$('#view');
  const docId=cur.doc||'readme';
  const html=CROSS[docId]||'<div class="empty">页面不存在</div>';
  let pre='';
  if(docId==='readme'){
    pre = '<h1>算法四书 · 总学习手册</h1>'
      + '<p>四本书 + 跨书总览整合为一个学习系统。点击顶部标签切换书，或用下方卡片进入。'
      + '每本书含学习路径、章节精讲、概念页、测验、抽认卡、术语表、模式库与速查表，进度自动保存在本机浏览器。</p>'
      + '<div class="book-cards">'
      + META.map(m=>`<div class="book-card"><h3>${esc(m.title)}</h3>
          <div class="meta">${m.chapters} 章 · ${m.concepts} 概念 · ${m.quizzes} 测验 · ${m.cards} 抽认卡</div>
          <div class="enter"><a href="#/book/${m.key}/path">进入学习 →</a> &nbsp;|&nbsp;
          <a href="${encodeURI(m.companion)}" target="_blank">单独伴侣 ↗</a></div></div>`).join('')
      + '</div>';
  }
  v.innerHTML = pre + html;
  renderMermaid();
}

function renderBook(){
  const B=BOOKS[cur.book];
  if(!B){ $('#view').innerHTML='<div class="empty">书目不存在</div>'; return; }
  const pid=pageIdOf(cur.page);
  let html=B.rendered[pid];
  if(!html){ html='<div class="empty">页面不存在</div>'; }
  // 记录已访问
  const S=getState(cur.book);
  if((cur.page.startsWith('chapter/')||cur.page.startsWith('concept/')) && !S.visited.includes(cur.book+'/'+cur.page)){
    S.visited.push(cur.book+'/'+cur.page);
    store.set(stKey(cur.book,'visited'), S.visited);
  }
  $('#view').innerHTML=html;
  if(cur.page==='cards') initCards();
  if(cur.page==='glossary') initGlossary();
  if(cur.page.startsWith('quiz/')) initQuizzes();
  if(pid==='__path__') updatePath();
  renderMermaid();
}

/* ---------- 测验 ---------- */
function initQuizzes(){
  const B=BOOKS[cur.book];
  document.querySelectorAll('.quiz-item').forEach(item=>{
    const btn=item.querySelector('.quiz-check');
    if(!btn||item.dataset.inited) return;
    item.dataset.inited='1';
    btn.addEventListener('click',()=>{
      const qid=item.dataset.qid, type=item.dataset.type;
      const q=(B.manifest.quizzes||[]).find(x=>x.id===qid); if(!q) return;
      let user=null, correct=false, fb='';
      if(type==='single'){
        const sel=item.querySelector('input:checked');
        user=sel?parseInt(sel.value):null;
        correct=(user===q.answer);
        fb=correct?'✓ 正确':'✗ 错误'+(user==null?'（未作答）':'');
      }else if(type==='multi'){
        user=Array.from(item.querySelectorAll('input:checked')).map(i=>parseInt(i.value)).sort();
        const ans=Array.isArray(q.answer)?q.answer.slice().sort():[q.answer];
        correct=user.length>0 && JSON.stringify(user)===JSON.stringify(ans);
        fb=correct?'✓ 正确':'✗ 错误';
      }else if(type==='blank'){
        const v=(item.querySelector('.quiz-blank').value||'').trim().toLowerCase();
        correct=(v===String(q.answer).trim().toLowerCase());
        fb=correct?'✓ 正确':'✗ 错误'+(v?'':'（未作答）');
      }
      item.querySelectorAll('input:checked').forEach(i=>{
        const val=parseInt(i.value);
        if(Array.isArray(q.answer)?q.answer.includes(val):val===q.answer) i.parentElement.style.color='var(--ok)';
        else i.parentElement.style.color='var(--bad)';
      });
      const feed=item.querySelector('.quiz-feedback');
      feed.className='quiz-feedback '+(correct?'fb-ok':'fb-bad');
      feed.textContent=fb;
      let ex=item.querySelector('.quiz-explain');
      if(!ex){ ex=document.createElement('div'); ex.className='quiz-explain'; item.appendChild(ex); }
      ex.innerHTML='解析：'+esc(q.explain||'');
      const S=getState(cur.book);
      const ch=q.chapterId||'__all__';
      if(!S.quiz[ch]) S.quiz[ch]={n:0};
      S.quiz[ch].n+=1;
      store.set(stKey(cur.book,'quiz'), S.quiz);
    });
  });
}
function updatePath(){
  const B=BOOKS[cur.book], S=getState(cur.book);
  document.querySelectorAll('.path-step').forEach(el=>{
    const step=el.id.replace('path-','');
    const s=(B.manifest.learningPath||[]).find(x=>String(x.step)===step);
    if(s && (s.chapterIds||[]).every(c=>S.visited.includes(cur.book+'/chapter/'+c))){
      el.classList.add('passed');
      if(!el.querySelector('.ck')){ const sp=document.createElement('span'); sp.className='ck done'; sp.textContent=' ✓ 已完成'; el.appendChild(sp); }
    }
  });
}

/* ---------- 抽认卡 ---------- */
let cardIdx=0, cardList=[];
function initCards(){
  const B=BOOKS[cur.book], S=getState(cur.book);
  const cards=B.manifest.flashcards||[];
  cardList=cards.slice(); cardIdx=0;
  if(!$('#card-done')){
    const d=document.createElement('div'); d.id='card-done'; d.className='empty';
    d.style.display='none'; d.textContent='本组卡片已全部复习完 🎉';
    const st=$('#card-stage'); if(st) st.appendChild(d);
  }
  const sel=$('#card-filter'); if(!sel) return;
  sel.innerHTML='<option value="">全部</option>';
  [...new Set(cards.map(c=>c.chapterId).filter(Boolean))].forEach(c=>{
    const o=document.createElement('option'); o.value=c;
    const ch=(B.manifest.chapters||[]).find(x=>x.id===c);
    o.textContent=ch?ch.title:c; sel.appendChild(o);
  });
  sel.onchange=()=>{ const v=sel.value; cardList=v?cards.filter(c=>c.chapterId===v):cards.slice(); cardIdx=0; showCard(); };
  $('#flashcard').onclick=()=>$('#flashcard').classList.toggle('flip');
  $('#card-known-btn').onclick=()=>markCard(true);
  $('#card-again-btn').onclick=()=>markCard(false);
  showCard();
}
function showCard(){
  const S=getState(cur.book);
  updateCardCounts();
  const done=$('#card-done'), fc=$('#flashcard');
  if(cardIdx>=cardList.length){
    if(done) done.style.display=''; if(fc) fc.style.display='none'; return;
  }
  if(done) done.style.display='none'; if(fc) fc.style.display='';
  const c=cardList[cardIdx];
  document.querySelector('.fc-front').textContent=c.front;
  document.querySelector('.fc-back').textContent=c.back;
  $('#flashcard').classList.remove('flip');
}
function markCard(known){
  const S=getState(cur.book);
  const c=cardList[cardIdx]; if(!c) return;
  S.cards[c.id]=known?'known':'again';
  store.set(stKey(cur.book,'cards'), S.cards);
  cardIdx++; showCard();
}
function updateCardCounts(){
  const S=getState(cur.book);
  const known=Object.values(S.cards).filter(v=>v==='known').length;
  const again=Object.values(S.cards).filter(v=>v==='again').length;
  const k=$('#card-known'), a=$('#card-again'), l=$('#card-left');
  if(k) k.textContent=known; if(a) a.textContent=again; if(l) l.textContent=Math.max(0,cardList.length-cardIdx);
}

/* ---------- 术语表 ---------- */
function initGlossary(){
  const input=$('#glossary-filter');
  if(!input||input.dataset.inited) return;
  input.dataset.inited='1';
  input.oninput=()=>{
    const v=input.value.trim().toLowerCase();
    document.querySelectorAll('#glossary-list li').forEach(li=>{
      li.style.display=(!v||li.dataset.term.includes(v))?'':'none';
    });
  };
}

/* ---------- 全局搜索 ---------- */
let searchIdx=null;
function buildSearch(){
  if(searchIdx) return searchIdx;
  searchIdx=[];
  META.forEach(m=>{
    const B=BOOKS[m.key];
    Object.entries(B.rendered).forEach(([pid,html])=>{
      if(pid.startsWith('__')) return;
      const text=html.replace(/<[^>]+>/g,' ').replace(/\s+/g,' ');
      searchIdx.push({book:m.key, page:pdfToPage(pid, B), text, label:m.title});
    });
  });
  Object.entries(CROSS).forEach(([k,html])=>{
    searchIdx.push({book:'cross', page:'cross/'+k, text:html.replace(/<[^>]+>/g,' ').replace(/\s+/g,' '), label:'跨书总览 · '+(CROSS_LABELS[k]||k)});
  });
  return searchIdx;
}
function pdfToPage(pid, B){
  if(pid.startsWith('__quiz_')) return 'quiz/'+pid.replace('__quiz_','').replace('__','');
  if(pid==='__path__') return 'path';
  if(pid==='__cards__') return 'cards';
  if(pid==='__glossary__') return 'glossary';
  if(pid==='__patterns__') return 'patterns';
  if(pid==='__cheatsheet__') return 'cheatsheet';
  const ch=(B.manifest.chapters||[]).find(c=>c.id===pid);
  if(ch) return 'chapter/'+pid;
  return 'concept/'+pid;
}
$('#q').addEventListener('input', e=>{
  const v=e.target.value.trim().toLowerCase();
  if(!v){ route(); return; }
  const hits=buildSearch().filter(p=>p.text.toLowerCase().includes(v)).slice(0,40);
  $('#view').innerHTML='<h1>搜索结果：'+esc(v)+'</h1>'+
    (hits.length? hits.map(h=>{
      const href=h.book==='cross'?('#/cross/'+(h.page.split('/')[1]||'readme')):('#/book/'+h.book+'/'+h.page);
      return `<div class="search-hit"><a href="${href}">${esc(h.label)}</a><br><span style="color:var(--muted);font-size:13px">${esc(h.text.slice(0,200))}</span></div>`;
    }).join('') : '<div class="empty">未找到相关内容，试试章节名 / 概念名 / 术语。</div>');
});

/* ---------- Mermaid ---------- */
let mermaidState='idle';
function renderMermaid(){
  const els=Array.from(document.querySelectorAll('.mermaid')).filter(el=>!el.dataset.rendered);
  if(!els.length) return;
  const run=()=>{ try{
    mermaid.initialize({startOnLoad:false, theme:document.body.dataset.theme==='dark'?'dark':'default'});
    els.forEach((el,idx)=>{ try{ el.innerHTML=mermaid.render('mm'+Date.now()+idx, el.textContent); el.dataset.rendered='1'; }
      catch(e){ el.dataset.rendered='0'; } });
  }catch(e){} };
  if(window.mermaid){ run(); return; }
  if(mermaidState==='loading') return;
  mermaidState='loading';
  const s=document.createElement('script');
  s.src='https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js';
  s.onload=()=>{ mermaidState='loaded'; run(); };
  s.onerror=()=>{ mermaidState='failed'; };
  document.head.appendChild(s);
}

/* ---------- 主题 ---------- */
const themeBtn=$('#theme-btn');
themeBtn.onclick=()=>{
  const d=document.body.dataset.theme==='dark';
  document.body.dataset.theme=d?'':'dark';
  themeBtn.textContent=d?'🌙 深色':'☀️ 浅色';
};

/* ---------- 启动 ---------- */
function route(){
  cur=parseHash();
  renderTabs();
  renderNav();
  if(cur.book==='cross') renderCross(); else renderBook();
  window.scrollTo(0,0);
}
window.addEventListener('hashchange', route);
route();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()

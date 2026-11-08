#!/usr/bin/env python3
"""用 Playwright 对 index.html 总学习手册做端到端交互验证。"""
import json
import os
from playwright.sync_api import sync_playwright

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "file://" + os.path.join(BASE, "算法专项-点化学习系统", "index.html")

results = []


def check(name, ok, extra=""):
    results.append((name, bool(ok), extra))
    print(("PASS " if ok else "FAIL ") + name + (" | " + extra if extra else ""))


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path="/usr/local/bin/chromium", args=["--no-sandbox", "--disable-gpu"])
    page = browser.new_page()
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))

    # 1 首页
    page.goto(URL + "#/cross/readme")
    page.wait_for_timeout(1200)
    check("首页标题", "算法四书 · 总学习手册" in page.inner_text("#view"))
    check("四书卡片数", page.eval_on_selector_all(".book-card", "els=>els.length") == 4,
          f"{page.eval_on_selector_all('.book-card','els=>els.length')} 张")

    # 2 跨书映射 / 检验
    page.goto(URL + "#/cross/mapping")
    page.wait_for_timeout(600)
    txt = page.inner_text("#view")
    check("跨书概念映射表渲染", len(txt) > 300 and "映射" in txt, f"{len(txt)} 字符")
    page.goto(URL + "#/cross/checks")
    page.wait_for_timeout(600)
    check("综合检验建议渲染", len(page.inner_text("#view")) > 300)

    # 3 Hello 算法 章节
    page.goto(URL + "#/book/hello/chapter/ch01")
    page.wait_for_timeout(800)
    v = page.inner_text("#view")
    check("Hello 章节渲染", len(v) > 200, f"{len(v)} 字符")
    check("侧栏章节数=17", page.eval_on_selector_all("#nav .nav-item", "els=>els.length") >= 17,
          f"{page.eval_on_selector_all('#nav .nav-item','els=>els.length')} 项")

    # 4 测验交互（取第一题正确答案作答）
    page.goto(URL + "#/book/hello/quiz/all")
    page.wait_for_timeout(800)
    n_quiz = page.eval_on_selector_all(".quiz-item", "els=>els.length")
    check("综合测验题数", n_quiz > 0, f"{n_quiz} 题")
    q = page.eval_on_selector(".quiz-item", """el=>{
        const qid=el.dataset.qid, type=el.dataset.type;
        const B=JSON.parse(document.getElementById('view').dataset.x||'null');
        return {qid:qid,type:type};
    }""")
    # 从内嵌数据取正确答案
    ans = page.evaluate("""(qid)=>{
        const B = BOOKS[cur.book];
        const q=(B.manifest.quizzes||[]).find(x=>x.id===qid);
        return q ? {type:q.type, answer:q.answer} : null;
    }""", q["qid"])
    if ans and ans["type"] == "single":
        page.click(f".quiz-item[data-qid='{q['qid']}'] input[value='{ans['answer']}']")
    elif ans and ans["type"] == "multi":
        for a in ans["answer"]:
            page.click(f".quiz-item[data-qid='{q['qid']}'] input[value='{a}']")
    elif ans and ans["type"] == "blank":
        page.fill(f".quiz-item[data-qid='{q['qid']}'] .quiz-blank", str(ans["answer"]))
    page.click(f".quiz-item[data-qid='{q['qid']}'] .quiz-check")
    page.wait_for_timeout(300)
    fb = page.inner_text(f".quiz-item[data-qid='{q['qid']}'] .quiz-feedback")
    check("测验作答反馈（正确）", "正确" in fb, fb)
    check("测验解析出现", page.eval_on_selector_all(".quiz-explain", "els=>els.length") > 0)

    # 5 抽认卡
    page.goto(URL + "#/book/tujie/cards")
    page.wait_for_timeout(800)
    check("抽认卡正面", page.inner_text(".fc-front").strip() != "",
          page.inner_text(".fc-front")[:24])
    page.click("#flashcard")
    check("卡片翻转", page.eval_on_selector("#flashcard", "el=>el.classList.contains('flip')"))
    page.click("#card-known-btn")
    check("记住计数+1", page.inner_text("#card-known") == "1", page.inner_text("#card-known"))

    # 6 术语表过滤
    page.goto(URL + "#/book/clrs/glossary")
    page.wait_for_timeout(700)
    total = page.eval_on_selector_all("#glossary-list li", "els=>els.length")
    term = page.inner_text("#glossary-list li").split("—")[0].strip()[:6]
    page.fill("#glossary-filter", term)
    page.wait_for_timeout(300)
    visible = page.eval_on_selector_all("#glossary-list li", "els=>els.filter(e=>e.style.display!=='none').length")
    check("术语表过滤", total > 0 and 0 < visible <= total, f"共{total}，过滤后{visible}（词:{term}）")

    # 7 全局搜索
    page.goto(URL + "#/cross/readme")
    page.wait_for_timeout(600)
    page.fill("#q", "动态规划")
    page.wait_for_timeout(600)
    hits = page.eval_on_selector_all(".search-hit", "els=>els.length")
    check("全局搜索命中", hits > 0, f"{hits} 条")

    # 8 进度持久（访问两章后刷新）
    page.goto(URL + "#/book/fourth/chapter/ch01a")
    page.wait_for_timeout(600)
    page.goto(URL + "#/book/fourth/chapter/ch01b")
    page.wait_for_timeout(600)
    page.goto(URL + "#/book/fourth/path")
    page.wait_for_timeout(400)
    label = page.inner_text("#progress-label")
    page.reload()
    page.wait_for_timeout(800)
    label2 = page.inner_text("#progress-label")
    check("进度跨刷新持久", "8%" in label2, label2)
    check("学习路径已标记完成", "已完成" in page.inner_text("#view"), "")

    # 9 深色模式
    page.click("#theme-btn")
    check("深色模式", page.eval_on_selector("body", "el=>el.dataset.theme") == "dark")

    # 10 四本书抽查章节全渲染
    for book, ch in (("hello", "ch05"), ("tujie", "ch04"), ("fourth", "ch02a"), ("clrs", "ch23")):
        page.goto(URL + f"#/book/{book}/chapter/{ch}")
        page.wait_for_timeout(600)
        txt = page.inner_text("#view")
        check(f"{book}/{ch} 渲染", len(txt) > 300, f"{len(txt)} 字符")

    # 11 单独伴侣链接编码
    page.goto(URL + "#/book/hello/path")
    page.wait_for_timeout(500)
    href = page.eval_on_selector_all("#nav .nav-item", "els=>{const e=els.find(x=>x.textContent.includes('单独打开')); return e?e.getAttribute('href'):null}")
    check("单独伴侣链接", href and "01-hello" in href, str(href)[:60])

    # 12 控制台错误
    check("控制台无错误", len(errors) == 0, " || ".join(errors[:6]))

    browser.close()

ok = sum(1 for _, v, _ in results if v)
print(f"\n=== 结果：{ok}/{len(results)} 通过 ===")
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "verify_report.json"), "w", encoding="utf-8") as f:
    json.dump([{"check": n, "pass": v, "extra": e} for n, v, e in results], f, ensure_ascii=False, indent=1)

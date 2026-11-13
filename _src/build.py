"""neatlab.app 정적 사이트 생성기.

_src/strings/<lang>.json(화면 문구)과 _src/privacy/<lang>.txt(처리방침 원문)로
언어별 페이지를 만든다. 영어는 기본 주소(/, /rollkeep/ ...), 그 밖의 언어는
같은 페이지 아래 /<lang>/ 하위 폴더(/ko/, /rollkeep/privacy/ja/ ...)에 둔다.
영어 페이지는 처음 방문 시 브라우저 언어를 보고 해당 언어 페이지로 이동한다
(언어 선택 메뉴에서 고른 언어는 localStorage 에 기억해 자동 이동보다 우선).

실행: python _src/build.py   (저장소 루트 어디서든)
"""
import html, io, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "_src")
SITE = "https://neatlab.app"
EMAIL = "support@neatlab.app"

# 언어 선택 메뉴 순서(영어 먼저, 그다음 아시아, 유럽은 자국어 이름 가나다/알파벳 순은 아님 — 사용 인구 순 대략)
LANG_ORDER = ["en", "ko", "ja", "zh-hans", "zh-hant",
              "de", "fr", "es", "it", "pt", "nl", "pl", "sv", "da", "nb", "fi",
              "cs", "sk", "hu", "ro", "bg", "el", "hr", "sl", "et", "lv", "lt", "ga", "mt", "uk"]

# 페이지: (키, 영어 경로)
PAGES = [("home", ""), ("rollkeep", "rollkeep/"), ("support", "rollkeep/support/"), ("privacy", "rollkeep/privacy/")]


def load_langs():
    langs = {}
    for code in LANG_ORDER:
        sp = os.path.join(SRC, "strings", f"{code}.json")
        pp = os.path.join(SRC, "privacy", f"{code}.txt")
        if os.path.exists(sp) and os.path.exists(pp):
            langs[code] = {"s": json.load(io.open(sp, encoding="utf-8")),
                           "p": io.open(pp, encoding="utf-8").read()}
    return langs


def url(page_path, code):
    return "/" + page_path + ("" if code == "en" else f"{code}/")


def esc(s):
    return html.escape(s, quote=True)


def linkify(s):
    s = esc(s)
    s = re.sub(r"(https://[^\s,)）」」，。]+)", r'<a href="\1">\1</a>', s)
    s = s.replace(EMAIL, f'<a href="mailto:{EMAIL}">{EMAIL}</a>')
    return s


def render_policy(text):
    lines = text.strip("\n").split("\n")
    title, body, out, inlist = lines[0].strip(), lines[1:], [], False
    for ln in body:
        s = ln.strip()
        if not s:
            if inlist:
                out.append("</ul>"); inlist = False
            continue
        if s.startswith("- "):
            if not inlist:
                out.append("<ul>"); inlist = True
            out.append(f"<li>{linkify(s[2:])}</li>"); continue
        if inlist:
            out.append("</ul>"); inlist = False
        if re.match(r"^\d{1,2}\.\s*\S", s) and len(s) < 90:
            out.append(f"<h2>{linkify(s)}</h2>")
        elif "2026-11-13" in s and len(s) < 60:
            out.append(f'<p class="muted">{linkify(s)}</p>')
        else:
            out.append(f"<p>{linkify(s)}</p>")
    if inlist:
        out.append("</ul>")
    return title, "\n".join(out)


REDIRECT_JS = """<script>
(function(){
  var avail=%(avail)s, base=%(base)s;
  if(/bot|crawl|spider|slurp|preview/i.test(navigator.userAgent))return;
  var saved=null; try{saved=localStorage.getItem('nl_lang');}catch(e){}
  function pick(){
    if(saved&&(saved==='en'||avail.indexOf(saved)>=0))return saved;
    var ls=navigator.languages&&navigator.languages.length?navigator.languages:[navigator.language||'en'];
    for(var i=0;i<ls.length;i++){
      var l=(ls[i]||'').toLowerCase();
      if(l.indexOf('zh')===0)return /hant|-tw|-hk|-mo/.test(l)?'zh-hant':'zh-hans';
      var p=l.split('-')[0];
      if(p==='no'||p==='nn')p='nb';
      if(p==='en')return 'en';
      if(avail.indexOf(p)>=0)return p;
    }
    return 'en';
  }
  var t=pick();
  if(t!=='en')location.replace(base+t+'/'+location.hash);
})();
</script>"""

SELECT_JS = """<script>
document.getElementById('lang').addEventListener('change',function(e){
  var o=e.target.selectedOptions[0]; try{localStorage.setItem('nl_lang',o.dataset.code);}catch(_){}
  location.href=o.value;
});
</script>"""


def page_html(code, langs, page_key, page_path, title, meta, main_html, policy_note=False):
    s = langs[code]["s"]
    hreflang = "\n".join(
        f'<link rel="alternate" hreflang="{esc(langs[c]["s"]["_html_lang"])}" href="{SITE}{url(page_path, c)}">' for c in langs)
    hreflang += f'\n<link rel="alternate" hreflang="x-default" href="{SITE}{url(page_path, "en")}">'
    opts = "".join(
        f'<option value="{url(page_path, c)}" data-code="{c}"{" selected" if c == code else ""}>{esc(langs[c]["s"]["_lang_name"])}</option>'
        for c in langs)
    redirect = ""
    if code == "en":
        redirect = REDIRECT_JS % {"avail": json.dumps([c for c in langs if c != "en"]), "base": json.dumps("/" + page_path)}
    note = f'<p class="notice">{esc(s["translation_note"])}</p>' if (policy_note and code != "en") else ""
    return f"""<!doctype html>
<html lang="{esc(s['_html_lang'])}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(meta)}">
<link rel="canonical" href="{SITE}{url(page_path, code)}">
{hreflang}
<link rel="icon" href="/assets/favicon.png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="stylesheet" href="/assets/style.css">
{redirect}
</head>
<body>
<header class="site"><div class="wrap">
  <a class="brand" href="{url('', code)}">neat<span>lab</span></a>
  <label class="lang"><span class="sr">{esc(s['nav_language'])}</span>
    <select id="lang" aria-label="{esc(s['nav_language'])}">{opts}</select></label>
</div></header>
<main{' class="policy"' if page_key == 'privacy' else ''}><div class="wrap">
{note}{main_html}
</div></main>
<footer class="site"><div class="wrap">
  <a href="{url('rollkeep/', code)}">{esc(s['link_rollkeep'])}</a><a href="{url('rollkeep/support/', code)}">{esc(s['link_support'])}</a><a href="{url('rollkeep/privacy/', code)}">{esc(s['link_privacy'])}</a>
  <div>{esc(s['footer_copyright'])}</div>
</div></footer>
{SELECT_JS}
</body>
</html>
"""


def build_page(code, langs, key, path):
    s = langs[code]["s"]
    u = lambda p: url(p, code)
    mail = f'<a href="mailto:{EMAIL}">{EMAIL}</a>'
    if key == "home":
        main = f"""<h1>{esc(s['home_h1'])}</h1>
<p class="lede">{esc(s['home_lede'])}</p>
<div class="film" aria-hidden="true"></div>
<h2>{esc(s['home_apps'])}</h2>
<a class="card" href="{u('rollkeep/')}">
  <img src="/assets/rollkeep-icon.png" alt="" width="72" height="72">
  <div><b>Rollkeep</b><span>{esc(s['home_rollkeep_tagline'])}</span></div>
</a>
<h2>{esc(s['home_contact'])}</h2>
<p>{mail}</p>"""
        return page_html(code, langs, key, path, s["home_title"], s["home_meta"], main)
    if key == "rollkeep":
        pts = "".join(f"<div><b>{esc(s[f'rk_p{i}_t'])}</b>{esc(s[f'rk_p{i}_d'])}</div>" for i in range(1, 6))
        main = f"""<img src="/assets/rollkeep-icon.png" alt="{esc(s['rk_icon_alt'])}" width="88" height="88" class="appicon">
<h1>Rollkeep</h1>
<p class="lede">{esc(s['rk_lede'])}</p>
<p><span class="pill">{esc(s['rk_soon'])}</span></p>
<div class="points">{pts}</div>
<div class="btns">
  <a class="btn" href="{u('rollkeep/support/')}">{esc(s['link_support'])}</a>
  <a class="btn" href="{u('rollkeep/privacy/')}">{esc(s['link_privacy'])}</a>
</div>"""
        return page_html(code, langs, key, path, s["rk_title"], s["rk_meta"], main)
    if key == "support":
        lede = esc(s["sup_lede"]).replace("{email}", mail)
        faq = "".join(f"<h3>{esc(s[f'sup_q{i}'])}</h3>\n<p>{esc(s[f'sup_a{i}'])}</p>\n" for i in range(1, 7))
        main = f"""<h1>{esc(s['sup_title'])}</h1>
<p class="lede">{lede}</p>
<h2>{esc(s['sup_faq'])}</h2>
{faq}<p class="muted"><a href="{u('rollkeep/privacy/')}">{esc(s['link_privacy'])}</a></p>"""
        return page_html(code, langs, key, path, s["sup_title"], s["sup_meta"], main)
    if key == "privacy":
        title, body = render_policy(langs[code]["p"])
        main = f"<h1>{esc(title)}</h1>\n{body}"
        return page_html(code, langs, key, path, title, title, main, policy_note=True)


def main():
    langs = load_langs()
    written = 0
    for key, path in PAGES:
        for code in langs:
            out_dir = os.path.join(ROOT, path, "" if code == "en" else code)
            os.makedirs(out_dir, exist_ok=True)
            io.open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8", newline="\n").write(build_page(code, langs, key, path))
            written += 1
    # 404
    s = langs["en"]["s"]
    io.open(os.path.join(ROOT, "404.html"), "w", encoding="utf-8", newline="\n").write(
        f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(s['nf_title'])} · Neatlab</title><link rel="stylesheet" href="/assets/style.css"></head>
<body><header class="site"><div class="wrap"><a class="brand" href="/">neat<span>lab</span></a></div></header>
<main><div class="wrap"><h1>{esc(s['nf_title'])}</h1><p class="lede"><a href="/">Neatlab</a> · <a href="/rollkeep/">Rollkeep</a></p></div></main></body></html>
""")
    # sitemap
    urls = [f"{SITE}{url(p, c)}" for _, p in PAGES for c in langs]
    io.open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8", newline="\n").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    print(f"languages: {len(langs)} {list(langs)}")
    print(f"pages written: {written}")
    missing = [c for c in LANG_ORDER if c not in langs]
    if missing:
        print("not yet translated (skipped):", missing)


if __name__ == "__main__":
    main()

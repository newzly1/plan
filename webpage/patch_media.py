# -*- coding: utf-8 -*-
"""Fill the 12 image misses: re-download failed ones; re-query the no-candidate ones with better terms."""
import json, os, subprocess, urllib.parse
BUILD = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(BUILD, "raw")
UA = "BaliTripPlanner/1.0 (personal trip research; mail2zhangly@gmail.com)"
cand = json.load(open(os.path.join(BUILD, "candidates.json")))

def curl_bytes(url, t=40):
    return subprocess.run(["curl","-s","--max-time",str(t),"-A",UA,"-L",url], capture_output=True).stdout
def curl_dl(url, out, t=50):
    subprocess.run(["curl","-s","--max-time",str(t),"-A",UA,"-L","--retry","3","--retry-delay","1","-o",out,url])
    return os.path.exists(out) and os.path.getsize(out) > 3000

BAD = ("map","locator","location","diagram","flag","coat of arms","svg","logo")
def ok_title(t): return not (t.lower().endswith(".svg") or any(b in t.lower() for b in BAD))
def search(term, n=6, w=1000):
    q={"action":"query","generator":"search","gsrsearch":term,"gsrnamespace":"6","gsrlimit":str(n),
       "prop":"imageinfo","iiprop":"url|mime","iiurlwidth":str(w),"format":"json"}
    try: d=json.loads(curl_bytes("https://commons.wikimedia.org/w/api.php?"+urllib.parse.urlencode(q)))
    except Exception: return []
    out=[]
    for p in d.get("query",{}).get("pages",{}).values():
        ii=(p.get("imageinfo") or [{}])[0]; m=ii.get("mime","")
        if m.startswith("image") and m not in ("image/svg+xml","image/gif") and ok_title(p.get("title","")):
            out.append({"title":p["title"],"thumb":ii.get("thumburl"),"index":p.get("index",99)})
    out.sort(key=lambda x:x["index"]); return out

# 1) had-candidate, download failed -> retry existing candidates
for sid in ["A2c","A2e","A4b","C3a"]:
    done=False
    for c in (cand.get(sid,{}).get("cands") or [])[:3]:
        if c.get("thumb") and curl_dl(c["thumb"], os.path.join(RAW,sid+".img")):
            print(f"{sid} REDL OK  {c['title']}"); done=True; break
    if not done: print(f"{sid} REDL FAIL")

# 2) no-candidate -> better queries
better={"A2d":"Bali swing","A3e":"Tulamben shipwreck Liberty","A4d":"Danau Buyan Bali lake",
        "A4e":"Banyumala waterfall","B3c":"Nusa Ceningan","C1b":"Gili Meno underwater sculpture",
        "D1d":"Kelor island Komodo","D2a":"Pinisi boat Indonesia"}
for sid,q in better.items():
    res=search(q)
    if not res: print(f"{sid} STILL NONE ({q})"); continue
    cand[sid]["cands"]=res
    got=False
    for c in res[:3]:
        if c.get("thumb") and curl_dl(c["thumb"], os.path.join(RAW,sid+".img")):
            print(f"{sid} NEW  OK  [{q}] -> {c['title']}"); got=True; break
    if not got: print(f"{sid} NEW  FAIL ({q})")

json.dump(cand, open(os.path.join(BUILD,"candidates.json"),"w"), ensure_ascii=False, indent=1)
print("done. root uid:", os.getuid())

# -*- coding: utf-8 -*-
"""Apply chosen replacement images (B2a,B3c,C3a) into raw/; re-hunt D2a phinisi and build a D2a options sheet."""
import json, os, shutil, subprocess, urllib.parse
from PIL import Image, ImageDraw, ImageFont, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
BUILD = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(BUILD,"raw"); OPT = os.path.join(BUILD,"opt")
UA = "BaliTripPlanner/1.0 (personal trip research; mail2zhangly@gmail.com)"
cand = json.load(open(os.path.join(BUILD,"candidates.json"))); opt = json.load(open(os.path.join(BUILD,"opt.json")))

CHOSEN = {"B2a":2, "B3c":1, "C3a":2}
for sid,i in CHOSEN.items():
    shutil.copyfile(os.path.join(OPT,f"{sid}_{i}.img"), os.path.join(RAW,f"{sid}.img"))
    cand[sid]["cands"] = [opt[sid][i]] + (cand.get(sid,{}).get("cands") or [])
    print("applied", sid, "<-", opt[sid][i]["title"])

def cb(url,t=40): return subprocess.run(["curl","-s","--max-time",str(t),"-A",UA,"-L",url],capture_output=True).stdout
def dl(url,out,t=45): subprocess.run(["curl","-s","--max-time",str(t),"-A",UA,"-L","--retry","2","-o",out,url]); return os.path.exists(out) and os.path.getsize(out)>3000
BAD=("map","locator","diagram","flag","svg","logo","engraving","lithograph","1800","181","185","186","187","188","189","190")
def okt(t): return not(t.lower().endswith(".svg") or any(b in t.lower() for b in BAD))
def search(term,n=8,w=900):
    q={"action":"query","generator":"search","gsrsearch":term,"gsrnamespace":"6","gsrlimit":str(n),"prop":"imageinfo","iiprop":"url|mime","iiurlwidth":str(w),"format":"json"}
    try: d=json.loads(cb("https://commons.wikimedia.org/w/api.php?"+urllib.parse.urlencode(q)))
    except Exception: return []
    o=[]
    for p in d.get("query",{}).get("pages",{}).values():
        ii=(p.get("imageinfo") or [{}])[0]; m=ii.get("mime","")
        if m.startswith("image") and m not in("image/svg+xml","image/gif") and okt(p.get("title","")):
            o.append({"title":p["title"],"thumb":ii.get("thumburl"),"index":p.get("index",99)})
    o.sort(key=lambda x:x["index"]); return o

d2a=[]; seen=set()
for q in ["Pinisi Komodo","Phinisi Labuan Bajo","Komodo National Park tourist boat","Kelor island boat Komodo","liveaboard boat Raja Ampat","Pinisi Bira boat"]:
    for c in search(q):
        if c["title"] in seen or not c["thumb"]: continue
        seen.add(c["title"]); d2a.append((q,c))
        if len(d2a)>=6: break
    if len(d2a)>=6: break
for i,(q,c) in enumerate(d2a): dl(c["thumb"], os.path.join(OPT,f"D2a_{i}.img"))
opt["D2a_new"]=[{"q":q,**c} for q,c in d2a]
json.dump(opt, open(os.path.join(BUILD,"opt.json"),"w"), ensure_ascii=False, indent=1)
json.dump(cand, open(os.path.join(BUILD,"candidates.json"),"w"), ensure_ascii=False, indent=1)
print("D2a opts:", [(q,c["title"].replace("File:","")[:36]) for q,c in d2a])

FONT=next((fp for fp in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"] if os.path.exists(fp)),None)
def font(s):
    try: return ImageFont.truetype(FONT,s)
    except Exception: return ImageFont.load_default()
CW,IH,LH=300,200,42; COLS=3; rows=max(1,(len(d2a)+COLS-1)//COLS)
sh=Image.new("RGB",(COLS*CW,rows*(IH+LH)),(20,20,24)); dr=ImageDraw.Draw(sh)
for i,(q,c) in enumerate(d2a):
    r,cc=divmod(i,COLS); x0,y0=cc*CW,r*(IH+LH)
    p=os.path.join(OPT,f"D2a_{i}.img")
    if os.path.exists(p) and os.path.getsize(p)>3000:
        try: im=Image.open(p).convert("RGB"); im.thumbnail((CW-10,IH-10)); sh.paste(im,(x0+(CW-im.width)//2,y0+(IH-im.height)//2))
        except Exception: pass
    dr.text((x0+6,y0+IH+2),f"D2a #{i}",font=font(17),fill=(255,225,130))
    dr.text((x0+6,y0+IH+22),c["title"].replace("File:","")[:34],font=font(11),fill=(170,170,182))
sh.save(os.path.join(BUILD,"sheets","d2a.jpg"),"JPEG",quality=84)
print("wrote d2a.jpg", sh.size)

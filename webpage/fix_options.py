# -*- coding: utf-8 -*-
"""Fetch several candidate options for the problem spots and lay them out as a labeled options sheet."""
import json, os, subprocess, urllib.parse, math
from PIL import Image, ImageDraw, ImageFont, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
BUILD = os.path.dirname(os.path.abspath(__file__)); OPT = os.path.join(BUILD,"opt"); os.makedirs(OPT, exist_ok=True)
UA = "BaliTripPlanner/1.0 (personal trip research; mail2zhangly@gmail.com)"

def cb(url,t=40): return subprocess.run(["curl","-s","--max-time",str(t),"-A",UA,"-L",url],capture_output=True).stdout
def dl(url,out,t=45):
    subprocess.run(["curl","-s","--max-time",str(t),"-A",UA,"-L","--retry","2","-o",out,url]); return os.path.exists(out) and os.path.getsize(out)>3000
BAD=("map","locator","diagram","flag","svg","logo")
def okt(t): return not(t.lower().endswith(".svg") or any(b in t.lower() for b in BAD))
def search(term,n=6,w=900):
    q={"action":"query","generator":"search","gsrsearch":term,"gsrnamespace":"6","gsrlimit":str(n),
       "prop":"imageinfo","iiprop":"url|mime","iiurlwidth":str(w),"format":"json"}
    try:d=json.loads(cb("https://commons.wikimedia.org/w/api.php?"+urllib.parse.urlencode(q)))
    except Exception:return []
    o=[]
    for p in d.get("query",{}).get("pages",{}).values():
        ii=(p.get("imageinfo") or [{}])[0];m=ii.get("mime","")
        if m.startswith("image") and m not in("image/svg+xml","image/gif") and okt(p.get("title","")):
            o.append({"title":p["title"],"thumb":ii.get("thumburl"),"index":p.get("index",99)})
    o.sort(key=lambda x:x["index"]);return o

# spot -> list of queries (gather candidates across all)
FIX={
 "B2a":["manta ray diving ocean","reef manta ray snorkeling"],
 "B3c":["Nusa Ceningan blue lagoon","Dream Beach Nusa Lembongan"],
 "C3a":["Tanjung Aan beach Lombok aerial","Tanjung Aan"],
 "D2a":["Pinisi ship sailing Komodo","phinisi boat Labuan Bajo Raja Ampat"],
 "C1c":["sea turtle snorkeling reef","Gili Trawangan snorkeling"],
}
opts={}
for sid,queries in FIX.items():
    cands=[];seen=set()
    for q in queries:
        for c in search(q):
            if c["title"] in seen or not c["thumb"]:continue
            seen.add(c["title"]);cands.append(c)
            if len(cands)>=4:break
        if len(cands)>=4:break
    opts[sid]=cands
    for i,c in enumerate(cands): dl(c["thumb"], os.path.join(OPT,f"{sid}_{i}.img"))
    print(sid, [c["title"].replace("File:","")[:40] for c in cands])
json.dump(opts, open(os.path.join(BUILD,"opt.json"),"w"), ensure_ascii=False, indent=1)

# build options sheet: each row = one spot, its options across columns
FONT=None
for fp in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
    if os.path.exists(fp):FONT=fp;break
def font(s):
    try:return ImageFont.truetype(FONT,s)
    except Exception:return ImageFont.load_default()
CW,IH,LH=300,200,40; COLS=4
rows=len(FIX)
sheet=Image.new("RGB",(COLS*CW,rows*(IH+LH)),(20,20,24)); d=ImageDraw.Draw(sheet)
for r,(sid,cands) in enumerate(opts.items()):
    for i in range(COLS):
        x0,y0=i*CW,r*(IH+LH)
        p=os.path.join(OPT,f"{sid}_{i}.img")
        if os.path.exists(p) and os.path.getsize(p)>3000:
            try:
                im=Image.open(p).convert("RGB");im.thumbnail((CW-10,IH-10))
                sheet.paste(im,(x0+(CW-im.width)//2,y0+(IH-im.height)//2))
            except Exception:pass
        d.text((x0+6,y0+IH+2),f"{sid} #{i}",font=font(17),fill=(255,225,130))
        t=(cands[i]["title"].replace("File:","")[:34]) if i<len(cands) else "—"
        d.text((x0+6,y0+IH+22),t,font=font(11),fill=(170,170,182))
sheet.save(os.path.join(BUILD,"sheets","options.jpg"),"JPEG",quality=84)
print("wrote options.jpg", sheet.size)

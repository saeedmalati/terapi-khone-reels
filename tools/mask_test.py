import asyncio, sys
from playwright.async_api import async_playwright
from PIL import Image, ImageChops
import os
F=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","template","reel-video","assets","fonts"); S="/tmp"
lines=["چون خودمو","بیشتر دوست داشتم","یاد گرفتم","دیده نمی‌شدم","التماس کردن نیست","شب‌های بی‌خوابی"]
fonts=[("Nastaliq",400),("Nastaliq",700),("Gulzar",400),("Ruqaa",400),("Ruqaa",700)]
def page(css, mask):
    ff="".join(f'@font-face{{font-family:"{n}";font-weight:{w};src:url("file://{F}/{n.lower()}-{w}.woff2")}}' for n,w in fonts)
    body="".join(f'<div class="stack" style="font-family:{n};font-weight:{w}">'+"".join(f'<span class="ink">{l}</span>' for l in lines)+'</div>' for n,w in fonts)
    m='-webkit-mask-image:linear-gradient(to left,#000 calc(var(--p) - 10%),rgba(0,0,0,0) var(--p));' if mask else ''
    return f'<html><head><style>{ff}*{{margin:0;padding:0;box-sizing:border-box}}body{{background:#000;color:#fff;direction:rtl;width:2400px;display:flex;flex-wrap:wrap;gap:40px;padding:80px}}.stack{{display:flex;flex-direction:column;align-items:center;gap:.62em;font-size:88px;line-height:1.9}}.ink{{display:inline-block;--p:112%;{css}{m}}}</style></head><body>{body}</body></html>'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(viewport={"width":2400,"height":3200})
        res={}
        for name,css in [("old","padding:0 14px;"),("new","padding:.7em .45em;margin:-.7em -.45em;")]:
            imgs=[]
            for mask in (False,True):
                open(f"{S}/t.html","w").write(page(css,mask)); await pg.goto(f"file://{S}/t.html"); await pg.evaluate("document.fonts.ready"); await pg.wait_for_timeout(500)
                f=f"{S}/{name}{int(mask)}.png"; await pg.screenshot(path=f,full_page=True); imgs.append(Image.open(f).convert("L"))
            d=ImageChops.difference(*imgs); px=sum(1 for v in d.get_flattened_data() if v>60)
            print(name,"pixels lost to mask:",px)
        await b.close()
asyncio.run(main())

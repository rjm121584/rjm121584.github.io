from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont
from pathlib import Path
import base64, math

ROOT=Path(__file__).resolve().parent
ASSETS=ROOT/"assets"
OUT=ASSETS/"Velvet-Solitaire-Feature-Graphic-1024x500.png"

def decode_b64(src, dst):
    dst.write_bytes(base64.b64decode(src.read_text().strip()))

logo_src=ASSETS/"current_velvet_logo.webp"
icon_src=ASSETS/"current_velvet_icon.webp"
decode_b64(ASSETS/"current_velvet_logo.webp.b64", logo_src)
decode_b64(ASSETS/"current_velvet_icon.webp.b64", icon_src)

# Reproduce the current v80 board-logo extraction from the approved newer source.
src=Image.open(logo_src).convert("RGB")
region=src.crop((4,12,350,160)).convert("RGBA")
pix=region.load()
mask=Image.new("L", region.size, 0)
mp=mask.load()
for y in range(region.height):
    for x in range(region.width):
        r,g,b,a=pix[x,y]
        lum=.299*r+.587*g+.114*b
        warm=(r>72 and g>42 and r>b*1.16 and (r-b)>24)
        bright=lum>132
        mid_gold=(r>100 and g>68 and b<105 and r>g*1.05)
        mp[x,y]=255 if (warm or bright or mid_gold) else 0
mask=mask.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(.55))
region.putalpha(mask)
box=region.getbbox()
if not box:
    raise SystemExit("Current logo extraction produced no visible artwork")
l,t,r,b=box
pad=7
region=region.crop((max(0,l-pad),max(0,t-pad),min(region.width,r+pad),min(region.height,b+pad)))
alpha=region.getchannel("A")
shadow_a=alpha.filter(ImageFilter.GaussianBlur(1.35))
shadow=Image.new("RGBA",region.size,(0,0,0,0))
shadow.putalpha(shadow_a.point(lambda v:int(v*.32)))
logo=Image.new("RGBA",(region.width+8,region.height+8),(0,0,0,0))
logo.alpha_composite(shadow,(3,3))
logo.alpha_composite(region,(0,0))

# Exact v154 icon bytes, only scaled.
icon=Image.open(icon_src).convert("RGBA")

W,H=1024,500
img=Image.new("RGBA",(W,H),(3,18,13,255))
p=img.load()

# Deep velvet green gradient with subtle folds.
for y in range(H):
    for x in range(W):
        gx=x/(W-1); gy=y/(H-1)
        center=max(0.0,1.0-math.sqrt(((x-500)/720)**2+((y-250)/390)**2))
        r=int(3+5*gx+2*center)
        g=int(18+14*gx+15*center)
        b=int(13+6*gx+4*center)
        p[x,y]=(r,g,b,255)

fold=Image.new("RGBA",(W,H),(0,0,0,0))
fd=ImageDraw.Draw(fold)
for y0,a in [(75,32),(225,25),(385,28)]:
    fd.arc((-240,y0-150,760,y0+180),200,345,fill=(42,105,76,a),width=34)
for y0,a in [(155,24),(315,20)]:
    fd.arc((200,y0-130,1180,y0+190),15,165,fill=(0,0,0,a),width=45)
fold=fold.filter(ImageFilter.GaussianBlur(28))
img=Image.alpha_composite(img,fold)

# Soft left shadow for branding.
shade=Image.new("RGBA",(W,H),(0,0,0,0))
sd=ImageDraw.Draw(shade)
for x in range(600):
    t=x/600
    sd.line((x,0,x,H),fill=(0,0,0,int(90*(1-t)**1.7)))
img=Image.alpha_composite(img,shade)

draw=ImageDraw.Draw(img)

# Gold frame accents.
gold=(222,181,93,230)
soft_gold=(180,137,64,150)
draw.rounded_rectangle((22,22,W-22,H-22),radius=24,outline=soft_gold,width=2)
draw.line((40,455,392,455),fill=gold,width=2)

# Exact icon.
icon_sz=132
ic=icon.resize((icon_sz,icon_sz),Image.Resampling.LANCZOS)
ish=Image.new("RGBA",ic.size,(0,0,0,160))
ish.putalpha(ic.getchannel("A").filter(ImageFilter.GaussianBlur(8)))
img.alpha_composite(ish,(63,51))
img.alpha_composite(ic,(56,44))

# Current in-game wordmark/logo, scaled only.
target_w=405
target_h=round(logo.height*target_w/logo.width)
lg=logo.resize((target_w,target_h),Image.Resampling.LANCZOS)
lsh=Image.new("RGBA",lg.size,(0,0,0,150))
lsh.putalpha(lg.getchannel("A").filter(ImageFilter.GaussianBlur(6)))
img.alpha_composite(lsh,(42,231))
img.alpha_composite(lg,(34,222))

# Decorative suit jewels below branding.
for i,(cx,cy) in enumerate([(95,432),(116,432),(137,432)]):
    rr=5 if i!=1 else 8
    draw.polygon([(cx,cy-rr),(cx+rr,cy),(cx,cy+rr),(cx-rr,cy)],fill=gold)

# Right-side solitaire tableau.
try:
    font_big=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",31)
    font_small=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",22)
except:
    font_big=ImageFont.load_default()
    font_small=ImageFont.load_default()

def card_back(x,y,w=112,h=156,angle=0):
    c=Image.new("RGBA",(w+24,h+24),(0,0,0,0))
    d=ImageDraw.Draw(c)
    d.rounded_rectangle((8,8,8+w,8+h),radius=10,fill=(8,26,52,255),outline=(218,174,80,255),width=3)
    d.rounded_rectangle((17,17,8+w-9,8+h-9),radius=7,outline=(182,137,57,220),width=2)
    d.polygon([(8+w//2,38),(8+w//2+14,58),(8+w//2,78),(8+w//2-14,58)],fill=(211,164,73,230))
    if angle:
        c=c.rotate(angle,resample=Image.Resampling.BICUBIC,expand=True)
    img.alpha_composite(c,(x,y))

def face_card(x,y,rank,suit,red=False,w=118,h=166,angle=0):
    c=Image.new("RGBA",(w+30,h+30),(0,0,0,0))
    d=ImageDraw.Draw(c)
    d.rounded_rectangle((10,10,10+w,10+h),radius=11,fill=(250,246,232,255),outline=(216,177,91,255),width=3)
    col=(178,35,41,255) if red else (25,27,29,255)
    d.text((20,16),rank,font=font_big,fill=col)
    d.text((22,50),suit,font=font_big,fill=col)
    # center suit
    bbox=d.textbbox((0,0),suit,font=font_big)
    sw=bbox[2]-bbox[0]; sh=bbox[3]-bbox[1]
    d.text((10+w/2-sw/2,10+h/2-sh/2),suit,font=font_big,fill=col)
    if angle:
        c=c.rotate(angle,resample=Image.Resampling.BICUBIC,expand=True)
    img.alpha_composite(c,(x,y))

# stacked backs
for x0,count in [(565,3),(690,4),(815,5)]:
    for n in range(count):
        card_back(x0,y=55+n*18,w=104,h=145,angle=0)

# face-up cards
face_card(548,145,"A","♥",True,w=112,h=158,angle=-4)
face_card(675,177,"K","♠",False,w=116,h=164,angle=3)
face_card(800,208,"8","♦",True,w=116,h=164,angle=5)

# foreground fan
face_card(595,306,"J","♣",False,w=108,h=150,angle=-9)
face_card(680,303,"Q","♥",True,w=110,h=154,angle=2)
face_card(767,300,"K","♠",False,w=112,h=158,angle=10)

# Add subtle warm light on right.
glow=Image.new("RGBA",(W,H),(0,0,0,0))
gp=glow.load()
for y in range(H):
    for x in range(W):
        d=((x-850)/330)**2+((y-205)/260)**2
        if d<1:
            a=int(42*(1-d))
            gp[x,y]=(255,199,83,a)
img=Image.alpha_composite(img,glow)

# Edge vignette.
vig=Image.new("RGBA",(W,H),(0,0,0,0))
vp=vig.load()
cx,cy=W/2,H/2
md=math.sqrt(cx*cx+cy*cy)
for y in range(H):
    for x in range(W):
        d=math.sqrt((x-cx)**2+(y-cy)**2)/md
        a=int(72*max(0,(d-.55)/.45))
        vp[x,y]=(0,0,0,a)
img=Image.alpha_composite(img,vig)

OUT.parent.mkdir(parents=True,exist_ok=True)
img.convert("RGB").save(OUT,"PNG",optimize=True)
print(OUT, OUT.stat().st_size)

# trigger store asset build

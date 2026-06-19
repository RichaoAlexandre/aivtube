"""Build a layered Live2D-ready PSD from a flat AGI-chan design.

Pipeline (no Cubism needed — this is the Linux art-prep side):
  1. remove the solid-white background (flood-fill from corners) -> transparent
  2. isolate the yellow smiley mask as its own layer; clear it from the base
  3. write a 2-layer PSD (character + mask) with pytoshop (raw compression)

Usage: python tools/build_model_psd.py assets/design/agichan_v4_00001_.png assets/AGI-chan.psd
Deps (comfy venv has them): numpy, opencv-python, pillow, pytoshop
"""
import sys, numpy as np, cv2
from PIL import Image
import pytoshop
from pytoshop.user import nested_layers
from pytoshop import enums

src=sys.argv[1] if len(sys.argv)>1 else "assets/design/agichan_v4_00001_.png"
out=sys.argv[2] if len(sys.argv)>2 else "assets/AGI-chan.psd"
img=cv2.imread(src, cv2.IMREAD_COLOR); h,w=img.shape[:2]

# 1) background -> alpha via flood fill from the 4 corners (keeps interior whites)
m=np.zeros((h+2,w+2),np.uint8)
for s in [(0,0),(w-1,0),(0,h-1),(w-1,h-1)]:
    cv2.floodFill(img.copy(), m, s, 0, (12,12,12),(12,12,12), 8|(255<<8)|cv2.FLOODFILL_MASK_ONLY)
bg=m[1:-1,1:-1]>0
alpha=cv2.morphologyEx(np.where(bg,0,255).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3,3),np.uint8))

# 2) yellow smiley mask in the top 45%
hsv=cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
ym=cv2.inRange(hsv,(18,80,120),(40,255,255)); ym[int(h*0.45):,:]=0
ym=cv2.morphologyEx(ym, cv2.MORPH_CLOSE, np.ones((9,9),np.uint8))
cnts,_=cv2.findContours(ym, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
blob=np.zeros((h,w),np.uint8)
if cnts:
    cv2.drawContours(blob,[cv2.convexHull(max(cnts,key=cv2.contourArea))],-1,255,-1)
    blob=cv2.dilate(blob,np.ones((5,5),np.uint8))

def bgra(alpha_arr):
    a=cv2.cvtColor(img,cv2.COLOR_BGR2BGRA); a[:,:,3]=alpha_arr; return a
mask_layer=bgra(blob)                       # smiley only
base=bgra(alpha.copy()); base[blob>0]=(0,0,0,0)   # character minus mask region

def to_layer(bgra_arr,name):
    rgba=cv2.cvtColor(bgra_arr, cv2.COLOR_BGRA2RGBA)
    ch={0:rgba[:,:,0].copy(),1:rgba[:,:,1].copy(),2:rgba[:,:,2].copy(),-1:rgba[:,:,3].copy()}
    return nested_layers.Image(name=name,visible=True,top=0,left=0,bottom=h,right=w,channels=ch)

psd=nested_layers.nested_layers_to_psd(
    [to_layer(mask_layer,"mask"), to_layer(base,"character")],
    color_mode=enums.ColorMode.rgb, compression=enums.Compression.raw)
with open(out,"wb") as f: psd.write(f)
print("wrote", out)

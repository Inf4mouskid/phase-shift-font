import os
import re
import sys
import PIL
import string
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from PIL import ImageFilter
from itertools import chain
from fontTools.ttLib import TTFont
from fontTools.unicode import Unicode


def load_font(path):
    ttf = TTFont(path, 0, allowVID=0,
                 ignoreDecompileErrors=True,
                 fontNumber=-1)
    chars = chain.from_iterable([y + (Unicode[y[0]],) for y in x.cmap.items()] for x in ttf["cmap"].tables)
    chars = set(chars)
    chars = sorted(chars,key = lambda c : int(c[0]))
    ttf.close()
    return chars

def convert_ttf(path):
    fontsize=80 #fontsize
    #textures need to be same size as w and h, also RGBA
    w=150 #width of the image before cropping
    h=150 #height of the image before cropping
    wb,hb = 25,30 # x,y coordinates where to draw font, 0,0 being upper-left corner
    #TODO: calculate wb,hb
    left,right = 5,5 #how many pixels to leave to each side when cropping

    base = os.path.basename(path)
    dirs = os.path.splitext(base)[0]
    if not os.path.exists(dirs):
        os.mkdir(dirs)
    chars = load_font(path)
    font = ImageFont.truetype(path,fontsize)

    for c in chars:
        if re.match('.notdef|nonmarkingreturn|.null',c[1]):
            continue
        if c[0] == 32: #space character
            sw,sh = font.getsize(chr(c[0]))
            space = Image.new("RGBA", (sw,sh),(0,0,0,0))
            space.save("%s/%d.png"%(dirs,c[0]))
            continue
        
        z = chr(c[0]) #current character 
        transparent = (0,0,0,0)
        
        #simple one color font with transparent background
        #layer0 = Image.new("RGBA", (w,h),transparent) #transparent background
        #l0 = ImageDraw.Draw(layer0)
        #l0.text((wb,hb),z,(255,255,255,255), font=font)
        
        #bglayer: blurred font
        layer0 = Image.new('RGBA', (w,h), transparent)
        l0 = ImageDraw.Draw(layer0)
        #drawing char 4 times different positions to get bigger blur effect
        color0 = (88,190,226,255)
        l0.text((wb-1,hb),z,color0,font=font)
        l0.text((wb+1,hb),z,color0,font=font)
        l0.text((wb,hb-1),z,color0,font=font)
        l0.text((wb,hb+1),z,color0,font=font)
        layer0 = layer0.filter(ImageFilter.GaussianBlur(8)) #add blur

        #layer1: stroke effect using texture
        layer1 = Image.open("texture2.png") #texture
        layer1_mask = Image.new('RGBA', (w,h), (0,0,0,255)) #mask layer 
        l1 = ImageDraw.Draw(layer1_mask)
        color1 = (0,0,0,0)
        #drawing char 4 times transparent to cut mask layer
        l1.text((wb-1, hb),z,color1,font=font)
        l1.text((wb+1, hb),z,color1,font=font)
        l1.text((wb, hb-1),z,color1,font=font)
        l1.text((wb, hb+1),z,color1,font=font)
        #mask texture
        layer1.paste((0,0,0,0), layer1_mask)
        
        #layer2: font layer with texture
        layer2 = Image.open("texture.png") #texture
        layer2_mask = Image.new('RGBA', (w,h), (0,0,0,255)) #mask layer
        l2 = ImageDraw.Draw(layer2_mask)
        # cutting mask layer
        l2.text((wb, hb),z, transparent, font=font)
        #mask texture
        layer2.paste((0,0,0,0), layer2_mask)

        #merge all layers
        i = Image.alpha_composite(layer0, layer1)
        i = Image.alpha_composite(i, layer2)

        #cropping and saving
        bb = i.getbbox()
        if bb is not None:
            i = i.crop((bb[0]-left,0,bb[2]+right,150))
        i.save("%s/%d.png"%(dirs,c[0]))
        print(z, end='', flush=True)
    print("")

if __name__ == '__main__':
    convert_ttf(sys.argv[1])

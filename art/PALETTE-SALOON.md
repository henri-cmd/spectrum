# Saloon pixel-art style guide (shared by every sprite script)

Render at native pixel resolution (1 image pixel = 1 game pixel), PNG with alpha, no anti-aliasing,
no gradients: flat fills, 1px dark outlines (#15090a) where a shape meets the background, and
1-2 shades of shading per material. The page scales sprites 3x with image-rendering: pixelated.

Palette (use these exact hex values; a sprite may use a subset):
  outline/black   #15090a
  shadow brown    #2a1710
  wood dark       #5a2f1a
  wood mid        #7a4426
  wood light      #9b5a2e
  wood highlight  #b8763a
  wood pale       #d9a066
  cream           #f3e2b4
  tan             #c9a46a
  red             #c8322e
  dark red        #8e1d1d
  pink light      #e9a0a0
  pink mid        #e07070
  sunset orange   #e8792b
  sunset gold     #f2b544
  dusk purple     #5a2a3a
  lamp glow       #ffb347
  gold text       #f0c050
  glass green     #4f6b3a
  skin            #e0a885
  shirt red       #a3241f
  hat dark        #3b2418

Light comes from the upper left (the lamp). Write scripts with Pillow only (PIL.Image, ImageDraw),
set pixels with draw.point / draw.rectangle at integer coordinates, never draw.ellipse with
anti-aliasing. Save to ../assets/<name>.png. Each script must be re-runnable:
  .venv/bin/python art/<script>.py

# Submarine sonar pixel-art style guide (shared by every sonar sprite script)

Same rules as the saloon set: render at native pixel resolution, PNG with alpha, no anti-aliasing,
no gradients, flat fills, 1px dark outlines (#0a0e12) where a shape meets the background, 1-2 shades
of shading per material. The page scales sprites 3x with image-rendering: pixelated.
The room is lit only by instruments: a cold green glow from the sonar scope and warm amber from
the console lamps. Shading is therefore dim, with highlights where screens and lamps are.

Palette (exact hex values; a sprite may use a subset):
  outline/black     #0a0e12
  steel darkest     #121a22
  steel dark        #1b2430
  steel mid         #2b3a4a
  steel light       #3e5266
  steel highlight   #5a7085
  steel pale        #8da2b5
  phosphor darkest  #0c2a1c
  phosphor dark     #145c35
  phosphor mid      #27a85e
  phosphor light    #6cf29b
  phosphor pale     #c8ffd9
  amber             #f0a030
  amber light       #ffd36b
  amber dark        #9a5a12
  alarm red         #d9342b
  dark red          #7a1a14
  brass             #c9a247
  brass dark        #7d5f24
  rubber black      #1e1e22
  skin              #e0a885
  skin shade        #b07a5a
  uniform navy      #22304a
  uniform light     #34496b
  white             #f2f4f6

Write scripts with Pillow only (PIL.Image, ImageDraw), set pixels with draw.point / draw.rectangle
at integer coordinates, draw circles per pixel with integer distance checks, never ImageDraw.ellipse.
Save to assets/sonar/<name>.png. Each script must be re-runnable:  .venv/bin/python art/<script>.py

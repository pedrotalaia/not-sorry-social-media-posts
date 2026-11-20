# ImageMagick 7 recipes

Use these to prepare assets the spec can't express, then place the result as an `image` layer. Always `magick` (v7), never `convert`.

## Cropping & resizing
```bash
magick in.jpg -resize 1080x1350^ -gravity center -extent 1080x1350 out.jpg   # cover crop
magick in.jpg -resize 1080x1350 -background "#fff" -gravity center -extent 1080x1350 out.jpg  # contain/letterbox
magick in.jpg -gravity North -crop 100%x60%+0+0 +repage out.jpg               # keep top 60%
magick in.jpg -auto-orient -strip out.jpg                                     # fix phone EXIF rotation
```

## Color treatments
```bash
magick in.jpg -colorspace Gray -colorspace sRGB out.jpg                       # B&W
magick in.jpg -colorspace Gray \( -size 1x256 gradient:"#F2A541"-"#0E3B43" \) -clut out.jpg   # duotone (light-dark)
magick in.jpg -modulate 100,80,100 -brightness-contrast 5x10 out.jpg          # desaturate + punch
magick in.jpg -fill "#0E3B43" -colorize 25% out.jpg                           # brand tint
magick in.jpg -sigmoidal-contrast 4x50% -modulate 102,90 out.jpg              # soft film look
magick in.jpg \( +clone -blur 0x12 \) -compose Overlay -composite out.jpg     # glow/dreamy
```

## Shapes, masks, cut-outs
```bash
# circle crop (avatar / testimonial)
magick in.jpg -resize 600x600^ -gravity center -extent 600x600 \
  \( -size 600x600 xc:none -fill white -draw "circle 300,300 300,0" \) -compose DstIn -composite avatar.png
# arch / pill shape
magick in.jpg -resize 800x1000^ -gravity center -extent 800x1000 \
  \( -size 800x1000 xc:none -fill white -draw "roundrectangle 0,0 799,1399 400,400" \) -compose DstIn -composite arch.png
# remove flat white background (logos/products on white)
magick logo.jpg -fuzz 8% -transparent white -trim +repage logo.png
# outline/sticker border around a cut-out PNG
magick cut.png \( +clone -alpha extract -morphology Dilate Disk:12 -background white -alpha shape \) +swap -compose over -composite sticker.png
```
Real background removal (people/products on busy backgrounds) isn't an ImageMagick strength: use `uvx rembg i in.jpg out.png` if the user agrees to installing it.

## Text tricks
```bash
magick -list font | grep -i inter                                             # find font names
# rotated vertical label
magick -background none -fill "#111" -font Inter-Bold -pointsize 28 label:"EST. 2019" -rotate -90 label.png
# text with gradient fill
magick -background none -font Inter-Black -pointsize 180 label:"SALE" \
  \( +clone -sparse-color Barycentric '0,0 #F2A541 %w,%h #E63946' \) +swap -compose SrcIn -composite gradtext.png
# outline-only text
magick -background none -fill none -stroke "#111" -strokewidth 3 -font Inter-Black -pointsize 200 label:"NEW" outline.png
# text on a path (circle) is impractical in IM — use an SVG with <textPath> and rasterize: magick -density 300 text.svg out.png
```

## Textures & backgrounds
```bash
magick -size 1080x1350 xc:"#FAF7F2" -attenuate 0.15 +noise Gaussian -colorspace Gray -colorspace sRGB paper.png
magick -size 1080x1350 radial-gradient:"#1B5E6B"-"#0E3B43" glow-bg.png
magick -size 1080x1350 plasma:"#F2A541"-"#0E3B43" -blur 0x30 blob-bg.png
# dot grid pattern
magick -size 40x40 xc:none -fill "#0E3B4322" -draw "circle 20,20 20,23" -write mpr:dot +delete -size 1080x1350 tile:mpr:dot dots.png
```

## Drop shadow / glass
```bash
magick card.png \( +clone -background black -shadow 50x30+0+20 \) +swap -background none -layers merge +repage card-shadow.png
# frosted panel: blur the region of the background behind a card
magick bg.jpg \( +clone -crop 900x500+90+700 +repage -blur 0x25 -fill white -colorize 15% \) -geometry +90+700 -composite out.jpg
```

## Device / photo frames
```bash
# polaroid
magick in.jpg -resize 800x800^ -gravity center -extent 800x800 -bordercolor white -border 30 -gravity south -splice 0x110 polaroid.png
```

## Output & checks
```bash
magick identify -format "%f %wx%h %[colorspace] %[size]\n" posts/*/*.png
magick out.png -quality 92 -strip -colorspace sRGB out.jpg
magick slide-*.png carousel.pdf                                  # LinkedIn document carousel
magick slide-*.png -resize 360x +append strip.png                # quick preview strip
```

"""Render the FraudShield og:image (1200x630) with Pillow.

Palette and hierarchy mirror the app: near-black violet-biased ground,
violet accent held separate from the green/amber/red semantic set, and
the three verdicts shown as chips so the card says what the product
actually outputs.
"""
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
BG      = (13, 11, 20)
CARD    = (22, 19, 39)
LINE    = (42, 37, 69)
TX      = (237, 234, 247)
TX2     = (162, 157, 191)
TX3     = (110, 104, 144)
ACCENT  = (139, 124, 246)
GREEN   = (52, 211, 153)
AMBER   = (251, 191, 36)
RED     = (248, 113, 113)

F = "C:/Windows/Fonts/"
def font(name, size):
    return ImageFont.truetype(F + name, size)

bold   = lambda s: font("segoeuib.ttf", s)
semi   = lambda s: font("seguisb.ttf", s)
reg    = lambda s: font("segoeui.ttf", s)
mono   = lambda s: font("consola.ttf", s)

img  = Image.new("RGB", (W, H), BG)

# ---- soft violet glow, upper-left: stacked low-alpha ellipses ----
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd   = ImageDraw.Draw(glow)
for i in range(60, 0, -1):
    r = i * 13
    a = int(20 * (i / 60) ** 3)
    gd.ellipse([-260 - r // 3, -300 - r // 3, -260 + r, -300 + r],
               fill=(139, 124, 246, a))
for i in range(50, 0, -1):
    r = i * 11
    a = int(11 * (i / 50) ** 3)
    gd.ellipse([W - 120 - r, H - 40 - r, W - 120 + r, H - 40 + r],
               fill=(109, 93, 232, a))
img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
d = ImageDraw.Draw(img)

M = 84  # left margin

# ---- shield mark ----
# Drawn rather than set as an emoji: the system emoji shield is red/white
# and fights the violet palette, and colour fonts do not centre reliably.
# Shield = rounded top block unioned with a triangle to the point.
SX, SY, SW, SH = M, 66, 96, 110          # bounding box
d.rounded_rectangle([SX, SY, SX + SW, SY + int(SH * 0.60)], radius=16, fill=ACCENT)
d.polygon([(SX, SY + int(SH * 0.50)),
           (SX + SW, SY + int(SH * 0.50)),
           (SX + SW // 2, SY + SH)], fill=ACCENT)
# inner highlight for a little depth
d.rounded_rectangle([SX + 9, SY + 9, SX + SW - 9, SY + int(SH * 0.60)],
                    radius=10, fill=(158, 145, 250))
d.polygon([(SX + 9, SY + int(SH * 0.50)),
           (SX + SW - 9, SY + int(SH * 0.50)),
           (SX + SW // 2, SY + SH - 14)], fill=(158, 145, 250))
# checkmark
cx = SX + SW // 2
d.line([(cx - 21, SY + 50), (cx - 6, SY + 65), (cx + 23, SY + 32)],
       fill=BG, width=9, joint="curve")

# ---- wordmark + eyebrow ----
d.text((M + 132, 84),  "FraudShield", font=bold(66), fill=TX)
d.text((M + 137, 152), "U P I   P A Y M E N T   S C R E E N I N G",
       font=semi(19), fill=ACCENT)

# ---- rule ----
d.line([M, 224, W - M, 224], fill=LINE, width=2)

# ---- headline ----
d.text((M, 262), "Explainable fraud screening for",  font=bold(52), fill=TX)
d.text((M, 322), "UPI payment screenshots",          font=bold(52), fill=TX)

# ---- supporting line ----
d.text((M, 398),
       "Nine weighted rules produce an auditable risk verdict in under a second.",
       font=reg(28), fill=TX2)

# ---- verdict chips ----
chips = [("Verified \u2014 Low Risk", GREEN),
         ("Unable to Verify",         AMBER),
         ("High Risk",                RED)]
x, y = M, 470
for label, col in chips:
    f = semi(25)
    tw = d.textlength(label, font=f)
    w  = int(tw) + 62
    d.rounded_rectangle([x, y, x + w, y + 60], radius=30,
                        fill=(col[0] // 7, col[1] // 7, col[2] // 7), outline=col, width=2)
    d.ellipse([x + 24, y + 25, x + 34, y + 35], fill=col)
    d.text((x + 46, y + 30), label, font=f, fill=col, anchor="lm")
    x += w + 18

# ---- footer ----
d.text((M, 572), "Runs entirely in your browser  \u00b7  Nothing is uploaded to a server",
       font=mono(21), fill=TX3)

img.save("og-image.png", "PNG", optimize=True)
print("saved og-image.png", img.size)

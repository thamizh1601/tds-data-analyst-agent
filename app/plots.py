# app/plots.py
import matplotlib.pyplot as plt
import numpy as np
import io, base64
from PIL import Image

def scatter_with_regression_png_datauri(x, y, xlabel="Rank", ylabel="Peak", title="Rank vs Peak", size_limit=100_000):
    """
    Make scatter + dotted red regression line. Return a PNG data URI.
    Attempts iterative DPI/size adjustments and Pillow-based downscaling to
    keep file size <= size_limit bytes.
    """
    if len(x) == 0 or len(y) == 0:
        return "data:image/png;base64,"

    def make_png_bytes(dpi=100, figsize=(6, 4)):
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        ax.scatter(x, y, s=20)
        # regression
        try:
            coeffs = np.polyfit(x, y, 1)
            m, b = coeffs
            xs = np.linspace(min(x), max(x), 200)
            ys = m * xs + b
            ax.plot(xs, ys, linestyle=':', color='red', linewidth=2)  # dotted red
        except Exception:
            pass
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(True, linestyle=':', alpha=0.4)
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)
        return buf.getvalue()

    # try combos
    for dpi in (150, 120, 100, 80, 60):
        for scale in (1.0, 0.9, 0.8, 0.7):
            figsize = (6 * scale, 4 * scale)
            png = make_png_bytes(dpi=dpi, figsize=figsize)
            if len(png) <= size_limit:
                return "data:image/png;base64," + base64.b64encode(png).decode()

    # fallback: use Pillow to quantize and downscale
    im = Image.open(io.BytesIO(png))
    for target_w in (900, 800, 700, 600, 500, 400, 350, 300, 250):
        w, h = im.size
        if w <= target_w:
            continue
        nh = int(h * (target_w / w))
        im2 = im.resize((target_w, nh), Image.LANCZOS)
        out = io.BytesIO()
        im2_conv = im2.convert("P", palette=Image.ADAPTIVE)
        im2_conv.save(out, format="PNG", optimize=True)
        data = out.getvalue()
        if len(data) <= size_limit:
            return "data:image/png;base64," + base64.b64encode(data).decode()

    # last resort: small thumbnail PNG
    im_small = im.resize((400, 300), Image.LANCZOS)
    out = io.BytesIO()
    im_small.save(out, format="PNG", optimize=True)
    b = out.getvalue()
    return "data:image/png;base64," + base64.b64encode(b).decode()
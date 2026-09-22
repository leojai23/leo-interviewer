"""Generate icons and a content-hashed service worker for the Interview Kit."""
import hashlib
import pathlib

HERE = pathlib.Path(__file__).parent


def make_icons():
    from PIL import Image, ImageDraw, ImageFont

    for size in (192, 512):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        pad = size // 12
        d.rounded_rectangle(
            [pad, pad, size - pad, size - pad],
            radius=size // 6,
            fill=(67, 56, 202, 255),  # #4338ca
            outline=(230, 229, 251, 255),
            width=max(2, size // 64),
        )
        try:
            font = ImageFont.truetype("georgiab.ttf", int(size * 0.5))
        except OSError:
            try:
                font = ImageFont.truetype("arialbd.ttf", int(size * 0.48))
            except OSError:
                font = ImageFont.load_default()
        text = "I"
        box = d.textbbox((0, 0), text, font=font)
        tw, th = box[2] - box[0], box[3] - box[1]
        d.text(
            ((size - tw) / 2 - box[0], (size - th) / 2 - box[1]),
            text,
            font=font,
            fill=(255, 255, 255, 255),
        )
        img.save(HERE / f"icon-{size}.png")
        print(f"wrote icon-{size}.png")


def make_sw():
    index = (HERE / "index.html").read_bytes()
    digest = hashlib.sha1(index).hexdigest()[:10]
    sw = f"""// Interview Kit service worker — cache-first, offline shell.
const CACHE = 'interview-kit-{digest}';
const ASSETS = ['./', './index.html', './manifest.json', './icon-192.png', './icon-512.png'];

self.addEventListener('install', (e) => {{
  self.skipWaiting();
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)));
}});

self.addEventListener('activate', (e) => {{
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
}});

self.addEventListener('fetch', (e) => {{
  if (e.request.method !== 'GET') return;
  e.respondWith(
    caches.match(e.request).then((hit) =>
      hit ||
      fetch(e.request).then((res) => {{
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => {{}});
        return res;
      }}).catch(() => caches.match('./index.html'))
    )
  );
}});
"""
    (HERE / "sw.js").write_text(sw, encoding="utf-8")
    print(f"wrote sw.js (CACHE = interview-kit-{digest})")


if __name__ == "__main__":
    make_icons()
    make_sw()

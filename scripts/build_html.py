"""Embed Plotly, processed model and UI in one offline HTML."""
from pathlib import Path
import base64
from io import BytesIO
import plotly.offline
from PIL import Image, ImageOps

ROOT=Path(__file__).resolve().parents[1]

def favicon_asset(root=ROOT):
    for name, mime, image_format in (
        ('favicon.png', 'image/png', 'PNG'),
        ('favicon.jpg', 'image/jpeg', 'JPEG'),
        ('favicon.jpeg', 'image/jpeg', 'JPEG'),
    ):
        path=root/'web'/name
        if path.is_file():
            with Image.open(path) as original:
                if original.format != image_format:
                    raise ValueError(f'web/{name} 的内容与文件扩展名不符')
                icon=ImageOps.exif_transpose(original)
                icon.thumbnail((128,128),Image.Resampling.LANCZOS)
                canvas=Image.new('RGBA' if image_format=='PNG' else 'RGB',
                                 (128,128),(0,0,0,0) if image_format=='PNG' else (255,255,255))
                canvas.paste(icon.convert(canvas.mode),
                             ((128-icon.width)//2,(128-icon.height)//2))
                output=BytesIO()
                canvas.save(output,format=image_format,optimize=True)
            return mime,output.getvalue(),path
    svg=root/'web/favicon.svg'
    return 'image/svg+xml',svg.read_bytes(),svg

def main():
    template=(ROOT/'web/template.html').read_text(encoding='utf-8')
    favicon_mime,favicon_bytes,favicon_path=favicon_asset()
    favicon=base64.b64encode(favicon_bytes).decode('ascii')
    html=(template
          .replace('/*__FAVICON_MIME__*/',favicon_mime)
          .replace('/*__FAVICON__*/',favicon)
          .replace('/*__STYLE__*/',(ROOT/'web/style.css').read_text(encoding='utf-8'))
          .replace('/*__PLOTLY__*/',plotly.offline.get_plotlyjs())
          .replace('/*__MODEL__*/',(ROOT/'processed_data/model.json').read_text(encoding='utf-8').replace('</','<\\/'))
          .replace('/*__APP__*/',(ROOT/'web/app.js').read_text(encoding='utf-8')))
    (ROOT/'dist').mkdir(exist_ok=True)
    (ROOT/'dist/index.html').write_text(html,encoding='utf-8')
    print('dist/index.html',len(html.encode('utf-8')),'bytes; favicon:',favicon_path.name,'; no runtime network dependencies')
if __name__=='__main__':main()

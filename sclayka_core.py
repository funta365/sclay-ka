"""Склейка верхних половин страниц по две на лист A4.

Страница N и N+1 исходного файла -> верх и низ одного листа A4.
Рендерится только верхняя половина каждой страницы и только по одной
странице за раз, так что память не растёт с размером документа.
"""
import io
import os
from dataclasses import dataclass
from typing import Callable

import pymupdf as fitz
from PIL import Image

A4 = fitz.paper_rect("a4")
SUPPORTED_EXT = (".pdf", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp")
SUFFIX = "_склейка"


@dataclass(frozen=True)
class Quality:
    name: str
    dpi: int
    jpeg: int
    hint: str


QUALITIES = (
    Quality("Печать", 300, 80, "300 dpi · для печати"),
    Quality("Стандарт", 200, 72, "200 dpi · файл в 2–3 раза меньше"),
    Quality("Компактно", 150, 60, "150 dpi · для почты"),
)


@dataclass(frozen=True)
class Options:
    quality: Quality = QUALITIES[0]
    grayscale: bool = False


class Cancelled(Exception):
    pass


def is_supported(path: str) -> bool:
    return path.lower().endswith(SUPPORTED_EXT)


def page_count(path: str) -> int:
    with fitz.open(path) as doc:
        if doc.needs_pass:
            raise ValueError("Файл защищён паролем")
        return doc.page_count


def output_path(src: str, folder: str) -> str:
    """Имя_склейка.pdf; если такой уже есть — Имя_склейка (2).pdf и т.д."""
    base = os.path.splitext(os.path.basename(src))[0] + SUFFIX
    path = os.path.join(folder, base + ".pdf")
    n = 2
    while os.path.exists(path):
        path = os.path.join(folder, f"{base} ({n}).pdf")
        n += 1
    return path


def _open_as_pdf(path: str) -> fitz.Document:
    doc = fitz.open(path)
    if doc.needs_pass:
        doc.close()
        raise ValueError("Файл защищён паролем")
    if not doc.is_pdf:  # картинка -> одностраничный PDF
        data = doc.convert_to_pdf()
        doc.close()
        doc = fitz.open("pdf", data)
    if doc.page_count == 0:
        doc.close()
        raise ValueError("В файле нет страниц")
    return doc


def _source_dpi(page: fitz.Page) -> float:
    """Реальное разрешение скана на странице (0, если картинок нет)."""
    best = 0.0
    try:
        infos = page.get_image_info()
    except Exception:
        return 0.0
    for info in infos:
        x0, y0, x1, y1 = info["bbox"]
        size_pt = max(x1 - x0, y1 - y0)
        if size_pt > 36:  # мелкие вставки (логотипы, штампы) не учитываем
            best = max(best, max(info["width"], info["height"]) * 72 / size_pt)
    return best


def _render_top_half(page: fitz.Page, slot: fitz.Rect, opts: Options) -> tuple[bytes, fitz.Rect]:
    r = page.rect
    clip = fitz.Rect(r.x0, r.y0, r.x1, r.y0 + r.height / 2)

    # Куда встанет картинка на листе: вписать в слот, по центру по горизонтали.
    scale = min(slot.width / clip.width, slot.height / clip.height)
    w, h = clip.width * scale, clip.height * scale
    x0 = slot.x0 + (slot.width - w) / 2
    target = fitz.Rect(x0, slot.y0, x0 + w, slot.y0 + h)

    # Разрешение: целевое, но не выше исходного скана (незачем раздувать 150 dpi до 300).
    zoom = opts.quality.dpi * target.width / 72 / clip.width
    src_dpi = _source_dpi(page)
    if src_dpi:
        zoom = min(zoom, max(src_dpi, 100) / 72)

    cs = fitz.csGRAY if opts.grayscale else fitz.csRGB
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=clip, colorspace=cs, alpha=False)
    mode = "L" if opts.grayscale else "RGB"
    img = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
    del pix

    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=opts.quality.jpeg, optimize=True,
             subsampling=2, dpi=(opts.quality.dpi,) * 2)
    return buf.getvalue(), target


def merge_file(
    src: str,
    dst: str,
    opts: Options,
    progress: Callable[[int, int], None] | None = None,
    cancelled: Callable[[], bool] = lambda: False,
) -> int:
    """Склеивает src в dst. Возвращает размер результата в байтах."""
    doc = _open_as_pdf(src)
    out = fitz.open()
    tmp = dst + ".part"
    try:
        total = doc.page_count
        half = A4.height / 2
        out_page = None
        for i in range(total):
            if cancelled():
                raise Cancelled()
            if i % 2 == 0:
                out_page = out.new_page(width=A4.width, height=A4.height)
            slot = fitz.Rect(0, (i % 2) * half, A4.width, (i % 2 + 1) * half)
            data, target = _render_top_half(doc[i], slot, opts)
            out_page.insert_image(target, stream=data)
            if progress:
                progress(i + 1, total)
        out.set_metadata({"producer": "Склей-ка", "title": os.path.basename(dst)})
        out.save(tmp, garbage=3, deflate=True)
        out.close()
        os.replace(tmp, dst)
        return os.path.getsize(dst)
    finally:
        doc.close()
        if not out.is_closed:
            out.close()
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass

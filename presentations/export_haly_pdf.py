"""Create a visually matched sharing PDF from finalized PowerPoint renders."""
import sys
from pathlib import Path

from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


def main():
    render_dir, output = map(Path, sys.argv[1:])
    if output.exists():
        raise FileExistsError("Refusing to overwrite an existing PDF")
    images = [render_dir / f"slide-{n:02d}.png" for n in range(1, 15)]
    if not all(image.is_file() for image in images):
        raise FileNotFoundError("Expected all 14 finalized slide renders")
    page_size = (960, 540)
    pdf = canvas.Canvas(str(output), pagesize=page_size, pageCompression=1)
    pdf.setTitle("HALY Operations Control Tower - Business Portfolio Case Study")
    pdf.setAuthor("Yusuf Ondes")
    pdf.setSubject("Fictional company and synthetic campaign fulfilment scenario")
    for number, image in enumerate(images, 1):
        pdf.drawImage(ImageReader(str(image)), 0, 0, *page_size)
        if number == 14:
            pdf.linkURL(
                "https://github.com/yusufondes/Operations-Control-Tower",
                (525, 153.75, 907.5, 185.25), relative=0, thickness=0,
            )
        pdf.showPage()
    pdf.save()
    print("Created 14-page, 16:9 image-based PDF; editable text remains in PPTX.")


if __name__ == "__main__":
    main()

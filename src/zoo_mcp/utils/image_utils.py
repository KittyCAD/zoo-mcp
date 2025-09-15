import io

from mcp.server.fastmcp.utilities.types import Image
from mcp.types import ImageContent
from PIL import Image as PILImage


def create_image_collage(image_byte_list: list[bytes]) -> bytes:
    assert len(image_byte_list) == 4, (
        "Exactly 4 images are required to create a 2x2 collage."
    )

    # Load images
    images = []
    for img_bytes in image_byte_list:
        img = PILImage.open(io.BytesIO(img_bytes))
        img = img.convert("RGB") if img.mode != "RGB" else img
        images.append(img)

    # Verify all are same size
    widths, heights = zip(*(img.size for img in images))
    if len(set(widths)) > 1 or len(set(heights)) > 1:
        raise ValueError("All images must have the same dimensions.")

    img_w, img_h = images[0].size

    # Create blank canvas 2x2
    collage = PILImage.new("RGB", (img_w * 2, img_h * 2))
    positions = [
        (0, 0),  # Top-left
        (img_w, 0),  # Top-right
        (0, img_h),  # Bottom-left
        (img_w, img_h),  # Bottom-right
    ]

    for img, pos in zip(images, positions):
        collage.paste(img, pos)

    # Scale down by 2x
    collage = collage.resize((img_w, img_h), PILImage.Resampling.LANCZOS)

    # Save to bytes
    out = io.BytesIO()
    collage.save(out, format="JPEG", quality=95)
    collage_bytes = out.getvalue()

    # Cleanup
    for img in images:
        img.close()
    collage.close()
    out.close()

    return collage_bytes


def encode_image(img_bytes: bytes) -> ImageContent:
    """
    Encodes a PIL Image to a format compatible with ImageContent.
    """
    img_obj = Image(data=img_bytes, format="jpeg")
    return img_obj.to_image_content()

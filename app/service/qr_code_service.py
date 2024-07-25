import qrcode
from io import BytesIO

def generate_qr_code(data: str) -> bytes:
    """
    Generates a QR code from the given data and returns it as a bytes object.
    """
    # Create a QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # Create an image from the QR code instance
    img = qr.make_image(fill="black", back_color="white")

    # Save the image to a bytes buffer
    buf = BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()
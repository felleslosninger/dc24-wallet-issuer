import qrcode
import base64
import urllib.parse
from io import BytesIO


def generate_qr_code(base_url: str, credential_data: dict) -> str:
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
    data = base_url + urllib.parse.urlencode(credential_data)
    qr.add_data(data)
    qr.make(fit=True)

    # Create an image from the QR code instance
    img = qr.make_image(fill="black", back_color="white")

    # Save the image to a bytes buffer
    buf = BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode('utf-8'), data
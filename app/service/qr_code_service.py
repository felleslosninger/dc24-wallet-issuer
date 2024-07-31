import qrcode
import base64
import urllib.parse
import json
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
    json_data = json.dumps(credential_data)
    
    # Properly format the URL by encoding the JSON data
    encoded_data = urllib.parse.quote(json_data)
    data = f"{base_url}{encoded_data}"
    
    qr.add_data(data)
    qr.make(fit=True)

    # Create an image from the QR code instance
    img = qr.make_image(fill="black", back_color="white")

    # Save the image to a bytes buffer
    buf = BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode('utf-8'), data
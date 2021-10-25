import io
import os
import time
from typing import Dict
from google.cloud import vision
from proto.marshal.collections import RepeatedComposite

from objects.receipt_info import ReceiptInfo


def get_text(path: str):
    """
    Get receipt text using Google Vision API.
    """
    # Instantiates a client
    client = vision.ImageAnnotatorClient()

    # The name of the image file to annotate
    base = "receipts/"
    file_name = os.path.abspath(base + path)

    # Loads the image into memory
    with io.open(file_name, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    # Get text from image
    response = client.text_detection(image=image, timeout=60)

    if response.error.message:
        raise Exception(
            "{}\nFor more info on error messages, check: "
            "https://cloud.google.com/apis/design/errors".format(
                response.error.message
            )
        )

    return response.text_annotations


def retrieve_info(text: RepeatedComposite) -> Dict[str, any]:
    """
    Returns a dictionary of name, date, tags,
    and total price of a given receipt.
    """

    info = ReceiptInfo(text)
    info.extract_info()

    return info.get_info()


def main() -> None:
    image = "test_receipt_lawson.jpg"
    start = time.time()
    text: RepeatedComposite = get_text(image)
    end = time.time()
    info = retrieve_info(text)
    print(
        f"Time elapsed getting text from API: {round(end - start, 2)} seconds."
    )
    print(info)


if __name__ == "__main__":
    main()

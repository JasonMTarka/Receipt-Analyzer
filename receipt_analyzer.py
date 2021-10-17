import io
import os
import datetime
import re

from typing import List, Dict
# Imports the Google Cloud client library
from google.cloud import vision
from google.cloud.vision_v1.types.image_annotator import EntityAnnotation
from proto.marshal.collections import RepeatedComposite

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

def get_row(
    text: RepeatedComposite,
    targets: List[EntityAnnotation],
    search_term: str,
    orientation: str ="vertical"
    ) -> List[str]:
        """
        Get row containing search term and corresponding price.
        """
        adjustment = 0.98
        result_length_limit = 5

        if not targets:
            print("No targets")
            return []

        coords = {}

        for target in targets:
            coords = {
                "y": target.bounding_poly.vertices[0].y,
                "x": target.bounding_poly.vertices[0].x
            }
        match orientation:
            case "vertical":
                height = coords["y"]
            case "horizontal":
                height = coords["x"]

        adjusted_up = height / adjustment
        adjusted_down = height * adjustment

        results = []
        for line in text[1:]:
            description = line.description
            line_height = line.bounding_poly.vertices[0].y

            if orientation == "horizontal":
                line_height = line.bounding_poly.vertices[0].x
            if (
                line_height > adjusted_down
                and line_height < adjusted_up
                and search_term not in description
                ):
                results.append(description)
        if len(results) >= result_length_limit and orientation == "vertical":
            return get_row(text, targets, search_term, orientation="horizontal")

        return results

def search(text: RepeatedComposite, search_term):
    """
    Search a receipt for a given search term and attempt to get corresponding 
    price.
    """

    def _extract_value(row: List[str]) -> int:
        """
        Attempts to extract an integer value from a row.
        """
        for element in row:
            try:
                return int(element.replace(" ", "").replace(",", ""))
            except ValueError:
                continue

    targets: List[EntityAnnotation] = []

    for line in text[1:]:
        if search_term in line.description:
            targets.append(line)
 
    if not targets:
        print(f"{search_term} not found.")
        print({"DEBUG" : text[0].description})

    row = get_row(text, targets, search_term)
    total = _extract_value(row)
    return total

def get_info(text: RepeatedComposite) -> Dict[str, any]:
    """
    Returns a dictionary of name, date, type,
    and total price of a given receipt.
    """

    def get_date(line: str) -> str:
        """
        Tries to get date from a given line from text.
        """
        date_regex = r"[0-9]{2,4}[/年][0-9]{1,2}[/月][0-9]{1,2}"
        if match := re.match(date_regex, line):
            matched_date = match.group()
            if "年" in matched_date or "月" in matched_date:
                try:
                    date = datetime.datetime.strptime(matched_date, "%Y年%m月%d")
                except ValueError:
                    date = datetime.datetime.strptime(matched_date, "%y年%m月%d")
            else:
                try: 
                    date = datetime.datetime.strptime(matched_date, "%Y/%m/%d")
                except ValueError:
                    date = datetime.datetime.strptime(matched_date, "%y/%m/%d")

            return f"{date.year}-{date.month}-{date.day}"
        else:
            return ""

    info: Dict[str, any] = {}
    word_list = text[0].description.split("\n")

    for line in word_list:

        print(line)

        if date := get_date(line):
            info["date"] = date

        if "泰和" in line:
            info["name"] = "Chinese Super"
            info["type"] = "groceries"
        if "肉のハナマ" in line:
            info["name"] = "Niku no Hanamasa"
            info["type"] = "groceries"
        if "東武ストア" in line:
            info["name"] = "Kasai New Super"
            info["type"] = "groceries"
        if "smartwaon" in line:
            info["name"] = "My Basket"
            info["type"] = "groceries"
        if "セブン-イレブン" in line:
            info["name"] = "Seven Eleven"
            info["type"] = "groceries"
        if "上記正に領収いたしました" in line:
            info["name"] = "Lawson"
            info["type"] = "groceries"
        if "黒ラベル" in line or "クロラベル" in line:
            info["alcohol"] = True
        if "ドミノピザ" in line:
            info["name"] = "Domino's"
            info["type"] = "dining"
        if "Hotto" in line:
            info["name"] = "Hotto Motto"
            info["type"] = "bento"

    info["total"] = search(text, "合")

    return info

def main() -> None:
    text: RepeatedComposite = get_text("test_receipt_seveneleven.jpg")
    info = get_info(text)
    print(info)


if __name__ == "__main__":
    main()

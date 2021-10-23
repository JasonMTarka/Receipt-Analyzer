import io
import os
import datetime
import re
import time
from typing import List, Dict
from google.cloud import vision
from google.cloud.vision_v1.types.image_annotator import EntityAnnotation
from proto.marshal.collections import RepeatedComposite

from constants import Orientations, Tags


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
    orientation: str = Orientations.VERTICAL
    ) -> List[str]:
        """
        Get row containing search term and corresponding price.
        """
        ADJUSTMENT = 0.98
        RESULT_LENGTH_LIMIT = 5

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
            case Orientations.VERTICAL:
                height = coords["y"]
            case Orientations.HORIZONTAL:
                height = coords["x"]

        adjusted_up = height / ADJUSTMENT
        adjusted_down = height * ADJUSTMENT

        results = []
        for line in text[1:]:
            description = line.description
            line_height = line.bounding_poly.vertices[0].y

            if orientation == Orientations.HORIZONTAL:
                line_height = line.bounding_poly.vertices[0].x
            if (
                line_height > adjusted_down
                and line_height < adjusted_up
                and search_term not in description
                ):
                results.append(description)

        if len(results) >= RESULT_LENGTH_LIMIT and orientation == Orientations.VERTICAL:
            return get_row(text, targets, search_term, orientation=Orientations.HORIZONTAL)

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
        return 0

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
    Returns a dictionary of name, date, tags,
    and total price of a given receipt.
    """

    def get_date(line: str) -> str:
        """
        Tries to get date from a given line from text.
        """
        date_regex = r"[0-9]{2,4}[/年][0-9]{1,2}[/月][0-9]{1,2}"
        if match := re.match(date_regex, line):
            date_str = match.group()
            if "年" in date_str or "月" in date_str:
                try:
                    date = datetime.datetime.strptime(date_str, "%Y年%m月%d")
                except ValueError:
                    date = datetime.datetime.strptime(date_str, "%y年%m月%d")
            else:
                try: 
                    date = datetime.datetime.strptime(date_str, "%Y/%m/%d")
                except ValueError:
                    date = datetime.datetime.strptime(date_str, "%y/%m/%d")

            return f"{date.year}-{date.month}-{date.day}"
        else:
            return ""

    DATE = "date"
    NAME = "name"
    TOTAL = "total"
    TAGS = "tags"

    info: Dict[str, str | int | List[str]] = {}
    info[TAGS] = []

    word_list = text[0].description.split("\n")

    for line in word_list:
        print(line)
        if new_date := get_date(line):
            info[DATE] = new_date
        if "泰和" in line:
            info[NAME] = "Chinese Super"
            info[TAGS].append(Tags.GROCERIES)
        if "肉のハナマ" in line:
            info[NAME] = "Niku no Hanamasa"
            info[TAGS].append(Tags.GROCERIES)
        if "東武ストア" in line:
            info[NAME] = "Kasai New Super"
            info[TAGS].append(Tags.GROCERIES)
        if "smartwaon" in line:
            info[NAME] = "My Basket"
            info[TAGS].append(Tags.GROCERIES)
        if "セブン-イレブン" in line:
            info[NAME] = "Seven Eleven"
            info[TAGS].append(Tags.GROCERIES)
        if "上記正に領収いたしました" in line:
            info[NAME] = "Lawson"
            info[TAGS].append(Tags.GROCERIES)
        if "黒ラベル" in line or "クロラベル" in line:
            info[TAGS].append(Tags.ALCOHOL)
        if "ドミノピザ" in line:
            info[NAME] = "Domino's"
            info[TAGS].append(Tags.DINING)
        if "Hotto" in line:
            info[NAME] = "Hotto Motto"
            info[TAGS].append(Tags.BENTO)
        if "welcia" in line:
            info[NAME] = "Welcia"
            info[TAGS].append(Tags.GROCERIES)
        if "貴族" in line:
            info[NAME] = "Torikizoku"
            info[TAGS].append(Tags.DINING)
        if "ロフト" in line:
            info[NAME] = "Loft"
            info[TAGS].append(Tags.HOUSEHOLD)
        if "UNIQLO" in line:
            info[NAME] = "Uniqlo"
            info[TAGS].append(Tags.CLOTHES)
        if "ヨーカドー" in line:
            info[NAME] = "Ito Yokado"
            info[TAGS].append(Tags.GROCERIES)

    info[TOTAL] = search(text, "合")

    return info

def main() -> None:
    start = time.time()
    text: RepeatedComposite = get_text("test_receipt_seveneleven.jpg")
    end = time.time()
    info = get_info(text)
    print(f"Time elapsed getting text from API: {round(end - start, 2)} seconds.")
    print(info)


if __name__ == "__main__":
    main()

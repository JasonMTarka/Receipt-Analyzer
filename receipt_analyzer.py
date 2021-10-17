import io
import os
import sys
from typing import List, Dict
# Imports the Google Cloud client library
from google.cloud import vision
from google.cloud.vision_v1.types.image_annotator import EntityAnnotation
from proto.marshal.collections import RepeatedComposite

def get_text(path: str):
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

def get_value(text: RepeatedComposite, targets: List[EntityAnnotation], search_term: str, orientation: str ="vertical") -> List[str]:

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
            return get_value(text, targets, search_term, orientation="horizontal")

        return results

def search(text: RepeatedComposite, search_term):

    def _extract_value(row: List[str]) -> int:
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

    row = get_value(text, targets, search_term)
    total = _extract_value(row)
    return total

def get_info(text: RepeatedComposite) -> Dict[str, any]:

    info: Dict[str, any] = {}
    word_list = text[0].description.split("\n")

    for char in word_list:
        if "泰和" in char:
            info["name"] = "Chinese Super"
            info["type"] = "groceries"
        if "肉のハナマ" in char:
            info["name"] = "Niku no Hanamasa"
            info["type"] = "groceries"
        if "東武ストア" in char:
            info["name"] = "Kasai New Super"
            info["type"] = "groceries"
        if "smartwaon" in char:
            info["name"] = "My Basket"
            info["type"] = "groceries"
        if "セブン-イレブン" in char:
            info["name"] = "Seven Eleven"
            info["type"] = "groceries"
        if "上記正に領収いたしました" in char:
            info["name"] = "Lawson"
            info["type"] = "groceries"
        if "黒ラベル" in char or "クロラベル" in char:
            info["alcohol"] = True
        if "ドミノピザ" in char:
            info["name"] = "Domino's"
            info["type"] = "dining"
    info["total"] = search(text, "合")

    return info

def main():
    text: RepeatedComposite = get_text("test_receipt_dominos.jpg")
    info = get_info(text)
    print(info)


if __name__ == "__main__":
    main()

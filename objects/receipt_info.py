import datetime
import re

from typing import Dict, List
from google.cloud.vision_v1.types.image_annotator import EntityAnnotation
from proto.marshal.collections import RepeatedComposite

from constants import Orientations, Categories, ITEMS


class ReceiptInfo:


    def __init__(self, text: RepeatedComposite) -> None:
        self._text = text
        self.name = ""
        self.date = ""
        self.tags = []
        self.total = 0


    def search_price(self, search_term: str) -> int:
        """
        Search a receipt for a given search term and attempt to get corresponding
        price.
        """

        def _get_row(
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

                # Gets last coord because more likely to be total
                coords = {
                    "y": targets[-1].bounding_poly.vertices[0].y,
                    "x": targets[-1].bounding_poly.vertices[0].x
                }

                match orientation:
                    case Orientations.VERTICAL:
                        height = coords["y"]
                    case Orientations.HORIZONTAL:
                        height = coords["x"]

                adjusted_up = height / ADJUSTMENT
                adjusted_down = height * ADJUSTMENT

                results = []
                for line in self._text[1:]:
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

                if (
                    len(results) >= RESULT_LENGTH_LIMIT 
                    and orientation == Orientations.VERTICAL
                    ):
                    return _get_row(targets, search_term, orientation=Orientations.HORIZONTAL)

                return results


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

        for line in self._text[1:]:
            if search_term in line.description:
                targets.append(line)

        if not targets:
            print(f"{search_term} not found.")
            print({"DEBUG": self._text[0].description})

        row = _get_row(targets, search_term)
        total = _extract_value(row)
        return total


    def extract_info(self) -> None:
        
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

        word_list = self._text[0].description.split("\n")

        for line in word_list:
            print(line)
            for item in ITEMS.keys():
                if new_date := get_date(line):
                    self.date = new_date
                if item in line:
                    self.name = ITEMS[item][Categories.NAME]
                    self.tags.append(ITEMS[item][Categories.TAGS])

        self.total = self.search_price("合")

    def get_info(self) -> Dict[str, str | int | List]:
        return {
            Categories.NAME: self.name,
            Categories.DATE: self.date,
            Categories.TOTAL: self.total,
            Categories.TAGS: self.tags
        }
class Orientations:
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class Tags:
    GROCERIES = "groceries"
    DINING = "dining"
    BENTO = "bento"
    HOUSEHOLD = "household"
    ALCOHOL = "alcohol"
    CLOTHES = "clothes"


class Categories:
    DATE = "date"
    TOTAL = "total"
    TAGS = "tags"
    NAME = "name"


# fmt: off
ITEMS = {
    "泰和": {
        Categories.NAME: "Chinese Super",
        Categories.TAGS: Tags.GROCERIES,
    },
    "肉のハナマ": {
        Categories.NAME: "Niku no Hanamasa",
        Categories.TAGS: Tags.GROCERIES,
    },
    "東武ストア": {
        Categories.NAME: "Kasai New Super",
        Categories.TAGS: Tags.GROCERIES,
    },
    "smartwaon": {
        Categories.NAME: "My Basket",
        Categories.TAGS: Tags.GROCERIES,
    },
    "セブン-イレブン": {
        Categories.NAME: "Seven Eleven",
        Categories.TAGS: Tags.GROCERIES,
    },
    "上記正に領収いたしました": {
        Categories.NAME: "Lawson",
        Categories.TAGS: Tags.GROCERIES,
    },
    "黒ラベル": {
        Categories.TAGS: Tags.ALCOHOL
        },
    "ドミノピザ": {
        Categories.NAME: "Domino's", 
        Categories.TAGS: Tags.DINING},
    "Hotto": {
        Categories.NAME: "Hotto Motto", 
        Categories.TAGS: Tags.BENTO},
    "welcia": {
        Categories.NAME: "Welcia", 
        Categories.TAGS: Tags.GROCERIES},
    "貴族": {
        Categories.NAME: "Torikizoku", 
        Categories.TAGS: Tags.DINING},
    "ロフト": {
        Categories.NAME: "Loft", 
        Categories.TAGS: Tags.HOUSEHOLD},
    "UNIQLO": {
        Categories.NAME: "Uniqlo", 
        Categories.TAGS: Tags.HOUSEHOLD},
    "ヨーカドー": {
        Categories.NAME: "Ito Yokado",
        Categories.TAGS: Tags.GROCERIES,
    },
}
# fmt: on

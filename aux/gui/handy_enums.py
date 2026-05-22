from enum import Enum
import random


class LineShape(Enum):
    SolidLine = "SolidLine"
    DashLine = "DashLine"
    DotLine = "DotLine"
    DashDotLine = "DashDotLine"
    DashDotDotLine = "DashDotDotLine"


class LineColor(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"
    YELLOW = "yellow"
    WHITE = "white"
    BLACK = "black"
    MAGENTA = "magenta"
    ORANGE = "orange"
    CORAL = "coral"
    CYAN = "cyan"
    GRAY = "gray"
    DARK_RED = "darkred"
    DARK_GREEN = "darkgreen"
    DARK_BLUE = "darkblue"
    PURPLE = "purple"
    PINK = "pink"
    BROWN = "brown"
    LIME = "lime"
    TEAL = "teal"
    
    INDIGO = "indigo"
    GOLD = "gold"
    SILVER = "silver"
    MAROON = "maroon"
    OLIVE = "olive"
    TOMATO = "tomato"
    DODGER_BLUE = "dodgerblue"
    DEEP_SKY_BLUE = "deepskyblue"
    FOREST_GREEN = "forestgreen"
    LIME_GREEN = "limegreen"
    DARK_ORCHID = "darkorchid"
    CADET_BLUE = "cadetblue"
    CRIMSON = "crimson"
    SLATE_BLUE = "slateblue"
    TURQUOISE = "turquoise"


def random_line_color():
    return random.choice(list(LineColor))

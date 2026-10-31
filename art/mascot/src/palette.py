"""Master palette. Every pixel in every sheet comes from this file.

Ramps run dark -> light. Index 0 doubles as the selective-outline tone.
"""

INK, COAT, COAT_DARK, BELT, METAL, HAT, BAND, PEN, GLASS, PAPER, WOOD, STEEL, SCREEN, SLEEVE, FOOT, GEM, NAVY, WATER, WHITE = range(1, 20)
# Case 2 suspects: Dash's enamel and fletching, Rolla's tyre and crust, Mu's pine and hard hat, roller skates
DASH, FLETCH, RUBBER, PIE, PINE, HARDHAT, SKATE = range(20, 27)

RAMPS = {
    INK:       ["#020310", "#060B20", "#0E1938", "#1A2E5C", "#2F4E8E"],
    COAT:      ["#3B2410", "#6E4822", "#9C6D38", "#C79A5C", "#E6C189"],
    SLEEVE:    ["#3B2410", "#6E4822", "#9C6D38", "#C79A5C", "#E6C189"],
    COAT_DARK: ["#24150A", "#3B2410", "#55361A", "#6E4822", "#8A5C2E"],
    BELT:      ["#1E1208", "#38220F", "#563519", "#764A25", "#946035"],
    METAL:     ["#4A3712", "#7D6123", "#B8933A", "#E3C266", "#FFF0B0"],
    HAT:       ["#170D06", "#2E1B0E", "#4A2D17", "#6A4223", "#8C5A31"],
    BAND:      ["#4A0A08", "#8E1A14", "#C9302A", "#EE5A4C", "#FF8A78"],
    PEN:       ["#4A0A08", "#8E1A14", "#C9302A", "#EE5A4C", "#FF8A78"],
    GLASS:     ["#1C3D63", "#2F6496", "#4F8FC6", "#86BDE6", "#D2ECFF"],
    PAPER:     ["#7D6E52", "#B3A37F", "#D9CCA6", "#F0E6C8", "#FFFBEF"],
    WOOD:      ["#3F2410", "#6B3F1D", "#99602E", "#C48A47", "#E3B470"],
    STEEL:     ["#23272E", "#3F4650", "#68717D", "#9AA4AF", "#D5DCE3"],
    SCREEN:    ["#0B2A1A", "#14482B", "#1F7A44", "#3DBB6A", "#9CF5B5"],
    FOOT:      ["#5A1530", "#8E2550", "#C23C74", "#EB6A9E", "#FFA3C6"],
    GEM:       ["#1E4C63", "#3A7E99", "#68B3CC", "#A8DDEC", "#E6F8FF"],
    NAVY:      ["#0A0F24", "#151E3D", "#22305C", "#33467F", "#4A61A3"],
    WATER:     ["#0F2E5C", "#1B4885", "#2C66AE", "#4A8AD0", "#7DB2EA"],
    WHITE:     ["#6F7584", "#A3A8B5", "#CDD1DA", "#E9ECF1", "#FFFFFF"],
    DASH:      ["#4A0C06", "#86200F", "#C4401E", "#EE6A35", "#FF9A62"],
    FLETCH:    ["#5C4410", "#9C7A1C", "#D9B23A", "#F4D86A", "#FFF2B0"],
    RUBBER:    ["#0B0C10", "#17191F", "#262931", "#383C47", "#50566A"],
    PIE:       ["#5A3410", "#94591E", "#C98B3A", "#E8B663", "#F8DB9A"],
    PINE:      ["#5A3A18", "#8C5E2C", "#BC8A4A", "#DDB173", "#F2D29C"],
    HARDHAT:   ["#5C3C06", "#A26A0A", "#E09B12", "#F8C23A", "#FFE38A"],
    SKATE:     ["#0A0F24", "#151E3D", "#22305C", "#33467F", "#4A61A3"],
}

# Glossy materials get a specular glint colour.
SPECULAR = {GEM: "#FFFFFF", WATER: "#E6F4FF", INK: "#BFD6FF", BAND: "#FFD0C6", PEN: "#FFD0C6", METAL: "#FFFFFF", FOOT: "#FFE6F0",
            GLASS: "#FFFFFF", STEEL: "#FFFFFF", SCREEN: "#E6FFEE", DASH: "#FFE0C8", HARDHAT: "#FFFFFF", SKATE: "#BFD6FF"}

OUTLINE = "#05030C"          # only where the sprite meets empty space and the ramp is light
EYE_WHITE = "#FFFFFF"
EYE_SHADE = "#C9D6EE"
PUPIL = "#04061A"
BROW = "#04061A"
MOUTH = "#6C8CCB"

GLOSSY = set(SPECULAR)


def register(ramp, specular=None):
    """Add a material ramp (dark -> light) and return its id. Cast files call this at import, in a fixed
    order, so every worker process assigns the same ids."""
    mid = max(RAMPS) + 1
    RAMPS[mid] = list(ramp)
    if specular:
        SPECULAR[mid] = specular
        GLOSSY.add(mid)
    return mid


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def all_colours():
    cols = {c for ramp in RAMPS.values() for c in ramp}
    cols |= set(SPECULAR.values())
    cols |= {OUTLINE, EYE_WHITE, EYE_SHADE, PUPIL, BROW, MOUTH}
    return sorted(cols)

# Preise fuer den Pendlerrechner
# alle Preise in CHF, 2. Klasse
# Quelle: sbb.ch, Stand Oktober 2026 (gueltig bis 12.12.2026)

PREISSTAND = "Oktober 2026"

# Halbtax PLUS: (was man bezahlt, wie viel Guthaben man bekommt)
PLUS_ERWACHSENE = {
    "PLUS 1000": (800, 1000),
    "PLUS 2000": (1500, 2000),
    "PLUS 3000": (2100, 3000),
}

PLUS_JUGEND = {
    "PLUS 1000": (600, 1000),
    "PLUS 2000": (1125, 2000),
    "PLUS 3000": (1575, 3000),
}

# Preise pro Altersgruppe
PREISE = {
    # 6 bis 15 Jahre (Kinder fahren sowieso zum halben Preis)
    "Kind": {
        "halbtax": 0,
        "plus": PLUS_JUGEND,
        "ga": 1720,
    },
    # 16 bis 24 Jahre
    "Jugend": {
        "halbtax": 120,
        "plus": PLUS_JUGEND,
        "ga": 2780,
    },
    # 25 bis 64 Jahre
    "Erwachsene": {
        "halbtax": 190,
        "plus": PLUS_ERWACHSENE,
        "ga": 3995,
    },
    # ab 65 Jahren
    "Senior": {
        "halbtax": 190,
        "plus": PLUS_ERWACHSENE,
        "ga": 3040,
    },
}

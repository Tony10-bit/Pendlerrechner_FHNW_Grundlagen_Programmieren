# US2, US6, US7 - Altersgruppe, guenstigste Option, Begründung
# US2: Alter eingeben, Altersgruppe bestimmen, Preise holen
# US6: Jahreskosten aller Optionen berechnen und günstigste anzeigen (folgt)
# US7: Begründung der Empfehlung (folgt)

from preise import PREISE, PREISSTAND


# ---------------- US2: Altersgruppe eingeben ----------------

# fragt so lange nach, bis eine gueltige Zahl eingegeben wird
def frage_zahl(frage):
    while True:
        eingabe = input(frage).strip()
        if eingabe.isdigit():
            return int(eingabe)
        print("Bitte eine gültige Zahl eingeben.")


# fragt so lange nach, bis ja oder nein eingegeben wird
def frage_ja_nein(frage):
    while True:
        antwort = input(frage).strip().lower()
        if antwort == "ja" or antwort == "nein":
            return antwort == "ja"
        print("Bitte ja oder nein eingeben.")


# ordnet das Alter einer Altersgruppe zu
def bestimme_altersgruppe(alter):
    if alter <= 15:
        return "Kind"
    elif alter <= 24:
        return "Jugend"
    elif alter <= 64:
        return "Erwachsene"
    else:
        return "Senior"


# fragt Alter und Halbtax ab, teilt einer Gruppe zu und gibt das Profil zurueck
def erfasse_profil():
    alter = frage_zahl("Wie alt bist du? ")
    gruppe = bestimme_altersgruppe(alter)
    hat_halbtax = frage_ja_nein("Besitzt du bereits ein Halbtax? (ja/nein): ")

    # Kopie machen, damit die Preistabelle selbst nicht veraendert wird
    preise = dict(PREISE[gruppe])

    # wer schon ein Halbtax hat, muss es nicht nochmals kaufen
    if hat_halbtax:
        preise["halbtax"] = 0

    print(f"Altersgruppe: {gruppe}")
    if alter < 6:
        print("Hinweis: Kinder unter 6 Jahren reisen in Begleitung gratis.")
    if hat_halbtax:
        print("Du hast bereits ein Halbtax. Es wird nicht nochmals verrechnet.")
    print(f"Preise (Stand {PREISSTAND}): Halbtax CHF {preise['halbtax']}, GA CHF {preise['ga']}")

    profil = {"alter": alter, "gruppe": gruppe, "hat_halbtax": hat_halbtax, "preise": preise}
    return profil


# ---------------- US6: Guenstigste Option anzeigen ----------------

# folgt


# ---------------- US7: Begruendung der Empfehlung ----------------

# folgt


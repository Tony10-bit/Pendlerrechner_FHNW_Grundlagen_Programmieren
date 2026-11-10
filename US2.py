# US2 - Altersgruppe eingeben
# Der Benutzer gibt sein Alter ein, das Programm bestimmt die Altersgruppe
# und holt die passenden Preise aus preise.py

from preise import PREISE, PREISSTAND


# fragt so lange nach, bis eine gueltige Zahl eingegeben wird
def frage_zahl(frage):
    while True:
        eingabe = input(frage).strip()
        if eingabe.isdigit():
            return int(eingabe)
        print("Bitte eine gueltige Zahl eingeben.")


# ordnet das Alter einer Altersgruppe zu
def bestimme_altersgruppe(alter):
    if alter < 6:
        return "Gratis"
    elif alter <= 15:
        return "Kind"
    elif alter <= 24:
        return "Jugend"
    elif alter <= 64:
        return "Erwachsene"
    else:
        return "Senior"


# fragt das Alter ab, zeigt die Altersgruppe an und gibt das Profil zurueck
def erfasse_profil():
    alter = frage_zahl("Wie alt bist du? ")
    gruppe = bestimme_altersgruppe(alter)

    while gruppe == "Gratis":
        print("Kinder unter 6 Jahren reisen gratis. Du brauchst kein Abo.")
        alter = frage_zahl("Wie alt bist du? ")
        gruppe = bestimme_altersgruppe(alter)

    preise = PREISE[gruppe]
    print(f"Altersgruppe: {gruppe}")
    print(f"Preise (Stand {PREISSTAND}): Halbtax CHF {preise['halbtax']}, GA CHF {preise['ga']}")

    profil = {"alter": alter, "gruppe": gruppe, "preise": preise}
    return profil


# nur zum Testen, wenn man diese Datei direkt startet
if __name__ == "__main__":
    profil = erfasse_profil()
    print(profil)

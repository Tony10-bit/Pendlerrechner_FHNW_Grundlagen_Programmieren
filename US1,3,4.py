
Strecken = []
Weitere_Strecke = "ja"

while Weitere_Strecke == "ja":

    # US1: Start- und Zielpunkt eingeben
    Startpunkt = input("Geben Sie Ihren Startpunkt ein: ")
    Zielpunkt = input("Geben Sie Ihren Zielpunkt ein: ")

    # US3: Häufigkeit eingeben
    while True:
        Eingabe = input("Wie oft fahren Sie diese Strecke? (Nur Zahl): ")

        if Eingabe.isdigit() and int(Eingabe) > 0:
            Haeufigkeit = int(Eingabe)
            break
        else:
            print("Bitte geben Sie eine positive ganze Zahl ein.")

    # US3: Woche oder Monat auswählen
    while True:
        Zeitraum = input("Pro Woche oder Monat? (w/m): ").lower()

        if Zeitraum == "w" or Zeitraum == "m":
            break
        else:
            print("Bitte w oder m eingeben.")

    # US3: Reisedauer auswählen
    while True:
        Eingabe = input("Wie viele Monate pro Jahr? (1/3/6/9/12): ")

        if Eingabe in ["1", "3", "6", "9", "12"]:
            Monate = int(Eingabe)
            break
        else:
            print("Bitte 1, 3, 6, 9 oder 12 eingeben.")

    # US3: Preis pro Hin- und Rückfahrt
    while True:
        try:
            Preis = float(input("Preis pro Hin- und Rückfahrt in CHF: ").replace(",", "."))

            if Preis >= 0:
                break
            else:
                print("Der Preis darf nicht negativ sein.")

        except ValueError:
            print("Bitte einen gültigen Preis eingeben.")

    # US3: Halbtax-Preis überprüfen
    while True:
        Halbtax = input("Ist das bereits ein Halbtax-Preis? (ja/nein): ").lower()

        if Halbtax == "ja" or Halbtax == "nein":
            break
        else:
            print("Bitte ja oder nein eingeben.")

    if Halbtax == "ja":
        Normalpreis = Preis * 2
    else:
        Normalpreis = Preis

    # Fahrtkosten für die gewählte Dauer berechnen
    if Zeitraum == "w":
        Anzahl_Fahrten = Haeufigkeit * (52 / 12) * Monate
    else:
        Anzahl_Fahrten = Haeufigkeit * Monate

    Kosten = Anzahl_Fahrten * Normalpreis

    # Strecke und Angaben speichern
    Strecken.append([Startpunkt, Zielpunkt, Haeufigkeit,
                     Zeitraum, Monate, Normalpreis, Kosten])

    print("\nRoute", len(Strecken))
    print("Von:", Startpunkt)
    print("Nach:", Zielpunkt)
    print("Hin- und Rückfahrten:", Haeufigkeit)
    print("Normalpreis: CHF", round(Normalpreis, 2))

    # US1: Weitere Strecke hinzufügen
    while True:
        Weitere_Strecke = input("\nWeitere Strecke hinzufügen? (ja/nein): ").lower()

        if Weitere_Strecke == "ja" or Weitere_Strecke == "nein":
            break
        else:
            print("Bitte ja oder nein eingeben.")


# US4: Zusätzliches Reisebudget
while True:
    Eingabe = input("\nZusätzliches Jahresbudget in CHF (Enter = 0): ")

    if Eingabe == "":
        Reisebudget = 0
        break

    try:
        Reisebudget = float(Eingabe.replace(",", "."))

        if Reisebudget >= 0:
            break
        else:
            print("Das Budget darf nicht negativ sein.")

    except ValueError:
        print("Bitte einen gültigen Betrag eingeben.")


# Alle erfassten Strecken anzeigen
print("\nIhre erfassten Verbindungen:")

Gesamtkosten = 0

for Nummer, Strecke in enumerate(Strecken, 1):
    print("\nRoute", Nummer)
    print("Von:", Strecke[0])
    print("Nach:", Strecke[1])
    print("Häufigkeit:", Strecke[2], "pro", Strecke[3])
    print("Monate:", Strecke[4])
    print("Normalpreis: CHF", round(Strecke[5], 2))
    print("Fahrtkosten: CHF", round(Strecke[6], 2))

    Gesamtkosten = Gesamtkosten + Strecke[6]

# US4: Reisebudget addieren
Gesamtkosten = Gesamtkosten + Reisebudget

print("\nZusätzliches Reisebudget: CHF", round(Reisebudget, 2))
print("Gesamtkosten pro Jahr: CHF", round(Gesamtkosten, 2))

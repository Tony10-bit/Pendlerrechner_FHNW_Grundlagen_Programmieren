
Strecken = []

Weitere_Strecke = "ja"

while Weitere_Strecke == "ja":

    Startpunkt = input("Geben Sie Ihren Startpunkt ein: ")
    Zielpunkt = input("Geben Sie Ihren Zielpunkt ein: ")

    # Häufigkeit mit Eingabeprüfung
    while True:
        Eingabe = input("Wie oft fahren Sie diese Strecke? (Nur Zahl): ")

        if Eingabe.isdigit() and int(Eingabe) > 0:
            Haeufigkeit = int(Eingabe)
            break
        else:
            print("Ungültige Eingabe! Bitte geben Sie eine positive ganze Zahl ein.")

    Zeitraum = input("Pro Woche oder Monat? (Woche/Monat): ")

    # Strecke speichern
    Strecken.append([Startpunkt, Zielpunkt, Haeufigkeit, Zeitraum])

    # Eingegebene Strecke anzeigen
    print("\nRoute", len(Strecken))
    print("Von:", Startpunkt)
    print("Nach:", Zielpunkt)
    print("Hin- und Rückfahrt:", Haeufigkeit, "Mal")

    # Weitere Strecke hinzufügen
    Weitere_Strecke = input("\nWeitere Strecke hinzufügen? (ja/nein): ").lower()

# Alle Strecken anzeigen
print("\nIhre erfassten Verbindungen:")

for Nummer, Strecke in enumerate(Strecken, 1):
    print("\nRoute", Nummer)
    print("Von:", Strecke[0])
    print("Nach:", Strecke[1])
    print("Häufigkeit:", Strecke[2], "pro", Strecke[3])

"""Verbindungssuche (direkte Zugverbindungen) über die OJP-API von opentransportdata.swiss.

Alles in einer Datei: Konfiguration, API-Verbindung, Streckenabfrage, Preisabfrage
und Benutzereingabe.
Benötigt: pip install requests

Preise kommen von der OJP-Fare-API (/ojpfare). Dafür braucht es einen eigenen Key
(separat im API Manager abonnieren). Er wird aus der Umgebungsvariable bzw. der
Datei .env (Zeile OTD_FARE_API_KEY=...) gelesen oder unten bei FARE_API_KEY eingetragen.
"""
import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo

import requests

# ============================================================== KONFIGURATION
API_KEY = "eyJvcmciOiI2NDA2NTFhNTIyZmEwNTAwMDEyOWJiZTEiLCJpZCI6IjQzZmFlNGYzODU4ZDRkMzI5ZTgyNTZlOTVmZTQzMWZlIiwiaCI6Im11cm11cjEyOCJ9"  # <- hier deinen (neuen) Key eintragen
API_URL = "https://api.opentransportdata.swiss/ojp20"
FARE_API_URL = "https://api.opentransportdata.swiss/ojpfare"
REQUESTOR_REF = "PythonRouteApp"
REQUEST_TIMEOUT = 15  # Sekunden
MAX_CONNECTIONS = 3  # so viele direkte Verbindungen werden angezeigt
PRICE_MAX_CONNECTIONS = 5  # Preisabfragen pro Suche (Limit: 50 Anfragen/Minute)
STANDARD_PRODUKT_ID = "125"  # normales Einzelbillett (Doku opentransportdata.swiss)
TZ = ZoneInfo("Europe/Zurich")
# Textdatei mit allen Suchergebnissen, im selben Ordner wie dieses Skript
RESULT_FILE = Path(__file__).parent / "verbindungen.txt"

OJP_NS = "http://www.vdv.de/ojp"
SIRI_NS = "http://www.siri.org.uk/siri"
NS = {"ojp": OJP_NS, "siri": SIRI_NS}

# Damit ein Trip beim Zurückschreiben wieder als <Trip xmlns="..."> erscheint
ET.register_namespace("", OJP_NS)
ET.register_namespace("siri", SIRI_NS)


def lese_fare_key() -> str:
    """Fare-Key aus Umgebungsvariable oder .env-Datei neben diesem Skript."""
    key = os.getenv("OTD_FARE_API_KEY", "").strip()
    env_datei = Path(__file__).parent / ".env"
    if not key and env_datei.exists():
        for zeile in env_datei.read_text(encoding="utf-8").splitlines():
            if zeile.strip().startswith("OTD_FARE_API_KEY="):
                key = zeile.split("=", 1)[1].strip().strip('"').strip("'")
    return key


# Falls keine .env vorhanden ist, wird dieser Key direkt verwendt
FARE_API_KEY = lese_fare_key() or "eyJvcmciOiI2NDA2NTFhNTIyZmEwNTAwMDEyOWJiZTEiLCJpZCI6IjhlOTQzMTRlMTgwNTQ2NjFhODcyOTZkN2U5MWZmNzY5IiwiaCI6Im11cm11cjEyOCJ9"


# ============================================================== FEHLER / DATEN
class OJPError(Exception):
    """Allgemeiner Fehler bei der API-Kommunikation."""


class AccessDeniedError(OJPError):
    """HTTP 401/403: Key fehlt, ist falsch oder nicht für diese API abonniert."""


class StopNotFoundError(OJPError):
    """Zu einem Namen wurde keine Haltestelle gefunden."""


@dataclass
class Connection:
    train_name: str
    platform: str
    departure: Optional[datetime]
    arrival: Optional[datetime]
    duration_minutes: Optional[int]
    price: Optional[float] = None  # Vollpreis 2. Klasse, einfache Fahrt, CHF
    price_error: Optional[str] = None
    trip_xml: Optional[ET.Element] = field(default=None, repr=False)


# ============================================================== API-HILFSFUNKTIONEN
def post(xml_payload: str, url: str = API_URL, api_key: str = API_KEY) -> ET.Element:
    headers = {
        "Content-Type": "application/xml",
        "Authorization": f"Bearer {api_key}",
    }
    try:
        response = requests.post(
            url,
            data=xml_payload.encode("utf-8"),
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code in (401, 403):
            raise AccessDeniedError(
                f"Zugriff verweigert (HTTP {response.status_code}). "
                "Prüfe den API-Key und ob die API abonniert ist."
            )
        response.raise_for_status()
        return ET.fromstring(response.content)
    except requests.RequestException as e:
        raise OJPError(f"Anfrage-Fehler: {e}") from e
    except ET.ParseError as e:
        raise OJPError(f"XML-Parse-Fehler: {e}") from e


def now_iso() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def parse_time(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(TZ)
    except ValueError:
        return None


def parse_duration(value: Optional[str]) -> Optional[int]:
    """Wandelt ISO-8601-Dauer (z. B. PT1H5M) in Minuten um."""
    if not value:
        return None
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?", value)
    if not match:
        return None
    return int(match.group(1) or 0) * 60 + int(match.group(2) or 0)


# ============================================================== STRECKENABFRAGE
def find_stop(name: str) -> tuple[str, str]:
    """Sucht eine Haltestelle. Gibt (StopPlaceRef, offizieller Name) zurück."""
    ts = now_iso()
    payload = f"""<?xml version="1.0" encoding="UTF-8"?>
<OJP xmlns="http://www.vdv.de/ojp" xmlns:siri="http://www.siri.org.uk/siri" version="2.0">
  <OJPRequest>
    <siri:ServiceRequest>
      <siri:RequestTimestamp>{ts}</siri:RequestTimestamp>
      <siri:RequestorRef>{REQUESTOR_REF}</siri:RequestorRef>
      <OJPLocationInformationRequest>
        <siri:RequestTimestamp>{ts}</siri:RequestTimestamp>
        <InitialInput>
          <Name>{escape(name)}</Name>
        </InitialInput>
        <Restrictions>
          <Type>stop</Type>
          <NumberOfResults>5</NumberOfResults>
        </Restrictions>
      </OJPLocationInformationRequest>
    </siri:ServiceRequest>
  </OJPRequest>
</OJP>
"""
    root = post(payload)

    candidates = []
    for place in root.findall(".//ojp:PlaceResult", NS):
        ref = place.find(".//ojp:StopPlaceRef", NS)
        label = place.find(".//ojp:StopPlaceName/ojp:Text", NS)
        if ref is not None and ref.text and label is not None and label.text:
            candidates.append((ref.text, label.text))

    if not candidates:
        raise StopNotFoundError(f"Keine Haltestelle für '{name}' gefunden.")

    # Exakter Namenstreffer bevorzugt, sonst erster Treffer
    for stop_id, label in candidates:
        if label.strip().lower() == name.strip().lower():
            return stop_id, label
    return candidates[0]


def search_direct_connections(
    origin_id: str,
    origin_label: str,
    dest_id: str,
    dest_label: str,
    max_results: int = 10,
) -> list[Connection]:
    """Gibt direkte Verbindungen (ohne Umsteigen) ab jetzt zurück.

    Zwischenhalte und Fahrplandaten (statt Echtzeit) werden mitgeladen,
    weil die Fare-API sie für die Preisberechnung braucht.
    """
    ts = now_iso()
    payload = f"""<?xml version="1.0" encoding="UTF-8"?>
<OJP xmlns="http://www.vdv.de/ojp" xmlns:siri="http://www.siri.org.uk/siri" version="2.0">
  <OJPRequest>
    <siri:ServiceRequest>
      <siri:RequestTimestamp>{ts}</siri:RequestTimestamp>
      <siri:RequestorRef>{REQUESTOR_REF}</siri:RequestorRef>
      <OJPTripRequest>
        <siri:RequestTimestamp>{ts}</siri:RequestTimestamp>
        <Origin>
          <PlaceRef>
            <StopPlaceRef>{escape(origin_id)}</StopPlaceRef>
            <Name><Text xml:lang="de">{escape(origin_label)}</Text></Name>
          </PlaceRef>
          <DepArrTime>{ts}</DepArrTime>
        </Origin>
        <Destination>
          <PlaceRef>
            <StopPlaceRef>{escape(dest_id)}</StopPlaceRef>
            <Name><Text xml:lang="de">{escape(dest_label)}</Text></Name>
          </PlaceRef>
        </Destination>
        <Params>
          <NumberOfResults>{max_results}</NumberOfResults>
          <IncludeIntermediateStops>true</IncludeIntermediateStops>
          <UseRealtimeData>none</UseRealtimeData>
        </Params>
      </OJPTripRequest>
    </siri:ServiceRequest>
  </OJPRequest>
</OJP>
"""
    root = post(payload)

    connections = []
    for trip_result in root.findall(".//ojp:TripResult", NS):
        trip = trip_result.find(".//ojp:Trip", NS)
        if trip is None:
            continue

        timed_legs = trip.findall(".//ojp:TimedLeg", NS)
        if len(timed_legs) != 1:  # nur direkte Verbindungen
            continue
        leg = timed_legs[0]

        name_elem = leg.find(".//ojp:PublishedServiceName/ojp:Text", NS)
        board = leg.find(".//ojp:LegBoard", NS)
        quay_elem = (
            board.find(".//ojp:PlannedQuay/ojp:Text", NS) if board is not None else None
        )

        connections.append(
            Connection(
                train_name=name_elem.text if name_elem is not None else "Zug",
                platform=quay_elem.text if quay_elem is not None else "Unbekannt",
                departure=parse_time(trip.findtext("ojp:StartTime", namespaces=NS)),
                arrival=parse_time(trip.findtext("ojp:EndTime", namespaces=NS)),
                duration_minutes=parse_duration(
                    trip.findtext("ojp:Duration", namespaces=NS)
                ),
                trip_xml=trip,
            )
        )
        if len(connections) >= MAX_CONNECTIONS:
            break
    return connections


# ============================================================== PREISABFRAGE
def fare_request_xml(trip: ET.Element) -> str:
    """Verpackt einen Trip in einen OJPFareRequest.

    Reisender: 1 erwachsene Person ohne Abo (leere EntitlementProducts) -> Vollpreis.
    Die leere Liste muss vorhanden sein, sonst antwortet der Dienst mit HTTP 500.
    """
    ts = now_iso()
    trip_xml = ET.tostring(trip, encoding="unicode")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<OJP xmlns="http://www.vdv.de/ojp" xmlns:siri="http://www.siri.org.uk/siri" version="2.0">
  <OJPRequest>
    <siri:ServiceRequest>
      <siri:RequestTimestamp>{ts}</siri:RequestTimestamp>
      <siri:RequestorRef>{REQUESTOR_REF}</siri:RequestorRef>
      <OJPFareRequest>
        <siri:RequestTimestamp>{ts}</siri:RequestTimestamp>
        <TripFareRequest>
          {trip_xml}
        </TripFareRequest>
        <Params>
          <FareAuthorityFilter>ch:1:NOVA</FareAuthorityFilter>
          <PassengerCategory>Adult</PassengerCategory>
          <FareClass>secondClass</FareClass>
          <Traveller>
            <PassengerCategory>Adult</PassengerCategory>
            <EntitlementProducts/>
          </Traveller>
        </Params>
      </OJPFareRequest>
    </siri:ServiceRequest>
  </OJPRequest>
</OJP>
"""


def standard_price(root: ET.Element) -> Optional[float]:
    """Normaler Einzelfahrpreis 2. Klasse aus der Fare-Antwort.

    Bevorzugt Produkt 125 (Standardbillett), sonst der höchste Preis der
    2. Klasse (Sparbillette sind günstiger und zählen nicht als Normalpreis).
    """
    second_class = []  # Liste von (Produkt-ID, Preis)
    for product in root.findall(".//ojp:FareProduct", NS):
        fare_class = (
            product.findtext("ojp:FareClass", namespaces=NS)
            or product.findtext("ojp:TravelClass", namespaces=NS)
            or ""
        ).strip().lower()
        if fare_class not in ("secondclass", "second"):
            continue
        text = product.findtext(".//ojp:Price", namespaces=NS)
        try:
            price = float(text)
        except (TypeError, ValueError):
            continue
        product_id = (product.findtext("ojp:FareProductId", namespaces=NS) or "").strip()
        second_class.append((product_id, price))

    if not second_class:
        return None
    for product_id, price in second_class:
        if product_id == STANDARD_PRODUKT_ID:
            return price
    return max(price for _, price in second_class)


def add_prices(connections: list[Connection]) -> None:
    """Fragt pro Verbindung den Preis ab. Fehler werden an der Verbindung vermerkt."""
    for c in connections[:PRICE_MAX_CONNECTIONS]:
        if c.trip_xml is None:
            continue
        try:
            root = post(fare_request_xml(c.trip_xml), FARE_API_URL, FARE_API_KEY)
            c.price = standard_price(root)
            if c.price is None:
                c.price_error = "Kein Preis in der Antwort."
        except AccessDeniedError as e:
            c.price_error = str(e)
            return  # weitere Anfragen wären auch verweigert
        except OJPError as e:
            c.price_error = str(e)


# ============================================================== EINGABE / AUSGABE
def ask_place(prompt: str) -> str:
    """Fragt einen Ortsnamen ab und wiederholt, bis die Eingabe nur Text enthält."""
    allowed_extra = set(" -.'/")
    while True:
        value = input(prompt).strip()
        if not value:
            print("  Bitte etwas eingeben.")
        elif any(ch.isdigit() for ch in value):
            print("  Ungültig: Zahlen sind nicht erlaubt.")
        elif not all(ch.isalpha() or ch in allowed_extra for ch in value):
            print("  Ungültig: Nur Buchstaben (sowie Leerzeichen, - . ' /) sind erlaubt.")
        elif not any(ch.isalpha() for ch in value):
            print("  Ungültig: Der Name muss Buchstaben enthalten.")
        else:
            return value


def fmt_time(value: Optional[datetime]) -> str:
    return value.strftime("%H:%M") if value else "?"


def fmt_duration(minutes: Optional[int]) -> str:
    if minutes is None:
        return "Unbekannt"
    hours, mins = divmod(minutes, 60)
    return (f"{hours} Std. " if hours else "") + f"{mins} Min."


def fmt_price(c: Connection) -> str:
    if c.price is not None:
        return f"CHF {c.price:.2f} (mit Halbtax CHF {c.price / 2:.2f})"
    if c.price_error:
        return f"nicht verfügbar ({c.price_error})"
    return f"nicht abgefragt (nur die ersten {PRICE_MAX_CONNECTIONS} Verbindungen)"


def format_connections(
    connections: list[Connection], origin_label: str, dest_label: str
) -> str:
    """Baut die komplette Ausgabe als Text (für Bildschirm und Textdatei)."""
    now = datetime.now(TZ)
    lines = [
        "#" * 60,
        f"Suche vom {now.strftime('%d.%m.%Y %H:%M')} Uhr",
        f"Strecke: {origin_label} -> {dest_label}",
    ]
    if not connections:
        lines.append(
            "Keine direkten Verbindungen im Ergebnis (nur Verbindungen mit Umsteigen)."
        )
        return "\n".join(lines)

    lines.append("Direkte Verbindungen:")
    lines.append("=" * 60)
    for i, c in enumerate(connections, start=1):
        lines.append(f"Verbindung #{i} ({c.train_name})")
        lines.append(f"  Abfahrt:  {fmt_time(c.departure)} Uhr (Gleis {c.platform})")
        lines.append(f"  Ankunft:  {fmt_time(c.arrival)} Uhr")
        lines.append(f"  Dauer:    {fmt_duration(c.duration_minutes)}")
        lines.append(f"  Preis:    {fmt_price(c)}")
        lines.append("-" * 60)

    prices = [c.price for c in connections if c.price is not None]
    if prices:
        cheapest = min(prices)
        lines.append("Preise: Vollpreis 2. Klasse, einfache Fahrt, 1 erwachsene Person.")
        lines.append(f"Günstigste einfache Fahrt: CHF {cheapest:.2f}")
        lines.append(
            f"Hin- und Rückfahrt:        CHF {2 * cheapest:.2f} "
            f"(mit Halbtax CHF {cheapest:.2f})"
        )
    return "\n".join(lines)


# ============================================================== TEXTDATEI
def save_result(text: str) -> None:
    """Hängt das Ergebnis an die Textdatei an (ältere Suchen bleiben erhalten)."""
    with open(RESULT_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n\n")
    print(f"\nErgebnis gespeichert in: {RESULT_FILE}")


def show_saved_results() -> None:
    """Zeigt alle früher gespeicherten Suchen aus der Textdatei an."""
    if not RESULT_FILE.exists():
        print("Noch keine gespeicherten Suchen vorhanden.")
        return
    content = RESULT_FILE.read_text(encoding="utf-8").strip()
    print(content if content else "Noch keine gespeicherten Suchen vorhanden.")


def ask_menu() -> str:
    """Startmenü: neue Suche, gespeicherte Suchen anzeigen oder beenden."""
    while True:
        print("\n1 = Neue Verbindung suchen")
        print("2 = Gespeicherte Suchen anzeigen")
        print("3 = Beenden")
        choice = input("Auswahl: ").strip()
        if choice in ("1", "2", "3"):
            return choice
        print("  Ungültig: Bitte 1, 2 oder 3 eingeben.")


def main() -> None:
    if API_KEY == "HIER_DEIN_API_KEY":
        print("Bitte zuerst oben in der Datei den API_KEY eintragen.")
        return

    while True:
        choice = ask_menu()
        if choice == "1":
            new_search()
        elif choice == "2":
            show_saved_results()
        else:
            print("Auf Wiedersehen!")
            return


def new_search() -> None:
    start = ask_place("Startort: ")
    ziel = ask_place("Zielort: ")

    try:
        origin_id, origin_label = find_stop(start)
        dest_id, dest_label = find_stop(ziel)
        print(f"Start: {origin_label} ({origin_id}) -> Ziel: {dest_label} ({dest_id})")
        now = datetime.now(TZ)
        print(f"Suche Verbindungen ab {now.strftime('%H:%M:%S')} (Schweizer Zeit)...")

        connections = search_direct_connections(
            origin_id, origin_label, dest_id, dest_label
        )
    except OJPError as e:
        print(f"Fehler: {e}")
        return

    if FARE_API_KEY == "HIER_DEIN_FARE_API_KEY":
        print("Hinweis: Kein FARE_API_KEY gefunden, Preise werden nicht abgefragt.")
        for c in connections:
            c.price_error = "kein FARE_API_KEY gefunden"
    elif connections:
        print("Frage Preise ab...")
        add_prices(connections)

    text = format_connections(connections, origin_label, dest_label)
    print("\n" + text)
    save_result(text)


if __name__ == "__main__":
    main()

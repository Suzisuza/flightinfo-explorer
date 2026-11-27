"""Flask entry point for the FlightInfo Explorer browser application."""

from flask import Flask, jsonify, render_template, request

import json
from pathlib import Path
import unicodedata

from flightinfo_api_client import (
    FlightInfoConfigurationError,
    FlightInfoServiceError,
    fetch_arrivals,
    fetch_departures_query,
    check_api_connection,
)

app = Flask(__name__)
DESTINATION_DATA_PATH = Path(__file__).parent / "data" / "city_country.json"


def _load_destination_data() -> dict:
    """Load airport-code mappings and the Swedavia destination suggestions."""
    try:
        with DESTINATION_DATA_PATH.open(encoding="utf-8") as data_file:
            data = json.load(data_file)
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError("The destination lookup file could not be read.") from error

    if not isinstance(data.get("airports"), dict) or not isinstance(data.get("destinations"), list):
        raise RuntimeError("The destination lookup file has an invalid format.")
    return data


DESTINATION_DATA = _load_destination_data()
DESTINATION_AIRPORTS = DESTINATION_DATA["airports"]
DESTINATIONS = DESTINATION_DATA["destinations"]
DESTINATION_COUNTRIES = sorted(
    {entry["country"] for entry in DESTINATIONS if entry.get("country")}
)
DESTINATION_LABELS = sorted(
    {
        f"{entry['city']}, {entry['country']}"
        for entry in DESTINATIONS
        if entry.get("city") and entry.get("country")
    }
)
DESTINATION_SEARCH_OPTIONS = sorted(set(DESTINATION_COUNTRIES + DESTINATION_LABELS))


def _normalize_destination(value: str) -> str:
    """Normalize accents and punctuation for matching API city labels."""
    folded = unicodedata.normalize("NFKD", value.casefold())
    return "".join(character for character in folded if character.isalnum())


DESTINATIONS_BY_CITY: dict[str, list[dict]] = {}
for _destination in DESTINATIONS:
    DESTINATIONS_BY_CITY.setdefault(_normalize_destination(_destination["city"]), []).append(
        _destination
    )

DESTINATION_CITY_ALIASES = {
    _normalize_destination("Munich"): "München",
    _normalize_destination("Geneva"): "Geneve",
    _normalize_destination("Palma de Mallorca"): "Palma",
    _normalize_destination("Heraklion"): "Irakleion",
    _normalize_destination("Marrakesh"): "Marrakech",
}


def _find_destination_by_city(city: str, country: str = "") -> dict | None:
    """Find one statistics destination by its city, including known aliases."""
    normalized_city = _normalize_destination(city)
    alias_city = DESTINATION_CITY_ALIASES.get(normalized_city)
    if alias_city:
        normalized_city = _normalize_destination(alias_city)
    matches = DESTINATIONS_BY_CITY.get(normalized_city, [])
    if country:
        normalized_country = _normalize_destination(country)
        matches = [
            item for item in matches
            if _normalize_destination(item["country"]) == normalized_country
        ]
    return matches[0] if len(matches) == 1 else None


def _destination_iata(flight: dict) -> str:
    """Read the destination IATA code from supported FlightInfo response shapes."""
    code = flight.get("arrivalAirportIata") or flight.get("ArrivalAirportIata")
    if code:
        return str(code).upper()

    identifier = flight.get("flightLegIdentifier") or flight.get("FlightLegIdentifier") or {}
    code = identifier.get("arrivalAirportIata") or identifier.get("ArrivalAirportIata")
    return str(code or "").upper()


def _origin_iata(flight: dict) -> str:
    """Read the origin IATA code from supported FlightInfo response shapes."""
    code = flight.get("departureAirportIata") or flight.get("DepartureAirportIata")
    if code:
        return str(code).upper()

    identifier = flight.get("flightLegIdentifier") or flight.get("FlightLegIdentifier") or {}
    code = identifier.get("departureAirportIata") or identifier.get("DepartureAirportIata")
    return str(code or "").upper()


def _add_origin_details(data: dict) -> dict:
    """Attach origin city and country labels from the local airport lookup."""
    flights = data.get("flights", data.get("Flights", []))
    if not isinstance(flights, list):
        return data

    for flight in flights:
        if not isinstance(flight, dict):
            continue
        code = _origin_iata(flight)
        origin = DESTINATION_AIRPORTS.get(code)
        if origin:
            origin = _find_destination_by_city(
                origin.get("city", ""), origin.get("country", "")
            ) or origin
        else:
            api_city = (
                flight.get("departureAirportEnglish")
                or flight.get("DepartureAirportEnglish")
                or flight.get("departureAirportSwedish")
                or flight.get("DepartureAirportSwedish")
                or ""
            )
            origin = _find_destination_by_city(str(api_city))
        if origin:
            if code:
                flight["originAirportIata"] = code
            flight["originCity"] = origin["city"]
            flight["originCountry"] = origin["country"]
        else:
            flight["originCountry"] = ""
    return data


def _add_destination_details(data: dict) -> dict:
    """Attach city and country details using airport code or API city text."""
    flights = data.get("flights", data.get("Flights", []))
    if not isinstance(flights, list):
        return data

    for flight in flights:
        if not isinstance(flight, dict):
            continue
        code = _destination_iata(flight)
        destination = DESTINATION_AIRPORTS.get(code)
        if destination:
            destination = _find_destination_by_city(
                destination.get("city", ""), destination.get("country", "")
            ) or destination
        else:
            api_city = (
                flight.get("arrivalAirportEnglish")
                or flight.get("ArrivalAirportEnglish")
                or flight.get("arrivalAirportSwedish")
                or flight.get("ArrivalAirportSwedish")
                or ""
            )
            destination = _find_destination_by_city(str(api_city))
        if destination:
            if code:
                flight["destinationAirportIata"] = code
            flight["destinationCity"] = destination["city"]
            flight["destinationCountry"] = destination["country"]
        else:
            flight["destinationCountry"] = ""
    return data


def _filter_flights_by_location(
    data: dict,
    search_text: str,
    *,
    city_field: str,
    country_field: str,
    filter_prefix: str,
) -> tuple[dict, str]:
    """Filter flight records by an exact country or city-country suggestion."""
    normalized = search_text.casefold()
    country_by_name = {name.casefold(): name for name in DESTINATION_COUNTRIES}
    flights = data.get("flights", data.get("Flights", []))

    if normalized in country_by_name:
        selected_country = country_by_name[normalized]
        data["flights"] = [
            flight
            for flight in flights
            if isinstance(flight, dict)
            and flight.get(country_field, "").casefold() == normalized
        ]
        data["numberOfFlights"] = len(data["flights"])
        data[f"{filter_prefix}CountryFilter"] = selected_country
        data[f"{filter_prefix}Filter"] = selected_country
        return data, selected_country

    city_by_label = {
        f"{entry['city']}, {entry['country']}".casefold(): (entry["city"], entry["country"])
        for entry in DESTINATIONS
        if entry.get("city") and entry.get("country")
    }
    if normalized not in city_by_label:
        raise ValueError("Choose a city or country from the suggestions.")

    selected_city, selected_country = city_by_label[normalized]
    data["flights"] = [
        flight
        for flight in flights
        if isinstance(flight, dict)
        and _normalize_destination(flight.get(city_field, ""))
        == _normalize_destination(selected_city)
        and _normalize_destination(flight.get(country_field, ""))
        == _normalize_destination(selected_country)
    ]
    data["numberOfFlights"] = len(data["flights"])
    filter_label = f"{selected_city}, {selected_country}"
    data[f"{filter_prefix}Filter"] = filter_label
    return data, filter_label


def _filter_departures_by_destination(data: dict, search_text: str) -> tuple[dict, str]:
    """Apply a destination country or city filter to departures."""
    return _filter_flights_by_location(
        data,
        search_text,
        city_field="destinationCity",
        country_field="destinationCountry",
        filter_prefix="destination",
    )


def _filter_arrivals_by_origin(data: dict, search_text: str) -> tuple[dict, str]:
    """Apply an origin country or city filter to arrivals."""
    return _filter_flights_by_location(
        data,
        search_text,
        city_field="originCity",
        country_field="originCountry",
        filter_prefix="origin",
    )


@app.get("/")
def home():
    """Render the application dashboard."""
    return render_template(
        "index.html", destination_search_options=DESTINATION_SEARCH_OPTIONS
    )


@app.get("/api/arrivals")
def arrivals():
    """Return arrivals, optionally filtered by their origin city or country."""
    airport = request.args.get("airport", "")
    flight_date = request.args.get("date", "")
    origin_search = (
        request.args.get("destination", "") or request.args.get("country", "")
    ).strip()

    if not airport or not flight_date:
        return jsonify(error="Choose an airport and date."), 400

    if origin_search and origin_search.casefold() not in {
        option.casefold() for option in DESTINATION_SEARCH_OPTIONS
    }:
        return jsonify(
            error="Choose a city or country from the suggestions."
        ), 400

    try:
        data = fetch_arrivals(airport, flight_date)
        if origin_search:
            data = _add_origin_details(data)
            data, _ = _filter_arrivals_by_origin(data, origin_search)
    except ValueError as error:
        return jsonify(error=str(error)), 400
    except FlightInfoConfigurationError as error:
        return jsonify(error=str(error)), 503
    except FlightInfoServiceError as error:
        return jsonify(error=str(error)), error.status_code

    return jsonify(data)


@app.get("/api/departures")
def departures():
    """Return OData departures, optionally filtered by destination or country."""
    airport = request.args.get("airport", "")
    flight_date = request.args.get("date", "")
    destination_search = (
        request.args.get("destination", "") or request.args.get("country", "")
    ).strip()

    if not airport or not flight_date:
        return jsonify(error="Choose an airport and date."), 400

    if destination_search and destination_search.casefold() not in {
        option.casefold() for option in DESTINATION_SEARCH_OPTIONS
    }:
        return jsonify(
            error="Choose a city or country from the suggestions."
        ), 400

    try:
        data = fetch_departures_query(airport, flight_date)
        data = _add_destination_details(data)
        if destination_search:
            data, _ = _filter_departures_by_destination(data, destination_search)
    except ValueError as error:
        return jsonify(error=str(error)), 400
    except FlightInfoConfigurationError as error:
        return jsonify(error=str(error)), 503
    except FlightInfoServiceError as error:
        return jsonify(error=str(error)), error.status_code

    return jsonify(data)


@app.get("/api/heartbeat")
def heartbeat():
    """Check that the public FlightInfo API can answer a lightweight request."""
    try:
        check_api_connection()
    except FlightInfoConfigurationError as error:
        return jsonify(status="unavailable", message=str(error)), 503
    except FlightInfoServiceError as error:
        return jsonify(status="unavailable", message=str(error)), error.status_code

    return jsonify(status="connected", message="The FlightInfo API is responding.")


if __name__ == "__main__":
    app.run(debug=True)

"""Flask entry point for the FlightInfo Explorer browser application."""

from flask import Flask, jsonify, render_template, request

import json
from pathlib import Path

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
    """Load the local IATA-to-city-and-country lookup used by the page."""
    try:
        with DESTINATION_DATA_PATH.open(encoding="utf-8") as data_file:
            data = json.load(data_file)
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError("The destination lookup file could not be read.") from error

    airports = data.get("airports")
    if not isinstance(airports, dict):
        raise RuntimeError("The destination lookup file has an invalid format.")
    return airports


DESTINATION_AIRPORTS = _load_destination_data()
DESTINATION_COUNTRIES = sorted(
    {entry["country"] for entry in DESTINATION_AIRPORTS.values() if entry.get("country")}
)


def _destination_iata(flight: dict) -> str:
    """Read the destination IATA code from supported FlightInfo response shapes."""
    code = flight.get("arrivalAirportIata") or flight.get("ArrivalAirportIata")
    if code:
        return str(code).upper()

    identifier = flight.get("flightLegIdentifier") or flight.get("FlightLegIdentifier") or {}
    code = identifier.get("arrivalAirportIata") or identifier.get("ArrivalAirportIata")
    return str(code or "").upper()


def _add_destination_details(data: dict) -> dict:
    """Attach local city and country names to each departure record."""
    flights = data.get("flights", data.get("Flights", []))
    if not isinstance(flights, list):
        return data

    for flight in flights:
        if not isinstance(flight, dict):
            continue
        code = _destination_iata(flight)
        destination = DESTINATION_AIRPORTS.get(code)
        if destination:
            flight["destinationAirportIata"] = code
            flight["destinationCity"] = destination["city"]
            flight["destinationCountry"] = destination["country"]
        else:
            flight["destinationCountry"] = ""
    return data


@app.get("/")
def home():
    """Render the application dashboard."""
    return render_template(
        "index.html", destination_countries=DESTINATION_COUNTRIES
    )


@app.get("/api/arrivals")
def arrivals():
    """Return arrivals for a selected airport and UTC date."""
    airport = request.args.get("airport", "")
    flight_date = request.args.get("date", "")

    if not airport or not flight_date:
        return jsonify(error="Choose an airport and date."), 400

    try:
        data = fetch_arrivals(airport, flight_date)
    except ValueError as error:
        return jsonify(error=str(error)), 400
    except FlightInfoConfigurationError as error:
        return jsonify(error=str(error)), 503
    except FlightInfoServiceError as error:
        return jsonify(error=str(error)), error.status_code

    return jsonify(data)


@app.get("/api/departures")
def departures():
    """Return OData departures, optionally filtered by destination country."""
    airport = request.args.get("airport", "")
    flight_date = request.args.get("date", "")
    country = request.args.get("country", "").strip()

    if not airport or not flight_date:
        return jsonify(error="Choose an airport and date."), 400

    if country and country.casefold() not in {
        name.casefold() for name in DESTINATION_COUNTRIES
    }:
        return jsonify(error="Choose a country from the destination list."), 400

    try:
        data = fetch_departures_query(airport, flight_date)
        data = _add_destination_details(data)
    except ValueError as error:
        return jsonify(error=str(error)), 400
    except FlightInfoConfigurationError as error:
        return jsonify(error=str(error)), 503
    except FlightInfoServiceError as error:
        return jsonify(error=str(error)), error.status_code

    if country:
        flights = data.get("flights", data.get("Flights", []))
        filtered_flights = [
            flight
            for flight in flights
            if isinstance(flight, dict)
            and flight.get("destinationCountry", "").casefold() == country.casefold()
        ]
        data["flights"] = filtered_flights
        data["numberOfFlights"] = len(filtered_flights)
        data["destinationCountryFilter"] = country

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

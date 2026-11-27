"""Small server-side client for the public FlightInfo API v2."""

from __future__ import annotations

import json
import os
from datetime import date, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_BASE_URL = "https://api.swedavia.se/flightinfo/v2"
SUPPORTED_AIRPORTS = {"ARN", "GOT", "BMA", "MMX", "LLA", "UME", "KRN", "RNB", "VBY", "OSD"}
REQUEST_TIMEOUT_SECONDS = 15


class FlightInfoConfigurationError(Exception):
    """Raised when the local subscription key is missing or empty."""


class FlightInfoServiceError(Exception):
    """Raised when the FlightInfo service cannot return usable data."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


def _key_file_candidates() -> list[Path]:
    """Return expected local key-file paths without exposing their contents."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        secret_folder = Path(local_app_data) / "FlightInfoSecrets"
    else:
        secret_folder = Path.home() / "AppData" / "Local" / "FlightInfoSecrets"

    return [
        secret_folder / "swedavia_api_key_primary.txt",
        secret_folder / "swedavia_primary_key.txt",
        secret_folder / "swedavia_secondary_key.txt",
        secret_folder / "swedavia_api_key.txt",
    ]


def load_subscription_key() -> str:
    """Read one locally saved key; prefer Primary and never read both at once."""
    for key_file in _key_file_candidates():
        if key_file.is_file():
            key = key_file.read_text(encoding="utf-8").strip()
            if key:
                return key
            raise FlightInfoConfigurationError(
                f"The saved API key file is empty: {key_file.name}"
            )

    raise FlightInfoConfigurationError(
        "No FlightInfo key file was found in the local FlightInfoSecrets folder."
    )


def validate_arrival_request(airport: str, flight_date: str) -> tuple[str, str]:
    """Validate the airport and ISO date before building the API request."""
    airport_code = airport.strip().upper()
    if airport_code not in SUPPORTED_AIRPORTS:
        supported = ", ".join(sorted(SUPPORTED_AIRPORTS))
        raise ValueError(f"Choose one of the supported airports: {supported}.")

    try:
        parsed_date = date.fromisoformat(flight_date)
    except (TypeError, ValueError) as error:
        raise ValueError("Enter a date in YYYY-MM-DD format.") from error

    if parsed_date.isoformat() != flight_date:
        raise ValueError("Enter a date in YYYY-MM-DD format.")

    return airport_code, parsed_date.isoformat()


def _fetch_api_json(url: str) -> dict | list:
    """Send an authenticated GET request and parse its JSON response."""
    subscription_key = load_subscription_key()
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "Ocp-Apim-Subscription-Key": subscription_key,
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            payload = response.read().decode("utf-8")
    except HTTPError as error:
        if error.code in (401, 403):
            raise FlightInfoServiceError(
                "The API rejected the subscription key. Check the saved key and FlightInfo subscription.",
                status_code=error.code,
            ) from error
        if error.code == 429:
            raise FlightInfoServiceError(
                "The FlightInfo request limit has been reached. Try again later.",
                status_code=429,
            ) from error
        raise FlightInfoServiceError(
            f"The FlightInfo service returned HTTP {error.code}.",
            status_code=error.code,
        ) from error
    except URLError as error:
        raise FlightInfoServiceError(
            "The FlightInfo service could not be reached. Check your internet connection and try again."
        ) from error
    except TimeoutError as error:
        raise FlightInfoServiceError(
            "The FlightInfo service took too long to respond. Try again."
        ) from error

    try:
        data = json.loads(payload)
    except json.JSONDecodeError as error:
        raise FlightInfoServiceError(
            "The FlightInfo service returned a response that was not valid JSON."
        ) from error

    if not isinstance(data, (dict, list)):
        raise FlightInfoServiceError(
            "The FlightInfo service returned an unexpected response format."
        )

    return data


def _fetch_flights(direction: str, airport: str, flight_date: str) -> dict:
    """Fetch arrivals or departures through the documented v2 endpoint."""
    if direction not in {"arrivals", "departures"}:
        raise ValueError("Choose arrivals or departures.")

    airport_code, requested_date = validate_arrival_request(airport, flight_date)
    return _fetch_api_json(
        f"{API_BASE_URL}/{airport_code}/{direction}/{requested_date}"
    )


def _normalize_query_response(data: dict | list) -> dict:
    """Return OData departure records in the shape used by the web page.

    The query response can wrap each flight in separate ``arrival`` and
    ``departure`` objects. The departure board needs the departure object,
    which contains the route, time, airline, and status fields.
    """
    if isinstance(data, list):
        flights = data
        response = {}
    else:
        response = dict(data)
        flights = response.get("flights", response.get("Flights", []))

    if not isinstance(flights, list):
        raise FlightInfoServiceError(
            "The OData query returned an unexpected flight list."
        )

    normalized_flights = []
    for flight in flights:
        if not isinstance(flight, dict):
            normalized_flights.append(flight)
            continue

        # FlightInfo's OData response may wrap each journey leg in an object.
        # For this departure query, select the departure leg for the board.
        departure = flight.get("departure", flight.get("Departure"))
        if isinstance(departure, dict):
            normalized_flights.append({**flight, **departure})
        else:
            # Keep the flat form supported for existing API responses/tests.
            normalized_flights.append(flight)

    response["flights"] = normalized_flights
    response["numberOfFlights"] = len(normalized_flights)
    return response


def _build_departure_filter(airport: str, flight_date: str) -> str:
    """Build the documented OData filter for one airport, date and direction."""
    airport_code, requested_date = validate_arrival_request(airport, flight_date)
    scheduled_date = date.fromisoformat(requested_date).strftime("%y%m%d")
    return (
        f"airport eq '{airport_code}' and scheduled eq '{scheduled_date}' "
        "and flightType eq 'D'"
    )


def fetch_departures_query(airport: str, flight_date: str) -> dict:
    """Fetch departures using FlightInfo's documented OData query endpoint."""
    filter_expression = _build_departure_filter(airport, flight_date)
    query = urlencode({"filter": filter_expression, "count": "1000"})
    data = _fetch_api_json(f"{API_BASE_URL}/query?{query}")
    return _normalize_query_response(data)


def check_api_connection() -> None:
    """Probe the public API with one small OData request.

    The portal's separate heartBeat operation is described as internal use only,
    so this check uses the public query endpoint instead.
    """
    # Use the computer's local date so the check works on Windows without
    # requiring an external time-zone database package.
    today = datetime.now().astimezone().date()
    filter_expression = _build_departure_filter("ARN", today.isoformat())
    query = urlencode({"filter": filter_expression, "count": "1"})
    data = _fetch_api_json(f"{API_BASE_URL}/query?{query}")
    _normalize_query_response(data)


def fetch_arrivals(airport: str, flight_date: str) -> dict:
    """Fetch arrivals through the documented public v2 endpoint."""
    return _fetch_flights("arrivals", airport, flight_date)


def fetch_departures(airport: str, flight_date: str) -> dict:
    """Fetch departures through the documented public v2 endpoint."""
    return _fetch_flights("departures", airport, flight_date)

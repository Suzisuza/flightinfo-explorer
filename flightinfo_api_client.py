"""Small server-side client for the public FlightInfo API v2."""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
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


def _fetch_flights(direction: str, airport: str, flight_date: str) -> dict:
    """Fetch flights through a documented public v2 endpoint."""
    if direction not in {"arrivals", "departures"}:
        raise ValueError("Choose arrivals or departures.")

    airport_code, requested_date = validate_arrival_request(airport, flight_date)
    subscription_key = load_subscription_key()
    request = Request(
        f"{API_BASE_URL}/{airport_code}/{direction}/{requested_date}",
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
            status_code=502,
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

    if not isinstance(data, dict):
        raise FlightInfoServiceError(
            "The FlightInfo service returned an unexpected response format."
        )

    return data


def fetch_arrivals(airport: str, flight_date: str) -> dict:
    """Fetch arrivals through the documented public v2 endpoint."""
    return _fetch_flights("arrivals", airport, flight_date)


def fetch_departures(airport: str, flight_date: str) -> dict:
    """Fetch departures through the documented public v2 endpoint."""
    return _fetch_flights("departures", airport, flight_date)

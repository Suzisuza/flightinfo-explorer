import json
import os
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from unittest.mock import MagicMock, patch

from flightinfo_app import FlightInfoServiceError, app
from flightinfo_api_client import (
    check_api_connection,
    fetch_arrivals,
    fetch_departures,
    fetch_departures_query,
)


class HomePageTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_homepage_renders_feature_overview(self):
        response = self.client.get("/")
        try:
            self.assertEqual(response.status_code, 200)
            page = response.get_data(as_text=True)
            self.assertNotIn("Swedavia", page)
            self.assertIn("Your flight journey", page)
            self.assertIn("FlightInfo Explorer", page)
            self.assertIn('id="arrival-search"', page)
            self.assertIn('id="arrival-list"', page)
            self.assertNotIn('id="arrival-data"', page)
            self.assertIn('data-airport="ARN"', page)
            self.assertIn("10 airports to explore", page)
            for airport_code in ("KRN", "RNB", "VBY", "OSD"):
                self.assertIn(f'data-airport="{airport_code}"', page)
            self.assertNotIn('data-airport="SFT"', page)
            self.assertIn('data-flight-mode="arrivals"', page)
            self.assertIn('data-flight-mode="departures"', page)
            self.assertIn('role="tablist"', page)
            self.assertIn('id="departures-tab"', page)
            self.assertIn('id="flight-pagination"', page)
            self.assertIn('id="previous-page"', page)
            self.assertIn('id="next-page"', page)
            self.assertIn('id="flight-date"', page)
            self.assertIn("10 airports to explore", page)
            self.assertNotIn("YOUR FLIGHT JOURNEY", page)
            self.assertIn('class="journey-plane"', page)
            for airport in ("ARN", "GOT", "BMA", "MMX", "LLA", "UME", "KRN", "RNB", "VBY", "OSD"):
                with self.subTest(airport=airport):
                    self.assertIn(airport, page)
            self.assertNotIn("airport-chip-active", page)
            self.assertNotIn("+ 6 more", page)
            for label in ("Arrivals", "Departures", "Find a flight", "API connection"):
                with self.subTest(label=label):
                    self.assertIn(label, page)
            self.assertNotIn("OData query", page)
            self.assertIn("Filter departures by country", page)
            self.assertIn('id="destination-country"', page)
            self.assertIn('type="search"', page)
            self.assertIn('list="destination-countries"', page)
            self.assertIn('<datalist id="destination-countries">', page)
            self.assertIn('id="check-api-button"', page)
            self.assertNotIn("Quick demo", page)
            self.assertNotIn("In development", page)
            self.assertNotIn("coming soon", page.lower())
            self.assertNotIn("Research build", page)
        finally:
            response.close()

    def test_arrivals_route_requires_airport_and_date(self):
        response = self.client.get("/api/arrivals")
        try:
            self.assertEqual(response.status_code, 400)
            self.assertIn("error", response.get_json())
        finally:
            response.close()

    @patch("flightinfo_app.fetch_arrivals")
    def test_arrivals_route_returns_service_data(self, fetch_mock):
        expected = {"NumberOfFlights": 0, "Flights": []}
        fetch_mock.return_value = expected

        response = self.client.get("/api/arrivals?airport=ARN&date=2026-11-26")
        try:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), expected)
            fetch_mock.assert_called_once_with("ARN", "2026-11-26")
        finally:
            response.close()

    @patch("flightinfo_app.fetch_arrivals", side_effect=ValueError("Choose one of the supported airports."))
    def test_arrivals_route_returns_validation_message(self, _fetch_mock):
        response = self.client.get("/api/arrivals?airport=SFT&date=2026-11-26")
        try:
            self.assertEqual(response.status_code, 400)
            self.assertIn("supported airports", response.get_json()["error"])
        finally:
            response.close()

    @patch("flightinfo_app.fetch_departures_query")
    def test_departures_route_returns_service_data(self, fetch_mock):
        expected = {"flights": [], "numberOfFlights": 0}
        fetch_mock.return_value = expected

        response = self.client.get("/api/departures?airport=ARN&date=2026-11-26")
        try:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), expected)
            fetch_mock.assert_called_once_with("ARN", "2026-11-26")
        finally:
            response.close()

    @patch("flightinfo_app.fetch_departures_query")
    def test_departures_route_filters_by_mapped_destination_country(self, fetch_mock):
        fetch_mock.return_value = {
            "flights": [
                {"flightId": "KL1100", "flightLegIdentifier": {"arrivalAirportIata": "AMS"}},
                {"flightId": "BA770", "flightLegIdentifier": {"arrivalAirportIata": "LHR"}},
            ],
            "numberOfFlights": 2,
        }

        response = self.client.get(
            "/api/departures?airport=ARN&date=2026-11-26&country=Netherlands"
        )
        try:
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data["numberOfFlights"], 1)
            self.assertEqual(data["destinationCountryFilter"], "Netherlands")
            self.assertEqual(data["flights"][0]["destinationCity"], "Amsterdam")
            self.assertEqual(data["flights"][0]["destinationCountry"], "Netherlands")
        finally:
            response.close()

    @patch("flightinfo_app.fetch_departures_query")
    def test_departures_route_rejects_country_not_in_destination_list(self, fetch_mock):
        response = self.client.get(
            "/api/departures?airport=ARN&date=2026-11-26&country=Atlantis"
        )
        try:
            self.assertEqual(response.status_code, 400)
            fetch_mock.assert_not_called()
        finally:
            response.close()

    @patch("flightinfo_app.check_api_connection")
    def test_heartbeat_route_reports_connected(self, heartbeat_mock):
        response = self.client.get("/api/heartbeat")
        try:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json()["status"], "connected")
            heartbeat_mock.assert_called_once_with()
        finally:
            response.close()

    @patch("flightinfo_app.check_api_connection", side_effect=FlightInfoServiceError("The API is unavailable."))
    def test_heartbeat_route_reports_api_failure(self, _heartbeat_mock):
        response = self.client.get("/api/heartbeat")
        try:
            self.assertEqual(response.status_code, 502)
            self.assertEqual(response.get_json()["status"], "unavailable")
        finally:
            response.close()

    def test_stylesheet_is_served(self):
        response = self.client.get("/static/flightinfo_design.css")
        try:
            self.assertEqual(response.status_code, 200)
            css = response.get_data(as_text=True)
            self.assertIn(".feature-grid", css)
            self.assertIn(".airport-chip:hover", css)
            self.assertIn(".flight-row", css)
            self.assertIn(".arrival-list", css)
            self.assertIn(".flight-mode-tab[aria-selected=\"true\"]", css)
            self.assertIn(".flight-pagination[hidden]", css)
            self.assertIn(".country-filter input", css)
            self.assertIn(".pagination-button", css)
            hover_rule = css.split(".airport-chip:hover {", 1)[1].split("}", 1)[0]
            self.assertIn("background-color: gold", hover_rule)
            self.assertIn("background: #e3f4fa", css)
            body_rule = css.split("body {", 1)[1].split("}", 1)[0]
            self.assertIn("color: black", body_rule)
            airport_panel = css.split(".airport-panel {", 1)[1].split("}", 1)[0]
            feature_card = css.split(".feature-card {", 1)[1].split("}", 1)[0]
            self.assertIn("background: lightskyblue", airport_panel)
            self.assertIn("background: lightskyblue", feature_card)
            base_chip = css.split(".airport-chip {", 1)[1].split("}", 1)[0]
            self.assertIn("background: #ffffff", base_chip)
            self.assertIn("border: 1px solid #75c6dd", base_chip)
        finally:
            response.close()

    def test_decorative_images_are_served(self):
        image_paths = (
            "/static/images/header-plane.png",
            "/static/images/travel-suitcase.png",
            "/static/images/palm-island.png",
        )

        for path in image_paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                try:
                    self.assertEqual(response.status_code, 200)
                    self.assertTrue(response.data)
                finally:
                    response.close()

    def test_flight_search_script_paginates_50_records(self):
        response = self.client.get("/static/flight_search.js")
        try:
            self.assertEqual(response.status_code, 200)
            script = response.get_data(as_text=True)
            self.assertIn("const flightsPerPage = 50", script)
            self.assertIn("function renderFlightPage()", script)
        finally:
            response.close()


class FlightInfoClientTests(unittest.TestCase):
    def test_fetch_arrivals_uses_saved_primary_key_and_documented_url(self):
        with tempfile.TemporaryDirectory() as temporary_folder:
            secret_folder = Path(temporary_folder) / "FlightInfoSecrets"
            secret_folder.mkdir()
            key_file = secret_folder / "swedavia_primary_key.txt"
            key_file.write_text("test-key-only-for-unit-test", encoding="utf-8")

            mocked_response = MagicMock()
            mocked_response.__enter__.return_value = mocked_response
            mocked_response.read.return_value = json.dumps(
                {"NumberOfFlights": 0, "Flights": []}
            ).encode("utf-8")

            with patch.dict(os.environ, {"LOCALAPPDATA": temporary_folder}):
                with patch("flightinfo_api_client.urlopen", return_value=mocked_response) as urlopen_mock:
                    data = fetch_arrivals("ARN", "2026-11-26")

            request = urlopen_mock.call_args.args[0]
            self.assertEqual(
                request.full_url,
                "https://api.swedavia.se/flightinfo/v2/ARN/arrivals/2026-11-26",
            )
            self.assertEqual(request.get_method(), "GET")
            self.assertEqual(
                request.get_header("Ocp-apim-subscription-key"),
                "test-key-only-for-unit-test",
            )
            self.assertEqual(data, {"NumberOfFlights": 0, "Flights": []})

    def test_fetch_departures_uses_the_documented_departures_url(self):
        with tempfile.TemporaryDirectory() as temporary_folder:
            secret_folder = Path(temporary_folder) / "FlightInfoSecrets"
            secret_folder.mkdir()
            (secret_folder / "swedavia_primary_key.txt").write_text(
                "test-key-only-for-unit-test", encoding="utf-8"
            )

            mocked_response = MagicMock()
            mocked_response.__enter__.return_value = mocked_response
            mocked_response.read.return_value = json.dumps(
                {"NumberOfFlights": 0, "Flights": []}
            ).encode("utf-8")

            with patch.dict(os.environ, {"LOCALAPPDATA": temporary_folder}):
                with patch("flightinfo_api_client.urlopen", return_value=mocked_response) as urlopen_mock:
                    data = fetch_departures("ARN", "2026-11-26")

            request = urlopen_mock.call_args.args[0]
            self.assertEqual(
                request.full_url,
                "https://api.swedavia.se/flightinfo/v2/ARN/departures/2026-11-26",
            )
            self.assertEqual(data, {"NumberOfFlights": 0, "Flights": []})

    def test_fetch_departures_query_uses_documented_odata_parameters(self):
        with tempfile.TemporaryDirectory() as temporary_folder:
            secret_folder = Path(temporary_folder) / "FlightInfoSecrets"
            secret_folder.mkdir()
            (secret_folder / "swedavia_primary_key.txt").write_text(
                "test-key-only-for-unit-test", encoding="utf-8"
            )

            mocked_response = MagicMock()
            mocked_response.__enter__.return_value = mocked_response
            mocked_response.read.return_value = json.dumps(
                {"Flights": [{"flightId": "SK123"}], "continuationtoken": "next"}
            ).encode("utf-8")

            with patch.dict(os.environ, {"LOCALAPPDATA": temporary_folder}):
                with patch("flightinfo_api_client.urlopen", return_value=mocked_response) as urlopen_mock:
                    data = fetch_departures_query("ARN", "2026-11-26")

            request = urlopen_mock.call_args.args[0]
            self.assertEqual(request.get_method(), "GET")
            self.assertEqual(
                request.get_header("Ocp-apim-subscription-key"),
                "test-key-only-for-unit-test",
            )
            self.assertEqual(
                urlsplit(request.full_url).path,
                "/flightinfo/v2/query",
            )
            parameters = parse_qs(urlsplit(request.full_url).query)
            self.assertEqual(
                parameters["filter"][0],
                "airport eq 'ARN' and scheduled eq '261126' and flightType eq 'D'",
            )
            self.assertEqual(parameters["count"], ["1000"])
            self.assertEqual(data["flights"], [{"flightId": "SK123"}])
            self.assertEqual(data["numberOfFlights"], 1)
            self.assertEqual(data["continuationtoken"], "next")

    def test_api_connection_check_uses_one_public_odata_result(self):
        with tempfile.TemporaryDirectory() as temporary_folder:
            secret_folder = Path(temporary_folder) / "FlightInfoSecrets"
            secret_folder.mkdir()
            (secret_folder / "swedavia_primary_key.txt").write_text(
                "test-key-only-for-unit-test", encoding="utf-8"
            )

            mocked_response = MagicMock()
            mocked_response.__enter__.return_value = mocked_response
            mocked_response.read.return_value = json.dumps(
                {"flights": [], "continuationtoken": "next"}
            ).encode("utf-8")

            with patch.dict(os.environ, {"LOCALAPPDATA": temporary_folder}):
                with patch("flightinfo_api_client.urlopen", return_value=mocked_response) as urlopen_mock:
                    check_api_connection()

            request = urlopen_mock.call_args.args[0]
            parameters = parse_qs(urlsplit(request.full_url).query)
            self.assertEqual(parameters["count"], ["1"])
            self.assertIn("flightType eq 'D'", parameters["filter"][0])

    def test_fetch_arrivals_rejects_unsupported_airport_before_network(self):
        with patch("flightinfo_api_client.urlopen") as urlopen_mock:
            with self.assertRaisesRegex(ValueError, "supported airports"):
                fetch_arrivals("SFT", "2026-11-26")
        urlopen_mock.assert_not_called()

    def test_fetch_arrivals_rejects_invalid_date_before_network(self):
        with patch("flightinfo_api_client.urlopen") as urlopen_mock:
            with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
                fetch_arrivals("ARN", "26-11-2026")
        urlopen_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()

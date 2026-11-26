"""Flask entry point for the FlightInfo Explorer browser application."""

from flask import Flask, jsonify, render_template, request

from flightinfo_api_client import (
    FlightInfoConfigurationError,
    FlightInfoServiceError,
    fetch_arrivals,
    fetch_departures,
)

app = Flask(__name__)


@app.get("/")
def home():
    """Render the application dashboard."""
    return render_template("index.html")


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
    """Return departures for a selected airport and UTC date."""
    airport = request.args.get("airport", "")
    flight_date = request.args.get("date", "")

    if not airport or not flight_date:
        return jsonify(error="Choose an airport and date."), 400

    try:
        data = fetch_departures(airport, flight_date)
    except ValueError as error:
        return jsonify(error=str(error)), 400
    except FlightInfoConfigurationError as error:
        return jsonify(error=str(error)), 503
    except FlightInfoServiceError as error:
        return jsonify(error=str(error)), error.status_code

    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True)

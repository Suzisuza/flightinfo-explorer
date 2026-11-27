# Project Summary

FlightInfo Explorer is a browser application built with Python, Flask, HTML, CSS, and JavaScript. It retrieves arrivals and departures from the Swedavia FlightInfo API v2 and presents the results as readable flight cards.

Users can choose from ten Swedavia airports, select a date and flight direction, browse results 50 at a time, and filter departures by destination country. A local JSON lookup maps common destination airport codes to city and country names. The page also provides an API connection check using a small public OData query.

The application uses documented FlightInfo operations, including the OData query endpoint for departures. The destination lookup is a curated starter dataset, not a complete or official Swedavia route list; destinations absent from the file cannot be assigned to a country filter.

On Windows, `start_flightinfo.bat` prepares the local Python environment, installs dependencies, starts Flask, and opens the browser. Live API features require the user to save their own subscription key outside the project. No key is included in the repository.

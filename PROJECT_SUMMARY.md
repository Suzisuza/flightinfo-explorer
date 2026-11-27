# Project Summary

FlightInfo Explorer is a browser-based reverse-engineering project built with Python, Flask, HTML, CSS, and JavaScript. It uses the Swedavia FlightInfo API v2 to display arrivals and departures as readable flight cards.

Users choose an airport, date, and flight direction. They can view all returned flights or filter arrivals by origin and departures by destination. Results are ordered by scheduled time and shown 50 per page. A local JSON file supplies airport labels and city/country suggestions based on Swedavia's 2025 destination statistics.

Arrivals use the documented FlightInfo operation. Departures use the documented OData query. A local subscription key, stored outside the project folder, is required for live API searches.

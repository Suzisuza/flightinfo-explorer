# Project Summary

FlightInfo Explorer is a browser-based reverse-engineering project built with Python, Flask, HTML, CSS, and JavaScript. It uses the Swedavia FlightInfo API v2 to retrieve arrivals and departures and present them as readable flight cards.

Users can select one of ten Swedavia airports, choose a date and flight direction, browse 50 results per page, and type a destination or country to filter departures. The local JSON suggestion list contains 255 city-country pairs in 51 countries, based on Swedavia's 2025 destination statistics. It includes every European destination listed in that source and selected destinations from Africa, Asia, North America, and South America. The source does not list a destination in Oceania with passenger traffic during 2025.

Departures use the documented OData query operation. The app also provides an API connection check. A local subscription key is required for live API searches and is stored outside the project folder.

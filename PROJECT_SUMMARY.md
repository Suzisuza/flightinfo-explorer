# Project Summary

FlightInfo Explorer is a browser application built with Python, Flask, HTML, CSS, and JavaScript. It uses the Swedavia FlightInfo API v2 to retrieve arrivals and departures for a selected airport and date. The page offers ten Swedavia airport choices.

The Flask backend reads the API subscription key from a local secret file outside the project folder and requests the flight data. The browser displays readable flight cards, orders them by scheduled time, shows times in Stockholm local time, and presents up to 50 flights per page.

On Windows, start_flightinfo.bat prepares the local Python environment, installs the listed dependencies, starts the Flask server, and opens the browser. Live searches require the user to provide their own local API key; no key is included in the project.

The implemented search features are arrivals and departures. Individual flight lookup and the API status card are not implemented. The automated test suite has 12 passing tests.

# FlightInfo Explorer — Project Documentation

## 1. Project purpose

FlightInfo Explorer is a school project based on the reverse-engineering assignment. The reference application and supplied video were examined to infer the visible features, required inputs, and likely data flow. The project recreates that flight-search experience as a browser application. It is an independent project and is not an official Swedavia product.

## 2. Research and requirements

The reference showed airport and date selection, Arrivals and Departures views, scheduled-time ordering, and destination search. The assignment asks the student to inspect an existing result, infer inputs and processing, sketch the logic, and build an application with similar output.

The Swedavia FlightInfo API v2 guide was reviewed before implementation. It documents the arrivals and departures operations and the public OData query. Departures in this project use the documented OData query filtered by airport, scheduled date, and flight type. The local city/country suggestions are based on Swedavia's [2025 destination statistics](https://www.swedavia.se/contentassets/95dc75e405f0460fb852949b4b7cb09f/destinations-statistik-2025.xlsx).

The application requirements were:

- Provide a browser interface with ten airport choices and a date field.
- Let the user switch between arrivals and departures.
- Show readable flight cards ordered by scheduled time, 50 per page.
- Filter arrivals by origin city or country and departures by destination city or country.
- Use the documented OData query for departures and provide a way to check API connectivity.
- Keep the API key outside the project files.

## 3. Design and implementation

Python and Flask handle server routes and API calls. HTML defines the page, CSS handles its appearance, JavaScript manages browser interaction, and JSON stores the airport and destination lookup.

For a search, JavaScript sends the selected airport, date, direction, and optional location to Flask. Flask validates the input and calls `flightinfo_api_client.py`. The API client reads the local subscription key and sends the request to FlightInfo. The response is JSON. The client normalizes wrapped OData departure records, and Flask maps city/country details for local filtering. JavaScript turns the returned fields into flight cards, sorts them by scheduled time, and paginates them.

The search suggestions remain hidden until the user types and only show labels beginning with the entered text. Leaving the search field empty displays all flights returned for the selected airport, date, and direction. The local dataset contains 254 city/country pairs across 51 countries, based on the 2025 statistics; historical statistics do not guarantee that a route operates on a chosen date.

The **Check connection** control makes a small authenticated public OData request. It checks whether the public API request succeeds at that time; it does not call the portal's internal `heartBeat` operation.

## 4. Main project files

| File or folder | Role |
|---|---|
| `start_flightinfo.bat` | Prepares the Python environment, selects a free local port, starts Flask, and opens Edge. |
| `flightinfo_app.py` | Flask page and API routes, validation, data mapping, and filtering. |
| `flightinfo_api_client.py` | Key loading, arrivals and OData requests, normalization, and API error handling. |
| `data/city_country.json` | Airport labels and city/country search data. |
| `templates/index.html` | Browser page structure and content. |
| `static/flight_search.js` | Browser search, rendering, sorting, pagination, and connection status. |
| `static/flightinfo_design.css` | Layout, colors, cards, and responsive styling. |
| `tests/test_flightinfo_app.py` | Automated checks for routes, filtering, API behavior, and paging. |
| `README.md` | Setup and run instructions. |
| `PROJECT_SUMMARY.md` | Short project overview. |
| `CODE_EXPLANATION.txt` | Plain-language explanation of the code. |

## 5. Testing

Run the automated checks from the `API projekt` folder:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The suite contains 30 tests. It covers both flight modes for all ten supported airport choices, city and country filtering for all 51 listed countries, OData request handling, API connection success and failure, and 50-flight pagination. These automated tests use sample API responses.

The application was also checked in a local browser against the live API for arrivals, departures, city and country filters, pagination, and API connectivity. Live flight results depend on the selected airport and date, the subscription, and Swedavia API availability.

## 6. Problems and solutions

| Problem | Solution |
|---|---|
| Flask used the wrong import name after the entry point was named `flightinfo_app.py`. | The launch configuration now uses the actual module name. |
| OData departure records could wrap arrival and departure legs separately. | The API client selects the departure leg before the browser displays the flight. |
| The location search was initially limited to departures. | The field now works in both modes and Flask filters arrivals by their origin. |
| A previous local server could remain open on the default port and show an outdated app. | The Windows launcher selects an available local port and opens that address. |
| Some API records omit optional flight details or use codes absent from the local lookup. | The page omits unavailable details and can map a unique returned city name. |

## 7. Conclusion

The project recreates the core airport and flight-search behavior of the reference application. It demonstrates how HTML, CSS, JavaScript, Flask, JSON, and a documented external API work together. Live data requires a valid local key and depends on the external service.

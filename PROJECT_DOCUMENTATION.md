# FlightInfo Explorer — Project Documentation

## 1. Project overview

FlightInfo Explorer is a browser application built with Python, Flask, HTML, CSS, and JavaScript. It was created as a reverse-engineering project based on the supplied Swedavia FlightInfo reference application and video. The goal was to inspect the visible application, infer its inputs and data flow, and build a similar flight-information experience.

This is an independent school project and is not an official Swedavia product.

## 2. Phase 1 — Research and planning

### Reference research

The reference application was reviewed to identify its visible purpose and behavior: choosing an airport and date, switching between arrivals and departures, viewing flights in time order, and searching/filtering destinations. The assignment describes a reverse-engineering process: inspect an existing result, infer likely inputs and processing, sketch the logic, then implement an application with similar output.

The Swedavia FlightInfo API v2 guide was checked before implementing API requests. It documents the arrival and departure operations and the public OData query endpoint. Departures in this project use OData filtering by airport, scheduled date, and flight type. The guide is available at [Swedavia FlightInfo API v2 documentation](https://apideveloper.swedavia.se/content/Using_the_FlightInfo_API.pdf).

Swedavia's [official destination statistics page](https://www.swedavia.se/om-swedavia/statistik/) describes its destination statistics as passenger traffic between Swedavia airports and destinations. The local search list was built from the linked [2025 destination statistics workbook](https://www.swedavia.se/contentassets/95dc75e405f0460fb852949b4b7cb09f/destinations-statistik-2025.xlsx).

### Requirements inferred from the reference and assignment

- Provide a browser interface with ten Swedavia airport choices.
- Let users select arrivals or departures and a date.
- Display readable flight cards in scheduled-time order, 50 per page.
- Let users type a destination or country to filter departures.
- Include OData-based departure requests and a way to check the FlightInfo API connection.
- Explain the research, implementation, tests, problems and solutions, and final result in English.

### Plan and tools

Python and Flask were chosen for the server and API calls. HTML defines the page, CSS styles it, and JavaScript handles browser interactions. JSON stores the destination lookup. The API key stays in a local file outside the project folder.

## 3. Phase 2 — Building the application

### Main parts and request flow

1. The user chooses an airport, flight direction, date, and optionally a destination or country.
2. `static/flight_search.js` sends those selections to the local Flask server.
3. `flightinfo_app.py` validates the inputs and selects the corresponding API client function.
4. `flightinfo_api_client.py` loads the local subscription key and sends a request to the documented FlightInfo API.
5. Swedavia returns JSON data. Flask passes the result to the browser, where JavaScript creates readable flight cards from the fields that are present.

JSON is a structured data format containing named values and nested objects. FlightInfo returns flight data as JSON, and the application reads selected values such as flight number, time, airline, route, and status rather than showing the raw response.

### Destination search and data choices

`data/city_country.json` contains the ten-airport display mapping and the type-ahead destination list. After removing a blank city entry from the source, the destination list has **254 city-and-country pairs in 51 countries**: all destinations listed for European countries in Swedavia's 2025 statistics, plus destinations in selected countries in Africa, Asia, North America, and South America. The 2025 source does not list an Oceania destination with passenger traffic, so none was added. The workbook includes historical traffic data; it does not guarantee that a route operates on every selected travel date.

The search field uses a custom suggestion list. It stays closed when the field is empty, and after typing it shows only names that begin with the entered text (ignoring case and accents). Suggestions include both country names and `City, Country` labels. When filtering, Flask maps a destination IATA code through the local lookup where available. If a code is not in that lookup, it can use the destination city text returned by FlightInfo to match a unique city in the 2025 destination list. Country or city filtering is applied to the departures returned by the API.

### OData and API connection check

The departure client sends the documented OData query with a filter shaped like:

```text
airport eq 'ARN' and scheduled eq 'YYMMDD' and flightType eq 'D'
```

The date format follows the API guide. The request asks for up to 1,000 records; the browser then paginates the returned flights in groups of 50. Destination-country matching is done locally because the OData filter in this application selects airport, date, and flight type.

The page's **Check connection** control calls the local `/api/heartbeat` route. Flask makes a small authenticated public OData request with a result count of one. The control reports whether that request succeeded at that time; it does not use the portal's internal `heartBeat` operation.

### Important files

| File or folder | Purpose |
|---|---|
| `flightinfo_app.py` | Flask page and API routes, input validation, destination enrichment, and filtering. |
| `flightinfo_api_client.py` | Key loading, request construction, OData query, and API error handling. |
| `data/city_country.json` | Airport labels and the Swedavia 2025 destination suggestions used for local filtering. |
| `templates/index.html` | Browser page structure, airport choices, tabs, date, search field, and results area. |
| `static/flight_search.js` | Browser search, sorting, rendering, pagination, and connection status. |
| `static/flightinfo_design.css` | Page colors, layout, cards, hover effects, and responsive styles. |
| `tests/test_flightinfo_app.py` | Automated checks for page content, routes, filtering, API requests, and pagination. |
| `start_flightinfo.bat` | Windows launcher that prepares the environment, starts Flask, and opens the app. |
| `requirements.txt` | Python packages required to run the application. |
| `README.md` | Setup, launch, API-key location, feature, and test instructions. |
| `PROJECT_SUMMARY.md` | Short overview of the project. |
| `CODE_EXPLANATION.txt` | Plain-language explanation of the important code and data flow. |

## 4. Phase 3 — Testing and completion

The automated checks are run from the project folder with:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The latest local run completed **22 tests successfully**.

The tests cover the page, arrivals and departures routes, OData parameters, destination and country filtering, API connection success/failure handling, static assets, and 50-flight pagination. API calls are mocked in automated tests, so these tests do not prove that a live key or every date and airport works against Swedavia.

The browser was manually opened through the Windows launcher. The page and its CSS, JavaScript, and image assets loaded locally. The API portal's Try it request for arrivals returned `HTTP/1.1 200 OK`. A live departures check should be made separately with a valid local key because subscriptions, dates, airports, and service availability can affect results.

The application includes arrival search, OData-based departure search, destination and country type-ahead filtering, readable results, 50-item pagination, and an API connection check. The project source and supporting setup files are stored in the GitHub repository.

## 5. Phase 4 — Problems and solutions

| Problem | Solution |
|---|---|
| Flask tried to import `app` after the entry point was named `flightinfo_app.py`. | The launch configuration was changed to use the actual module name. |
| A launch command failed when run from the parent folder because `.venv` was inside the project folder. | `start_flightinfo.bat` changes to its own folder before using the environment. The README gives the correct command for both folder locations. |
| Raw JSON was difficult to read as a flight board. | JavaScript turns available response fields into readable flight cards. |
| Some API records do not contain every optional detail. | The page displays optional fields only when present and uses the API's returned status text. |
| FlightInfo destination codes do not include a complete city and country lookup. | The local JSON list was expanded from Swedavia's official 2025 destination statistics; returned city text is used when a code is not mapped. |
| The browser could not contact the local application when Flask was not running. | Keep the server window open while using the browser; the launcher starts Flask and opens the page. |

## 6. Conclusion and possible improvements

The project recreates the core flight-search workflow identified in the reference and connects it to the documented FlightInfo API. The work demonstrates how browser code, a Flask server, an API client, JSON data, and an external API work together. The destination suggestions are based on 2025 passenger statistics, so future improvements could refresh the local list and verify city-name matching against new FlightInfo responses. Live behavior also depends on a valid subscription key and the API's current data.

## 7. Run the application on Windows

In VS Code, look at the folder shown at the end of the PowerShell prompt.

If it ends with `...\Swedavia FlightInfo>`, run:

```powershell
& ".\API projekt\start_flightinfo.bat"
```

If it ends with `...\Swedavia FlightInfo\API projekt>`, run:

```powershell
.\start_flightinfo.bat
```

The launcher opens the local app at `http://127.0.0.1:5000/`. Keep the server window open while using the page. Live searches require the user's subscription key saved outside the project, as described in `README.md`.

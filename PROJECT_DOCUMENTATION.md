# FlightInfo Explorer — Project Documentation

## 1. Project overview

FlightInfo Explorer is a browser application built with Python, Flask, HTML, CSS, and JavaScript. It recreates the main workflow observed in the supplied Swedavia FlightInfo reference: choose an airport and date, select arrivals or departures, and read flight results in a list.

This is an independent reverse-engineering school project. It is not an official Swedavia application.

## 2. Research and requirements

The reference application and the supplied video were reviewed to identify the visible inputs, flight list, date selection, direction tabs, destination information, and API connection feature. The assignment describes reverse engineering as inspecting an existing result, inferring its inputs and process, sketching the logic, and building an application with similar output.

The Swedavia FlightInfo API v2 guide was checked before building requests. It documents arrivals and departures operations and a public OData query endpoint. The OData query supports a `filter`, `continuationtoken`, and `count`; its filter can select fields including airport, flight type, scheduled date, and flight ID. The application uses the query endpoint for departures with airport, date, and departure type conditions. The API documentation is available at [Swedavia FlightInfo API guide](https://apideveloper.swedavia.se/content/Using_the_FlightInfo_API.pdf).

The core requirements inferred from the reference were:

- Select one of the ten airport codes shown in the application.
- Select arrivals or departures and a date.
- Present flight information as readable cards, sorted by scheduled time.
- Limit the visible list to 50 flights per page.
- Filter departures by destination country.
- Provide an on-page way to check whether the FlightInfo API responds.

The API key is read from a local text file outside the project. The key is not part of the source code, repository, or project ZIP.

## 3. Design and data decisions

Python and Flask handle server routes and calls to the external API. HTML defines the browser page, CSS handles its appearance, and JavaScript manages selection, search, sorting, pagination, and display. This separates the browser interface from API credentials and server-side request handling.

The Swedavia FlightInfo response provides destination airport identifiers but not a complete country name mapping for the interface. Therefore `data/city_country.json` contains a manually curated lookup from common IATA airport codes to city and country names. This lookup is a starter dataset, not a complete or official Swedavia route list. The country filter only matches destinations present in that file; an unknown destination code cannot be assigned a country by the application.

The documented OData filters used by the project do not supply the destination country mapping. OData is used to select the departure records by airport, scheduled date, and flight type. The country filter is then applied in Flask using the local JSON lookup.

The connection check sends one small authenticated request through the public OData query endpoint, asking for at most one record for ARN departures on the computer's local date. It reports whether the request received a usable API response. This check uses the documented public query operation rather than relying on a separate portal `heartBeat` operation.

## 4. Implementation

### Project files

| File or folder | Responsibility |
|---|---|
| `start_flightinfo.bat` | Creates the local Python environment if necessary, installs dependencies, starts Flask, and opens the browser on Windows. |
| `flightinfo_app.py` | Flask entry point and routes for the page, arrivals, departures, and API connection check. It enriches departures and applies the country filter. |
| `flightinfo_api_client.py` | Validates airport codes and dates, loads the local API key, sends authenticated requests, builds OData queries, and translates API errors. |
| `data/city_country.json` | Curated airport-code, city, and country lookup for common destinations. |
| `templates/index.html` | Page structure, airport choices, direction tabs, date, country filter, results area, and connection controls. |
| `static/flight_search.js` | Sends searches, displays results, formats times, sorts and paginates flights, filters by country, and updates connection status. |
| `static/flightinfo_design.css` | Page colours, layout, cards, hover effects, and responsive design. |
| `tests/test_flightinfo_app.py` | Automated tests for page content, routes, filtering, API request construction, error handling, and pagination. |
| `requirements.txt` | Python dependencies needed to run the project. |
| `README.md` | Setup, launch, key-file, feature, and test instructions. |
| `PROJECT_SUMMARY.md` | Short overview of the application and current scope. |
| `CODE_EXPLANATION.txt` | Plain-language explanation of the important code and data flow. |

### Request and response flow

1. A user selects an airport, direction, date, and optionally a country for departures.
2. JavaScript sends the selected values to Flask at `/api/arrivals` or `/api/departures`.
3. Flask validates the input and calls `flightinfo_api_client.py`.
4. The API client reads a local subscription key and sends the request to Swedavia.
5. Swedavia returns JSON data. Flask returns it to the browser, and JavaScript builds readable flight cards from fields present in the response.

JSON is a structured data format consisting of named values and nested objects. It is used for the API response and for the local destination lookup. The browser uses the relevant JSON fields instead of showing the full raw response.

### OData and country filtering

The departures client builds an OData query using a filter in this form:

```text
airport eq 'ARN' and scheduled eq 'YYMMDD' and flightType eq 'D'
```

The date is formatted as required by the documented query example. The request also asks for up to 1,000 records so that the page can paginate the returned set locally in groups of 50. The country search field offers suggestions populated from country names in `city_country.json`. The user can type a country name and choose a matching suggestion. Flask maps each returned destination IATA code to the local lookup and filters the departure records by the entered country.

### API connection check

The page's **Check connection** button calls `/api/heartbeat` on the local Flask server. Flask then makes one authenticated OData query to the public FlightInfo service. A successful response indicates that this particular request worked at that time. A failure is shown as unavailable. The check depends on internet access, a working local server, and a valid key/subscription; it is not a guarantee that every API operation is available.

## 5. Testing and current evidence

The automated suite was run locally with:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The latest run completed **18 tests successfully**. Tests cover the home page, API routes, invalid input, destination country matching, invalid country selection, the heartbeat route's success and failure handling, the OData URL/filter/count/header, static assets, and 50-flight pagination. External API requests are mocked in these automated tests, so the test run does not prove that a live key or every live airport/date combination works.

Earlier manual checks confirmed that the Flask page and its CSS, JavaScript, and image assets loaded in the browser. A documented arrivals request was also submitted using the API portal's Try it control and returned `HTTP/1.1 200 OK`. The newly added country filter and OData departures implementation are covered by local tests; they should also be demonstrated with the user's live key before being treated as manually verified against the live service.

## 6. Problems encountered and solutions

| Problem | Solution or current handling |
|---|---|
| Flask initially tried to import `app` after the file was named `flightinfo_app.py`. | The launch configuration was changed to use the actual module name. |
| Starting from the parent folder made `.venv` paths fail. | The Windows launcher changes to its own project directory before using the environment. |
| Raw JSON was difficult to read. | JavaScript turns available response fields into readable flight cards. |
| Some flight records omit optional values. | The renderer only displays optional details when the API provides them. The status badge shows the status returned by the API, including “Deleted” when that is the returned status. |
| No documented country field was available for the interface's country search. | A local JSON airport-to-country lookup was added. It is explicitly limited to the airport codes it contains. |
| Windows may not have an IANA timezone database installed for Python's `ZoneInfo`. | The connection check uses the computer's local date, avoiding an extra timezone-data dependency. |
| The browser could not contact the local app when Flask was not running. | The server must remain running while the browser is in use; the Windows launcher starts it and opens the page. |

## 7. Run the application

On Windows, open the project folder in VS Code and run this command from the project root, or double-click the launcher in File Explorer:

```powershell
.\start_flightinfo.bat
```

The app opens at `http://127.0.0.1:5000/`. Keep its server window open while using the page. For live API requests, save the user's own subscription key outside the project as described in `README.md`.

## 8. Conclusion and remaining limits

The application now includes arrival searches, OData-based departure searches, country filtering through a local JSON lookup, readable and paginated results, and an API connection check. It demonstrates how the browser interface, Flask server, API client, JSON data, and external service fit together.

The country lookup is not exhaustive, and a destination not listed in the file cannot be matched to a country. Automated tests use mocked API responses. Live API behaviour can vary by subscription, date, airport, API availability, and returned data, so those cases require a separate live check.

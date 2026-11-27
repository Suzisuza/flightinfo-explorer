# FlightInfo Explorer

FlightInfo Explorer is a browser-based reverse-engineering project built with Python, Flask, HTML, CSS, and JavaScript. It uses the Swedavia FlightInfo API v2 to display arrivals and departures as readable flight cards.

## Run on Windows

The recommended way to start the application is `start_flightinfo.bat` in the `API projekt` folder. In VS Code, look at the folder at the end of the PowerShell prompt.

If the terminal is in the parent `Swedavia FlightInfo` folder, run:

```powershell
& ".\API projekt\start_flightinfo.bat"
```

If the terminal is already in the `API projekt` folder, run:

```powershell
.\start_flightinfo.bat
```

The launcher creates `.venv` if needed, installs the packages in `requirements.txt`, chooses an available local port starting at 5000, starts Flask in a separate window, and opens the application in Microsoft Edge. Keep the server window open. Stop it with `Ctrl+C` in that window.

### Manual setup

Run these commands from the `API projekt` folder:

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m flask --app flightinfo_app run --port 5055
```

Then open `http://127.0.0.1:5055/` in a browser. If that port is occupied, choose another unused port and use the same port in the address.

## Features

- Select one of ten airports, a date, and Arrivals or Departures.
- Leave the location field empty to view all flights returned for the selection.
- Filter arrivals by origin city or country and departures by destination city or country.
- Browse scheduled-time results in pages of up to 50 flights.
- Check the live FlightInfo API connection.

Arrivals use the documented FlightInfo v2 arrivals operation. Departures use the documented OData query operation. The API client normalizes wrapped departure records before the page displays them. The search suggestions come from Swedavia's [2025 destination statistics](https://www.swedavia.se/contentassets/95dc75e405f0460fb852949b4b7cb09f/destinations-statistik-2025.xlsx).

## API key

Save your subscription key outside the project folder, preferably at:

`%LOCALAPPDATA%\FlightInfoSecrets\swedavia_api_key_primary.txt`

The application also recognizes `swedavia_primary_key.txt`, `swedavia_secondary_key.txt`, and `swedavia_api_key.txt` in that folder. Do not add a key to the project, GitHub, or the submission ZIP. A teacher who wants live results must use their own key.

## Important files

| File | Purpose |
|---|---|
| `start_flightinfo.bat` | Prepares and launches the application on Windows |
| `flightinfo_app.py` | Flask routes, input checks, data mapping, and filters |
| `flightinfo_api_client.py` | API requests, OData query, key loading, and error handling |
| `data/city_country.json` | Airport labels and city/country suggestions |
| `templates/index.html` | Browser page structure |
| `static/flight_search.js` | Search, flight cards, sorting, paging, and connection status |
| `static/flightinfo_design.css` | Page layout and visual styling |
| `PROJECT_DOCUMENTATION.md` | Written record of the research, design choices, and implementation |
| `PROJECT_SUMMARY.md` | Short project overview |
| `CODE_EXPLANATION.txt` | Plain-language explanation of important code |

## Run the tests

From the `API projekt` folder, run:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The tests cover both flight modes, all ten supported airport choices, all 51 countries in the filter list, OData handling, the API connection route, and pagination. Automated tests use sample responses; live results depend on the API, date, and subscription.

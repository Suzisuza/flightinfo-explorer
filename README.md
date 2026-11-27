# FlightInfo Explorer

A browser-based learning project inspired by the Swedavia FlightInfo API v2 reference application.

## Run on Windows

The easiest way to start the application is to double-click `start_flightinfo.bat` in the project folder. In VS Code, you can also run it from a PowerShell terminal opened in the project root:

```powershell
.\start_flightinfo.bat
```

The launcher creates the local `.venv` environment if needed, installs the packages from `requirements.txt`, starts the Flask server in a separate command window, and opens the app in Microsoft Edge at `http://127.0.0.1:5000/`. Keep the server window open while using the app. Stop the server with `Ctrl+C` in that window.

On the learner's original desktop layout, the project folder is nested inside `Swedavia FlightInfo\API projekt`. If a PowerShell terminal is still in the parent `Swedavia FlightInfo` folder, run:

```powershell
& ".\API projekt\start_flightinfo.bat"
```

For manual setup from the project root:

1. Create a virtual environment: `py -m venv .venv`
2. Install dependencies: `.venv\Scripts\python.exe -m pip install -r requirements.txt`
3. Start Flask: `.venv\Scripts\python.exe -m flask --app flightinfo_app run`
4. Open `http://127.0.0.1:5000/` in a browser.

The first run of the launcher needs an internet connection to install Flask. If Python is not installed, install Python 3 first. If port 5000 is already in use, stop the other Flask server before starting this one.

## Project files

| File | Purpose |
|---|---|
| `start_flightinfo.bat` | Windows launcher: prepares dependencies, starts Flask, and opens the browser |
| `flightinfo_app.py` | Main Flask application and browser routes |
| `flightinfo_api_client.py` | Sends authenticated FlightInfo requests from Python |
| `data/city_country.json` | Local IATA airport-to-city-and-country lookup for departure labels and country filtering |
| `templates/index.html` | Structure and text of the browser page |
| `static/flight_search.js` | Airport and tab selection, search, country filter, readable flight list, and API connection check |
| `static/flightinfo_design.css` | Colors, layout, hover effects, and responsive design |
| `tests/test_flightinfo_app.py` | Automated checks for the app and API client |
| `requirements.txt` | Python packages needed by the project |

Arrivals use the documented FlightInfo v2 arrivals operation. Departures use the documented OData query operation, filtering by airport, scheduled date, and departure type. The browser sends the selected airport, date, and optional destination country to Flask; Python adds the subscription key and contacts the Swedavia API.

The destination country filter uses `data/city_country.json` to map returned destination IATA codes to city and country names. This is a curated starter lookup, not a complete or official Swedavia route list. Destinations missing from the file cannot be identified or included in a country filter.

The **Check connection** control makes one small authenticated public OData request and reports whether the API responds. It is a live connectivity check and therefore requires a valid key and internet access. It does not call the portal's separate `heartBeat` operation, which is documented as internal use only.

## Local API key

Save one key in a text file outside this project, preferably at:

`%LOCALAPPDATA%\FlightInfoSecrets\swedavia_primary_key.txt`

The app also recognizes `swedavia_secondary_key.txt` and `swedavia_api_key.txt` in that same folder. It reads only the first available file in that order. Never paste a key into source code, the browser JavaScript, GitHub, or a project ZIP.

The homepage can run without a key. Live arrival and departure searches require a valid local key file; a teacher receiving the project should use their own key if they need to make live API requests. The project ZIP and Git repository must not contain the learner's private key.

Choose **Arrivals** or **Departures** with the tabs above the airport/date search. Both searches support the ten Swedavia airport choices shown in the page: ARN, GOT, BMA, MMX, LLA, UME, KRN, RNB, VBY and OSD. Dates are sent in `YYYY-MM-DD` format. Departures can optionally be filtered by destination country using the local JSON lookup. Results are shown as a readable list ordered by scheduled time, with up to 50 flights on each page. The page displays the API's status text as returned and omits optional details that are missing.

Run the automated checks with:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

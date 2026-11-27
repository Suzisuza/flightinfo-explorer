# FlightInfo Explorer

A browser-based learning project inspired by the Swedavia FlightInfo API v2 reference application.

## Run on Windows

The Windows launcher is `start_flightinfo.bat`, located inside the `API projekt` folder. In VS Code, first check the folder shown at the end of the PowerShell prompt, then use the matching command below.

### If the terminal is in the parent `Swedavia FlightInfo` folder

For example, if the prompt ends with:

```text
PS C:\Users\hp\OneDrive\Skrivbord\Swedavia FlightInfo>
```

Run this exact command:

```powershell
& ".\API projekt\start_flightinfo.bat"
```

### If the terminal is already in the `API projekt` folder

For example, if the prompt ends with:

```text
PS C:\Users\hp\OneDrive\Skrivbord\Swedavia FlightInfo\API projekt>
```

Run:

```powershell
.\start_flightinfo.bat
```

You can also double-click `start_flightinfo.bat` in File Explorer. The launcher creates the project's local `.venv` environment if needed, installs packages from `requirements.txt`, starts Flask in a separate command window, and opens the app in Microsoft Edge at `http://127.0.0.1:5000/`. Keep the server window open while using the app. Stop the server with `Ctrl+C` in that window.

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
| `data/city_country.json` | Local airport labels and destination suggestions used for city and country filtering |
| `templates/index.html` | Structure and text of the browser page |
| `static/flight_search.js` | Airport and tab selection, search, destination filter, readable flight list, and API connection check |
| `static/flightinfo_design.css` | Colors, layout, hover effects, and responsive design |
| `tests/test_flightinfo_app.py` | Automated checks for the app and API client |
| `requirements.txt` | Python packages needed by the project |

Arrivals use the documented FlightInfo v2 arrivals operation. Departures use the documented OData query operation, filtering by airport, scheduled date, and departure type. The browser sends the selected airport, date, and optional destination country to Flask; Python adds the subscription key and contacts the Swedavia API.

For departures, type a destination city or country name and choose a matching suggestion. The list in `data/city_country.json` is based on Swedavia's official [2025 destination statistics](https://www.swedavia.se/contentassets/95dc75e405f0460fb852949b4b7cb09f/destinations-statistik-2025.xlsx). It contains 255 city-country pairs in 51 countries: all European destinations listed in that source, plus selected countries in Africa, Asia, North America, and South America. The source lists no Oceania destination with passenger traffic during 2025. These are historical traffic statistics and do not guarantee that a route operates on every selected travel date. When an IATA code is not in the local lookup, the app can match a unique city name returned by FlightInfo.

The **Check connection** control makes one small authenticated public OData request and reports whether the API responds. It is a live connectivity check and therefore requires a valid key and internet access. It does not call the portal's separate `heartBeat` operation, which is documented as internal use only.

## Local API key

Save one key in a text file outside this project, preferably at:

`%LOCALAPPDATA%\FlightInfoSecrets\swedavia_primary_key.txt`

The app also recognizes `swedavia_secondary_key.txt` and `swedavia_api_key.txt` in that same folder. It reads only the first available file in that order. Never paste a key into source code, the browser JavaScript, GitHub, or a project ZIP.

The homepage can run without a key. Live arrival and departure searches require a valid local key file; a teacher receiving the project should use their own key if they need to make live API requests. The project ZIP and Git repository must not contain the learner's private key.

Choose **Arrivals** or **Departures** with the tabs above the airport/date search. Both searches support the ten Swedavia airport choices shown in the page: ARN, GOT, BMA, MMX, LLA, UME, KRN, RNB, VBY and OSD. Dates are sent in `YYYY-MM-DD` format. Departures can optionally be filtered by destination city or country using the local JSON lookup. Results are shown as a readable list ordered by scheduled time, with up to 50 flights on each page. The page displays the API's status text as returned and omits optional details that are missing.

Run the automated checks with:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

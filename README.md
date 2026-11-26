# FlightInfo Explorer

A browser-based learning project inspired by the Swedavia FlightInfo API v2 reference application.

## Run locally

Open the `API projekt` folder itself in VS Code. Run the following commands in its integrated PowerShell terminal. If the terminal starts in the parent `Swedavia FlightInfo` folder, you can enter the project folder and start Flask in one command:

`cd ".\API projekt"; .\.venv\Scripts\python.exe -m flask --app flightinfo_app run --debug`

If the terminal is already in `API projekt`, run only the Flask start command from step 3.

1. Create a virtual environment: `py -m venv .venv`
2. Install dependencies: `.venv\Scripts\python.exe -m pip install -r requirements.txt`
3. Start Flask: `.venv\Scripts\python.exe -m flask --app flightinfo_app run --debug`
4. Open `http://127.0.0.1:5000/` in a browser.

Stop the local server with `Ctrl+C` in the terminal.

If Flask displays `Could not import 'app'`, stop the old server with `Ctrl+C` and start it again using the updated `--app flightinfo_app` command above. The main Python file is now named `flightinfo_app.py`.

## Project files

| File | Purpose |
|---|---|
| `flightinfo_app.py` | Main Flask application and browser routes |
| `flightinfo_api_client.py` | Sends authenticated FlightInfo requests from Python |
| `templates/index.html` | Structure and text of the browser page |
| `static/flight_search.js` | Airport and tab selection, API search, and readable flight list |
| `static/flightinfo_design.css` | Colors, layout, hover effects, and responsive design |
| `tests/test_flightinfo_app.py` | Automated checks for the app and API client |
| `requirements.txt` | Python packages needed by the project |

The Arrivals and Departures searches use the corresponding documented FlightInfo v2 operations through the Flask server. The browser sends the selected airport and date to Flask; Python adds the subscription key and contacts the Swedavia API.

## Local API key

Save one key in a text file outside this project, preferably at:

`%LOCALAPPDATA%\FlightInfoSecrets\swedavia_primary_key.txt`

The app also recognizes `swedavia_secondary_key.txt` and `swedavia_api_key.txt` in that same folder. It reads only the first available file in that order. Never paste a key into source code, the browser JavaScript, GitHub, or a project ZIP.

The home page can run without a key. Live arrival and departure searches require a valid local key file; a teacher receiving the project should use their own key if they need to make live API requests. The project ZIP and Git repository must not contain the learner's private key.

Choose **Arrivals** or **Departures** with the tabs above the airport/date search. Both searches support the ten Swedavia airport choices shown in the page: ARN, GOT, BMA, MMX, LLA, UME, KRN, RNB, VBY and OSD. Dates are sent in `YYYY-MM-DD` format. Results are shown as a readable list ordered by scheduled time, with up to 50 flights on each page. The page displays the API's status text as returned and omits optional details that are missing.

Run the automated checks with:

`.venv\Scripts\python.exe -m unittest discover -s tests -v`

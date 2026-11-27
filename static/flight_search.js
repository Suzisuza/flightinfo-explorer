"use strict";

const airportButtons = document.querySelectorAll(".airport-chip");
const modeTabs = document.querySelectorAll(".flight-mode-tab");
const modeLinks = document.querySelectorAll(".feature-link[data-flight-mode]");
const flightForm = document.querySelector("#arrival-search");
const dateInput = document.querySelector("#flight-date");
const flightSearchPanel = document.querySelector("#flight-search-panel");
const resultsPanel = document.querySelector("#arrival-results");
const resultsTitle = document.querySelector("#results-title");
const resultMessage = document.querySelector("#arrival-message");
const flightList = document.querySelector("#arrival-list");
const searchButton = flightForm.querySelector("button[type='submit']");
const paginationControls = document.querySelector("#flight-pagination");
const previousPageButton = document.querySelector("#previous-page");
const nextPageButton = document.querySelector("#next-page");
const paginationInfo = document.querySelector("#pagination-info");
const destinationFilterPanel = document.querySelector("#country-filter");
const destinationSearchInput = document.querySelector("#destination-country");
const destinationSuggestionList = document.querySelector("#destination-options");
const destinationOptions = JSON.parse(
  document.querySelector("#destination-options-data").textContent,
);
const apiStatusText = document.querySelector("#api-status-text");
const checkApiButton = document.querySelector("#check-api-button");

let selectedAirport = "ARN";
let selectedMode = "arrivals";
let sortedFlights = [];
let currentPage = 0;
const flightsPerPage = 50;
let activeSuggestionIndex = -1;

const airportNames = {
  ARN: "Stockholm Arlanda",
  GOT: "Gothenburg Landvetter",
  BMA: "Stockholm Bromma",
  MMX: "Malmö",
  LLA: "Luleå",
  UME: "Umeå",
  KRN: "Kiruna",
  RNB: "Ronneby",
  VBY: "Visby",
  OSD: "Åre Östersund",
};

dateInput.value = new Date().toISOString().slice(0, 10);

function readField(object, ...names) {
  if (!object || typeof object !== "object") return "";
  for (const name of names) {
    const value = object[name];
    if (value !== undefined && value !== null && value !== "") return value;
  }
  return "";
}

function normalizeSuggestion(value) {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase();
}

function closeDestinationSuggestions() {
  destinationSuggestionList.hidden = true;
  destinationSearchInput.setAttribute("aria-expanded", "false");
  destinationSearchInput.removeAttribute("aria-activedescendant");
  activeSuggestionIndex = -1;
}

function setActiveDestinationSuggestion(index) {
  const suggestions = destinationSuggestionList.querySelectorAll('[role="option"]');
  if (!suggestions.length) return;

  activeSuggestionIndex = (index + suggestions.length) % suggestions.length;
  suggestions.forEach((suggestion, suggestionIndex) => {
    const isActive = suggestionIndex === activeSuggestionIndex;
    suggestion.setAttribute("aria-selected", String(isActive));
    if (isActive) {
      destinationSearchInput.setAttribute("aria-activedescendant", suggestion.id);
      suggestion.scrollIntoView({ block: "nearest" });
    }
  });
}

function chooseDestinationSuggestion(value) {
  destinationSearchInput.value = value;
  closeDestinationSuggestions();
  destinationSearchInput.focus();
}

function renderDestinationSuggestions() {
  const searchText = normalizeSuggestion(destinationSearchInput.value.trim());
  destinationSuggestionList.replaceChildren();
  closeDestinationSuggestions();
  if (!searchText) return;

  const matchingOptions = destinationOptions.filter((option) =>
    normalizeSuggestion(option).startsWith(searchText),
  );
  if (!matchingOptions.length) return;

  matchingOptions.forEach((option, index) => {
    const item = document.createElement("li");
    item.id = `destination-suggestion-${index}`;
    item.setAttribute("role", "option");
    item.setAttribute("aria-selected", "false");
    item.textContent = option;
    item.addEventListener("mousedown", (event) => event.preventDefault());
    item.addEventListener("click", () => chooseDestinationSuggestion(option));
    destinationSuggestionList.append(item);
  });

  destinationSuggestionList.hidden = false;
  destinationSearchInput.setAttribute("aria-expanded", "true");
}

function getTimeValues(flight) {
  const timeGroup = selectedMode === "arrivals"
    ? readField(flight, "arrivalTime", "ArrivalTime")
    : readField(flight, "departureTime", "DepartureTime");

  return {
    scheduled: readField(timeGroup, "scheduledUtc", "ScheduledUtc"),
    estimated: readField(timeGroup, "estimatedUtc", "EstimatedUtc"),
    actual: readField(timeGroup, "actualUtc", "ActualUtc"),
  };
}

function scheduledTimestamp(flight) {
  const times = getTimeValues(flight);
  const timestamp = Date.parse(times.scheduled || times.estimated || times.actual);
  return Number.isNaN(timestamp) ? Number.MAX_SAFE_INTEGER : timestamp;
}

function formatTime(value) {
  if (!value) return "";
  const parsedTime = new Date(value);
  if (Number.isNaN(parsedTime.getTime())) return "";

  return new Intl.DateTimeFormat("en-GB", {
    timeZone: "Europe/Stockholm",
    hour: "2-digit",
    minute: "2-digit",
  }).format(parsedTime);
}

function addDetail(container, label, value) {
  if (!value) return;
  const detail = document.createElement("p");
  const name = document.createElement("strong");
  name.textContent = `${label}: `;
  detail.append(name, document.createTextNode(value));
  container.append(detail);
}

function createStatusBadge(statusText) {
  const badge = document.createElement("span");
  badge.className = "flight-status";
  badge.textContent = statusText;
  return badge;
}

function selectFlightMode(mode) {
  selectedMode = mode;
  destinationFilterPanel.hidden = mode !== "departures";
  const label = mode === "arrivals" ? "Arrivals" : "Departures";
  resultsTitle.textContent = `${label} results`;
  searchButton.textContent = `Show ${label.toLowerCase()}`;
  flightSearchPanel.setAttribute("aria-labelledby", `${mode}-tab`);
  resultsPanel.hidden = true;
  resultMessage.textContent = "";
  flightList.replaceChildren();
  paginationControls.hidden = true;
  sortedFlights = [];
  currentPage = 0;

  modeTabs.forEach((tab) => {
    const isSelected = tab.dataset.flightMode === mode;
    tab.setAttribute("aria-selected", String(isSelected));
    tab.tabIndex = isSelected ? 0 : -1;
  });
}

function renderFlights(data) {
  flightList.replaceChildren();
  const flights = readField(data, "flights", "Flights");
  const action = selectedMode === "arrivals" ? "arrivals" : "departures";
  const airportPhrase = selectedMode === "arrivals" ? "at" : "from";

  if (!Array.isArray(flights) || flights.length === 0) {
    sortedFlights = [];
    paginationControls.hidden = true;
    resultMessage.textContent = `No ${action} were listed ${airportPhrase} ${airportNames[selectedAirport] || selectedAirport} on ${dateInput.value}.`;
    return;
  }

  sortedFlights = [...flights].sort(
    (first, second) => scheduledTimestamp(first) - scheduledTimestamp(second),
  );
  currentPage = 0;
  const destinationDescription = selectedMode === "departures" && destinationSearchInput.value
    ? ` to ${destinationSearchInput.value}`
    : "";
  resultMessage.textContent = `${sortedFlights.length} ${action} ${airportPhrase} ${airportNames[selectedAirport] || selectedAirport}${destinationDescription} on ${dateInput.value}. Sorted from earliest to latest by scheduled time. Times are shown in Stockholm local time.`;
  renderFlightPage();
}

function renderFlightPage() {
  flightList.replaceChildren();
  const pageCount = Math.ceil(sortedFlights.length / flightsPerPage);
  const firstIndex = currentPage * flightsPerPage;
  const lastIndex = Math.min(firstIndex + flightsPerPage, sortedFlights.length);
  const pageFlights = sortedFlights.slice(firstIndex, lastIndex);

  paginationControls.hidden = pageCount <= 1;
  previousPageButton.disabled = currentPage === 0;
  nextPageButton.disabled = currentPage >= pageCount - 1;
  paginationInfo.textContent = `Showing ${firstIndex + 1}–${lastIndex} of ${sortedFlights.length} flights · Page ${currentPage + 1} of ${pageCount}`;

  pageFlights.forEach((flight) => {
    const row = document.createElement("article");
    row.className = "flight-row";

    const times = getTimeValues(flight);
    const displayTime = times.actual || times.estimated || times.scheduled;
    const timeLabel = times.actual
      ? (selectedMode === "arrivals" ? "Arrived" : "Departed")
      : times.estimated
        ? "Estimated"
        : "Scheduled";

    const timeColumn = document.createElement("div");
    timeColumn.className = "arrival-time-column";
    const timeCaption = document.createElement("span");
    timeCaption.className = "arrival-time-label";
    timeCaption.textContent = displayTime ? timeLabel : "Time";
    const timeValue = document.createElement("strong");
    timeValue.className = "arrival-time-value";
    timeValue.textContent = formatTime(displayTime) || "—";
    timeColumn.append(timeCaption, timeValue);
    row.append(timeColumn);

    const main = document.createElement("div");
    main.className = "flight-main";
    const heading = document.createElement("div");
    heading.className = "flight-card-heading";

    const flightHeading = document.createElement("h4");
    const flightId = readField(flight, "flightId", "FlightId");
    const airline = readField(flight, "airlineOperator", "AirlineOperator");
    const airlineName = readField(airline, "name", "Name");
    flightHeading.textContent = [flightId, airlineName].filter(Boolean).join(" · ") || "Flight details unavailable";
    heading.append(flightHeading);

    const location = readField(flight, "locationAndStatus", "LocationAndStatus");
    const statusText = readField(
      location,
      "flightLegStatusEnglish",
      "FlightLegStatusEnglish",
      "flightLegStatus",
      "FlightLegStatus",
    );
    if (statusText) heading.append(createStatusBadge(statusText));
    main.append(heading);

    const destinationField = selectedMode === "arrivals"
      ? ["departureAirportEnglish", "DepartureAirportEnglish", "departureAirportSwedish", "DepartureAirportSwedish", "departureAirportIata", "DepartureAirportIata"]
      : ["arrivalAirportEnglish", "ArrivalAirportEnglish", "arrivalAirportSwedish", "ArrivalAirportSwedish", "arrivalAirportIata", "ArrivalAirportIata"];
    const otherAirport = readField(flight, ...destinationField);
    const destinationCity = selectedMode === "departures"
      ? readField(flight, "destinationCity", "DestinationCity")
      : "";
    const destinationCountry = selectedMode === "departures"
      ? readField(flight, "destinationCountry", "DestinationCountry")
      : "";
    const route = document.createElement("p");
    route.className = "flight-route";
    const destinationText = [destinationCity, destinationCountry].filter(Boolean).join(", ");
    route.textContent = otherAirport || destinationText
      ? `${selectedMode === "arrivals" ? "From" : "To"} ${destinationText || otherAirport}`
      : "Route information unavailable";
    main.append(route);

    const details = document.createElement("div");
    details.className = "flight-details";
    if (times.estimated && !times.actual) addDetail(details, "Scheduled", formatTime(times.scheduled));
    if (times.actual) addDetail(details, "Scheduled", formatTime(times.scheduled));
    if (times.actual) addDetail(details, "Estimated", formatTime(times.estimated));
    addDetail(details, "Terminal", readField(location, "terminal", "Terminal"));
    addDetail(details, "Gate", readField(location, "gate", "Gate"));

    if (selectedMode === "arrivals") {
      const baggage = readField(flight, "baggage", "Baggage");
      addDetail(details, "Baggage belt", readField(baggage, "baggageClaimUnit", "BaggageClaimUnit"));
    } else {
      addDetail(details, "Check-in", readField(location, "checkInStatusEnglish", "CheckInStatusEnglish"));
      const deskFrom = readField(location, "checkInDeskFrom", "CheckInDeskFrom");
      const deskTo = readField(location, "checkInDeskTo", "CheckInDeskTo");
      const deskRange = deskFrom && deskTo ? `${deskFrom}–${deskTo}` : deskFrom || deskTo;
      addDetail(details, "Check-in desks", deskRange);
      addDetail(details, "Boarding", readField(location, "gateActionEnglish", "GateActionEnglish"));
    }

    if (details.childElementCount) main.append(details);
    row.append(main);
    flightList.append(row);
  });
}

airportButtons.forEach((button) => {
  button.addEventListener("click", () => {
    selectedAirport = button.dataset.airport;

    airportButtons.forEach((airportButton) => {
      const isSelected = airportButton === button;
      airportButton.classList.toggle("airport-chip-selected", isSelected);
      airportButton.setAttribute("aria-pressed", String(isSelected));
    });
  });
});

modeTabs.forEach((tab) => {
  tab.addEventListener("click", () => selectFlightMode(tab.dataset.flightMode));
});

modeLinks.forEach((link) => {
  link.addEventListener("click", () => selectFlightMode(link.dataset.flightMode));
});

previousPageButton.addEventListener("click", () => {
  if (currentPage > 0) {
    currentPage -= 1;
    renderFlightPage();
  }
});

nextPageButton.addEventListener("click", () => {
  if (currentPage < Math.ceil(sortedFlights.length / flightsPerPage) - 1) {
    currentPage += 1;
    renderFlightPage();
  }
});

destinationSearchInput.addEventListener("input", renderDestinationSuggestions);
destinationSearchInput.addEventListener("keydown", (event) => {
  const suggestionsAreOpen = !destinationSuggestionList.hidden;
  const lastIndex = destinationSuggestionList.querySelectorAll('[role="option"]').length - 1;

  if (event.key === "ArrowDown" && destinationSearchInput.value.trim()) {
    event.preventDefault();
    if (!suggestionsAreOpen) renderDestinationSuggestions();
    setActiveDestinationSuggestion(activeSuggestionIndex + 1);
  } else if (event.key === "ArrowUp" && suggestionsAreOpen) {
    event.preventDefault();
    setActiveDestinationSuggestion(activeSuggestionIndex < 0 ? lastIndex : activeSuggestionIndex - 1);
  } else if (event.key === "Enter" && suggestionsAreOpen && activeSuggestionIndex >= 0) {
    event.preventDefault();
    const suggestion = destinationSuggestionList.querySelectorAll('[role="option"]')[activeSuggestionIndex];
    chooseDestinationSuggestion(suggestion.textContent);
  } else if (event.key === "Escape") {
    closeDestinationSuggestions();
  }
});

document.addEventListener("click", (event) => {
  if (!destinationSearchInput.parentElement.contains(event.target)) {
    closeDestinationSuggestions();
  }
});

flightForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  closeDestinationSuggestions();
  resultsPanel.hidden = false;
  resultsTitle.textContent = `${selectedMode === "arrivals" ? "Arrivals" : "Departures"} results`;
  resultMessage.textContent = `Loading ${selectedMode}...`;
  flightList.replaceChildren();
  paginationControls.hidden = true;
  sortedFlights = [];
  currentPage = 0;
  searchButton.disabled = true;

  const parameters = new URLSearchParams({
    airport: selectedAirport,
    date: dateInput.value,
  });
  if (selectedMode === "departures" && destinationSearchInput.value) {
    parameters.set("destination", destinationSearchInput.value);
  }

  try {
    const response = await fetch(`/api/${selectedMode}?${parameters.toString()}`);
    const data = await response.json();

    if (!response.ok) {
      resultMessage.textContent = `Request failed (HTTP ${response.status}).`;
      const errorMessage = document.createElement("p");
      errorMessage.className = "flight-error";
      errorMessage.textContent = data.error || "The request could not be completed.";
      flightList.append(errorMessage);
      paginationControls.hidden = true;
      return;
    }

    renderFlights(data);
  } catch (error) {
    resultMessage.textContent = "The app could not contact its local server.";
    const errorMessage = document.createElement("p");
    errorMessage.className = "flight-error";
    errorMessage.textContent = "Check that the Flask app is running, then try again.";
    flightList.append(errorMessage);
  } finally {
    searchButton.disabled = false;
  }
});

checkApiButton.addEventListener("click", async () => {
  checkApiButton.disabled = true;
  apiStatusText.textContent = "Checking the FlightInfo API...";
  apiStatusText.className = "api-status-pending";

  try {
    const response = await fetch("/api/heartbeat");
    const data = await response.json();
    if (!response.ok || data.status !== "connected") {
      throw new Error(data.message || "The API connection could not be confirmed.");
    }
    apiStatusText.textContent = "Connected. The FlightInfo API responded successfully.";
    apiStatusText.className = "api-status-connected";
  } catch (error) {
    apiStatusText.textContent = error.message || "Could not check the API connection.";
    apiStatusText.className = "api-status-unavailable";
  } finally {
    checkApiButton.disabled = false;
  }
});

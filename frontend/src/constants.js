/**
 * Application constants for LineupBoss
 */

// Position constants
export const POSITIONS = ["Pitcher", "Catcher", "1B", "2B", "3B", "SS", "LF", "RF", "LC", "RC", "Bench"];
export const INFIELD = ["Pitcher", "1B", "2B", "3B", "SS"];
export const OUTFIELD = ["Catcher", "LF", "RF", "LC", "RC"];
export const BENCH = ["Bench"];

// Other constants
export const MAX_INNINGS = 9;
export const DEFAULT_INNINGS = 6;

// UI constants
export const POSITION_COLORS = {
  "Pitcher": "#FFD700",   // Gold
  "Catcher": "#FF8C00",   // Dark Orange
  "1B": "#32CD32",        // Lime Green
  "2B": "#00BFFF",        // Deep Sky Blue
  "3B": "#FF69B4",        // Hot Pink
  "SS": "#9370DB",        // Medium Purple
  "LF": "#00CED1",        // Dark Turquoise
  "RF": "#FF6347",        // Tomato
  "LC": "#20B2AA",        // Light Sea Green
  "RC": "#BA55D3",        // Medium Orchid
  "Bench": "#A9A9A9"      // Dark Gray
};

// Routes
export const ROUTES = {
  HOME: "/",
  LOGIN: "/login",
  REGISTER: "/register",
  DASHBOARD: "/",
  TEAM_DETAIL: "/teams/:teamId",
  GAME_DETAIL: "/games/:gameId",
};

// API error messages
export const API_ERRORS = {
  UNAUTHORIZED: "You must be logged in to access this resource",
  SERVER_ERROR: "An unexpected error occurred. Please try again later.",
  NOT_FOUND: "The requested resource was not found",
  VALIDATION: "Please check your input and try again",
  NETWORK: "Unable to connect to the server. Please check your internet connection."
};
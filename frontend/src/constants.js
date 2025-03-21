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

// UI constants with new brand colors
export const POSITION_COLORS = {
  "Pitcher": "#F2C94C",   // Golden Yellow (accent)
  "Catcher": "#BA1F33",   // Cardinal Red (primary)
  "1B": "#0A2463",        // Navy Blue (primary)
  "2B": "#0A2463",        // Navy Blue (primary)
  "3B": "#0A2463",        // Navy Blue (primary)
  "SS": "#0A2463",        // Navy Blue (primary)
  "LF": "#1B512D",        // Forest Green (secondary)
  "RF": "#1B512D",        // Forest Green (secondary)
  "LC": "#1B512D",        // Forest Green (secondary)
  "RC": "#1B512D",        // Forest Green (secondary)
  "Bench": "#D6C7A9"      // Sand/Tan (secondary)
};

// Brand colors reference
export const BRAND_COLORS = {
  // Primary Colors
  primaryNavy: "#0A2463",    // Navy Blue - trust and reliability
  primaryRed: "#BA1F33",     // Cardinal Red - energy and excitement
  primaryWhite: "#FFFFFF",   // Clean White - backgrounds and contrast
  
  // Secondary Colors
  secondarySand: "#D6C7A9",  // Sand/Tan - baseball infield dirt, subtle backgrounds
  secondaryGreen: "#1B512D", // Forest Green - baseball field grass, success states
  
  // Accent Colors
  accentYellow: "#F2C94C",   // Golden Yellow - highlighting important elements, calls to action
  accentGray: "#E5E5E5",     // Light Gray - subtle UI elements and dividers
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
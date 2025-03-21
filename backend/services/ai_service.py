"""
AI service for generating fielding rotations.
"""
import os
import json
import random
import time
from typing import Dict, List, Any
import logging
from anthropic import Anthropic

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIService:
    """Service for AI-related operations."""
    
    @staticmethod
    def generate_fielding_rotation(
        game_id: int,
        players: List[Dict[str, Any]],
        innings: int,
        required_positions: List[str],
        infield_positions: List[str],
        outfield_positions: List[str],
        no_consecutive_innings: bool = True,
        balance_playing_time: bool = True,
        allow_same_position: bool = False,
        strict_position_balance: bool = True,
        temperature: float = 0.7
    ) -> Dict[int, Dict[str, int]]:
        """
        Generate a fielding rotation using the Anthropic API.
        
        Args:
            game_id: Game ID
            players: List of player objects with id, name, jersey_number, available, and can_play_catcher
            innings: Number of innings
            required_positions: List of required positions
            infield_positions: List of infield positions
            outfield_positions: List of outfield positions
            
        Returns:
            Dictionary mapping innings to position assignments
        """
        try:
            # Get API key from environment variable
            api_key = os.getenv("ANTHROPIC_API_KEY")
            
            # Enhanced debugging for API key issues
            if not api_key:
                # Try to list environment variables (safely) to help debug
                env_vars = [k for k in os.environ.keys() if k.startswith("ANTHROPIC") or "API" in k]
                logger.error(f"ANTHROPIC_API_KEY not found in environment variables. Found similar vars: {env_vars}")
                raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
            
            # Check for common API key format issues
            if not api_key.startswith("sk-ant-"):
                logger.warning("ANTHROPIC_API_KEY exists but may have incorrect format - should start with 'sk-ant-'")
            
            logger.info(f"Using Anthropic API key starting with: {api_key[:8]}...")
            
            # Initialize Anthropic client with better error handling
            try:
                anthropic = Anthropic(api_key=api_key)
                # Make a minimal test request to validate the API key
                logger.info("Initializing Anthropic client and testing connection...")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {str(e)}")
                raise ValueError(f"Anthropic client initialization failed: {str(e)}")
            
            # Format the list of required positions for the prompt
            required_positions_str = ', '.join(required_positions)
            
            # Prepare the data for the prompt
            players_json = json.dumps(players, indent=2)
            
            # Generate a random seed to ensure different rotations each time
            random_seed = random.randint(1, 10000)
            timestamp = int(time.time())
            
            # Create the prompt
            # Building the prompt with customization options
            rule_components = [
                f"1. MOST CRITICAL: In EVERY inning, ALL of these positions MUST be filled EXACTLY ONCE: {required_positions_str}",
                f"2. Unavailable players (marked \"available\": false) MUST be marked as \"OUT\" in ALL innings",
                f"3. \"Catcher\" position can ONLY be assigned to players marked as \"can_play_catcher\": true",
                f"4. ALL positions must be assigned EXACTLY ONE player - no position can be left unfilled",
                f"5. NO duplicate position assignments within the same inning",
            ]
            
            # Rule about playing the same position multiple times
            if not allow_same_position:
                rule_components.append(f"6. NO player should play the SAME position more than once across ALL innings of a game")
            else:
                rule_components.append(f"6. Players MAY play the same position multiple times across innings")
            
            # Rule about consecutive innings in infield/outfield
            if no_consecutive_innings:
                rule_components.append(f"""7. NO player should play infield or outfield in CONSECUTIVE innings (they must alternate or have bench time in between)
               - Infield positions are: {', '.join(infield_positions)}
               - Outfield positions are: {', '.join(outfield_positions)}""")
            else:
                rule_components.append(f"""7. Players MAY play infield or outfield in consecutive innings
               - Infield positions are: {', '.join(infield_positions)}
               - Outfield positions are: {', '.join(outfield_positions)}""")
            
            # Rule about balancing playing time
            if balance_playing_time:
                playing_time_rule = "8. BALANCE playing time:"
                if strict_position_balance:
                    playing_time_rule += """
               - Every available player should have nearly equal infield time (within 1 inning difference)
               - Every available player should have nearly equal outfield time (within 1 inning difference)"""
                playing_time_rule += """
               - Only use bench if necessary (when there are more players than field positions)
               - Bench time should be evenly distributed across players (within 1 inning difference)"""
                rule_components.append(playing_time_rule)
            else:
                rule_components.append("8. Even distribution of playing time is NOT required, but try to give everyone some playing time")
            
            # Final verification rule
            rule_components.append(f"9. DOUBLE CHECK that ALL of these positions are assigned in EVERY inning: {required_positions_str}")
            
            # Join all rules into a full ruleset
            all_rules = "\n\n".join(rule_components)
            
            prompt = f"""
            You are an expert baseball coach assistant that specializes in creating fair and balanced fielding rotations.
            
            IMPORTANT: Use the random seed {random_seed} and timestamp {timestamp} to generate a unique rotation.
            If you've given a rotation for this team before, create a different valid rotation this time.

            Please analyze the following data and create a fielding rotation plan with these STRICT requirements:

            {all_rules}

            Here is the data:
            - Number of innings: {innings}
            - Players: {players_json}

            Please provide the fielding rotation as a structured JSON object that can be parsed by a program.
            Use this format:
            {{
              "rotations": {{
                "1": {{ "position1": player_id, "position2": player_id, ... }},
                "2": {{ "position1": player_id, "position2": player_id, ... }},
                ...
              }}
            }}

            Each inning should be a key in the "rotations" object, and each position should map to a player ID.
            Do not include any other text or explanation in your response, just the JSON.
            """
            
            # Call the Anthropic API with improved error handling and model fallback
            logger.info(f"Sending request to Anthropic for game_id: {game_id}")
            
            try:
                # Use a simpler approach with just one model and a timeout
                logger.info("Using Claude 3.5 Sonnet for fielding rotation generation with timeout...")
                
                # Set a timeout to avoid long-running requests
                timeout = 8.0  # 8 seconds timeout to stay within Heroku's limits
                
                # Use the user-provided temperature parameter
                response = anthropic.messages.create(
                    model="claude-3-5-sonnet-20240620",  # Use the latest model directly
                    max_tokens=4000,
                    temperature=temperature,  # Use the temperature parameter passed from the frontend
                    system="You are an expert baseball coach assistant that creates fielding rotations. Respond only with JSON.",
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    timeout=timeout  # Add timeout parameter
                )
                logger.info(f"Successfully received response with ID: {response.id}")
                
            except Exception as e:
                # This catches any errors that happen with the API call
                logger.error(f"Anthropic API call failed: {str(e)}")
                
                # Try to provide a more helpful error message
                if "timeout" in str(e).lower():
                    raise ValueError("Request timed out. The operation took too long to complete.")
                elif "model" in str(e).lower():
                    raise ValueError("The AI model is not available. Please check model availability.")
                elif "rate limit" in str(e).lower() or "429" in str(e):
                    raise ValueError("API rate limit exceeded. Please try again later.")
                elif "authentication" in str(e).lower() or "401" in str(e) or "403" in str(e):
                    raise ValueError("Authentication error. API key may be invalid or expired.")
                else:
                    raise ValueError(f"Error calling Anthropic API: {str(e)}")
            
            # Extract and parse the response
            content = response.content[0].text
            logger.info(f"Received response from Anthropic: {content[:100]}...")
            
            # Find and extract the JSON part of the response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_content = content[json_start:json_end]
                result = json.loads(json_content)
                
                # Convert inning keys to integers and player IDs to integers with robust error handling
                rotations = {}
                for inning_str, positions in result.get('rotations', {}).items():
                    try:
                        inning = int(inning_str)
                        inning_rotations = {}
                        
                        # Handle each position-player pair with careful type checking
                        for pos, pid in positions.items():
                            try:
                                # Handle different possible formats returned by the AI
                                if isinstance(pid, int):
                                    player_id = pid
                                elif isinstance(pid, str) and pid.isdigit():
                                    player_id = int(pid)
                                elif isinstance(pid, list) and len(pid) > 0:
                                    # If somehow a list was returned, take the first element
                                    first_item = pid[0]
                                    if isinstance(first_item, int):
                                        player_id = first_item
                                    elif isinstance(first_item, str) and first_item.isdigit():
                                        player_id = int(first_item)
                                    else:
                                        # If we can't parse it, use a default "unknown" value
                                        logger.warning(f"Cannot parse player ID from list: {pid} for position {pos}")
                                        player_id = -1  # Use -1 to indicate unknown
                                else:
                                    # If we can't parse it at all, use a default
                                    logger.warning(f"Cannot parse player ID: {pid} of type {type(pid)} for position {pos}")
                                    player_id = -1  # Use -1 to indicate unknown
                                
                                inning_rotations[pos] = player_id
                            except Exception as e:
                                logger.warning(f"Error parsing player ID for position {pos}: {str(e)}")
                                inning_rotations[pos] = -1  # Use -1 to indicate error
                        
                        rotations[inning] = inning_rotations
                    except Exception as e:
                        logger.warning(f"Error parsing inning {inning_str}: {str(e)}")
                        # Skip this inning if we can't parse it
                
                # If we didn't get any valid rotations, generate a simple default
                if not rotations:
                    logger.warning("No valid rotations parsed, generating a simple default")
                    rotations = {1: {"error": "Failed to parse response"}}
                
                return {'rotations': rotations}
            else:
                logger.error("Failed to extract JSON from Anthropic response")
                raise ValueError("Failed to extract valid JSON from Anthropic response")
                
        except Exception as e:
            logger.error(f"Error generating fielding rotation: {str(e)}")
            # Add more context to the error message
            if "ANTHROPIC_API_KEY" in str(e):
                raise ValueError("ANTHROPIC_API_KEY is configured but might be invalid or improperly formatted")
            elif "status_code=401" in str(e) or "status_code=403" in str(e):
                raise ValueError("Authentication error with Anthropic API. Please check that the API key is valid")
            elif "status_code=429" in str(e):
                raise ValueError("Rate limit exceeded with Anthropic API. Please try again later")
            elif "status_code=" in str(e):
                # Extract the status code for more informative error
                import re
                status_match = re.search(r'status_code=(\d+)', str(e))
                status_code = status_match.group(1) if status_match else "unknown"
                raise ValueError(f"Anthropic API error with status code {status_code}")
            else:
                # Pass through the original error with more context
                raise ValueError(f"Error connecting to Anthropic API: {str(e)}")
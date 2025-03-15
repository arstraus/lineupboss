"""
AI service for generating fielding rotations.
"""
import os
import json
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
        outfield_positions: List[str]
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
            if not api_key:
                logger.error("ANTHROPIC_API_KEY not found in environment variables")
                raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
            
            # Initialize Anthropic client
            anthropic = Anthropic(api_key=api_key)
            
            # Format the list of required positions for the prompt
            required_positions_str = ', '.join(required_positions)
            
            # Prepare the data for the prompt
            players_json = json.dumps(players, indent=2)
            
            # Create the prompt
            prompt = f"""
            You are an expert baseball coach assistant that specializes in creating fair and balanced fielding rotations.

            Please analyze the following data and create a fielding rotation plan with these STRICT requirements:

            1. MOST CRITICAL: In EVERY inning, ALL of these positions MUST be filled EXACTLY ONCE: {required_positions_str}
            2. Unavailable players (marked "available": false) MUST be marked as "OUT" in ALL innings
            3. "Catcher" position can ONLY be assigned to players marked as "can_play_catcher": true
            4. ALL positions must be assigned EXACTLY ONE player - no position can be left unfilled
            5. NO duplicate position assignments within the same inning
            6. NO player should play the SAME position more than once across ALL innings of a game
            7. NO player should play infield or outfield in CONSECUTIVE innings (they must alternate or have bench time in between)
               - Infield positions are: {', '.join(infield_positions)}
               - Outfield positions are: {', '.join(outfield_positions)}
            8. STRICTLY BALANCE playing time:
               - Every available player should have nearly equal infield time (within 1 inning difference)
               - Every available player should have nearly equal outfield time (within 1 inning difference)
               - Only use bench if necessary (when there are more players than field positions)
               - Bench time should be evenly distributed across players (within 1 inning difference)
            9. DOUBLE CHECK that ALL of these positions are assigned in EVERY inning: {required_positions_str}

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
            
            # Call the Anthropic API
            logger.info(f"Sending request to Anthropic for game_id: {game_id}")
            response = anthropic.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4000,
                temperature=0.1,
                system="You are an expert baseball coach assistant that creates fielding rotations. Respond only with JSON.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract and parse the response
            content = response.content[0].text
            logger.info(f"Received response from Anthropic: {content[:100]}...")
            
            # Find and extract the JSON part of the response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_content = content[json_start:json_end]
                result = json.loads(json_content)
                
                # Convert inning keys to integers and player IDs to integers
                rotations = {}
                for inning_str, positions in result.get('rotations', {}).items():
                    inning = int(inning_str)
                    rotations[inning] = {pos: int(pid) for pos, pid in positions.items()}
                
                return {'rotations': rotations}
            else:
                logger.error("Failed to extract JSON from Anthropic response")
                raise ValueError("Failed to extract valid JSON from Anthropic response")
                
        except Exception as e:
            logger.error(f"Error generating fielding rotation: {str(e)}")
            raise
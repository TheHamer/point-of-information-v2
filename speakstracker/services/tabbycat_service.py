"""
TabbycatService - Service layer for consuming the Tabbycat API.

Handles API authentication and provides methods for fetching:
- Speaker data and scores
- Team data and standings
- Round pairings and results
- Motions
"""

import requests
from requests.adapters import HTTPAdapter, Retry
from urllib.parse import urlparse
from typing import Optional, Dict, List, Any


class TabbycatService:
    """Service class for interacting with the Tabbycat API."""
    
    # Position mappings
    SIDE_TO_POSITION = {
        0: "OG",  # Opening Government (aff in 2-team)
        1: "OO",  # Opening Opposition (neg in 2-team)
        2: "CG",  # Closing Government
        3: "CO",  # Closing Opposition
        "aff": "OG",
        "neg": "OO",
        "og": "OG",
        "oo": "OO",
        "cg": "CG",
        "co": "CO",
    }
    
    # Speaker position mappings based on team position and speech order
    SPEAKER_POSITIONS = {
        "OG": {1: "PM", 2: "DPM"},
        "OO": {1: "LO", 2: "DLO"},
        "CG": {1: "MG", 2: "GW"},
        "CO": {1: "MO", 2: "OW"},
    }
    
    # Team points from placement
    PLACEMENT_TO_POINTS = {
        1: 3,  # 1st place
        2: 2,  # 2nd place
        3: 1,  # 3rd place
        4: 0,  # 4th place
    }
    
    def __init__(self, base_url: str):
        """
        Initialize the TabbycatService.
        
        Args:
            base_url: The base URL of the Tabbycat instance (e.g., https://tabbycat.example.com)
        """
        self.base_url = self._normalize_base_url(base_url)
        self.session = self._create_session()
        
    def _normalize_base_url(self, url: str) -> str:
        """Normalize the base URL, extracting the tournament slug if present."""
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        
        # Extract tournament slug from path if present
        path_parts = [p for p in parsed.path.split('/') if p]
        if path_parts:
            # Common Tabbycat URL patterns
            exclude_paths = ['api', 'results', 'participants', 'motions', 
                           'standings', 'tab', 'break', 'draw', 'feedback',
                           'admin', 'accounts', 'privateurls', 'checkins']
            for part in path_parts:
                if part not in exclude_paths and not part.startswith('v'):
                    self.tournament_slug = part
                    break
        
        return base
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        retry = Retry(total=3, connect=3, status=1, backoff_factor=0.5,
                     status_forcelist=[502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session
    
    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make a GET request to the API."""
        url = f"{self.base_url}/api/v1{endpoint}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def _paginate(self, endpoint: str, params: Optional[Dict] = None) -> List[Dict]:
        """Handle paginated API responses."""
        results = []
        params = params or {}
        
        while True:
            data = self._get(endpoint, params)
            if isinstance(data, list):
                return data
            
            results.extend(data.get('results', []))
            
            if not data.get('next'):
                break
            
            # Update offset for next page
            params['offset'] = params.get('offset', 0) + len(data.get('results', []))
        
        return results
    
    # ==================== Tournament Methods ====================
    
    def get_tournament(self, tournament_slug: str) -> Dict:
        """Get tournament information."""
        return self._get(f"/tournaments/{tournament_slug}")
    
    def get_rounds(self, tournament_slug: str) -> List[Dict]:
        """Get all rounds for a tournament."""
        return self._paginate(f"/tournaments/{tournament_slug}/rounds")
    
    # ==================== Speaker Methods ====================
    
    def get_speakers(self, tournament_slug: str) -> List[Dict]:
        """Get all speakers in a tournament."""
        return self._paginate(f"/tournaments/{tournament_slug}/speakers")
    
    def get_speaker(self, tournament_slug: str, speaker_id: int) -> Dict:
        """Get a specific speaker by ID."""
        return self._get(f"/tournaments/{tournament_slug}/speakers/{speaker_id}")
    
    def get_speaker_by_name(self, tournament_slug: str, name: str) -> Optional[Dict]:
        """Find a speaker by name."""
        speakers = self.get_speakers(tournament_slug)
        for speaker in speakers:
            speaker_name = speaker.get('name') or ''
            last_name = speaker.get('last_name')
            if not speaker_name:
                continue
            name_lower = name.lower()
            # Try matching name as-is (handles full name in 'name' field)
            if speaker_name.lower() == name_lower:
                return speaker
            # Try matching with last_name appended (handles first-name-only 'name' field)
            if last_name and f"{speaker_name} {last_name}".strip().lower() == name_lower:
                return speaker
        return None
    
    def get_speaker_standings(self, tournament_slug: str) -> List[Dict]:
        """Get speaker standings."""
        return self._paginate(f"/tournaments/{tournament_slug}/speakers/standings")
    
    def get_speaker_round_scores(self, tournament_slug: str) -> List[Dict]:
        """Get speaker scores per round."""
        return self._paginate(f"/tournaments/{tournament_slug}/speakers/standings/rounds")
    
    # ==================== Team Methods ====================
    
    def get_teams(self, tournament_slug: str) -> List[Dict]:
        """Get all teams in a tournament."""
        return self._paginate(f"/tournaments/{tournament_slug}/teams")
    
    def get_team(self, tournament_slug: str, team_id: int) -> Dict:
        """Get a specific team by ID."""
        return self._get(f"/tournaments/{tournament_slug}/teams/{team_id}")
    
    def get_team_by_name(self, tournament_slug: str, name: str) -> Optional[Dict]:
        """Find a team by name (short_name or long_name)."""
        teams = self.get_teams(tournament_slug)
        name_lower = name.lower()
        for team in teams:
            if (team.get('short_name', '').lower() == name_lower or 
                team.get('long_name', '').lower() == name_lower):
                return team
        return None
    
    def get_team_standings(self, tournament_slug: str) -> List[Dict]:
        """Get team standings."""
        return self._paginate(f"/tournaments/{tournament_slug}/teams/standings")
    
    def get_team_round_scores(self, tournament_slug: str) -> List[Dict]:
        """Get team scores per round."""
        return self._paginate(f"/tournaments/{tournament_slug}/teams/standings/rounds")
    
    # ==================== Round & Pairing Methods ====================
    
    def get_round_pairings(self, tournament_slug: str, round_seq: int) -> List[Dict]:
        """Get pairings for a specific round."""
        return self._paginate(f"/tournaments/{tournament_slug}/rounds/{round_seq}/pairings")
    
    def get_pairing_ballot(self, tournament_slug: str, round_seq: int, 
                          debate_id: int, confirmed: bool = True) -> List[Dict]:
        """Get the ballots/results for a specific debate."""
        params = {'confirmed': confirmed} if confirmed else {}
        return self._paginate(
            f"/tournaments/{tournament_slug}/rounds/{round_seq}/pairings/{debate_id}/ballots",
            params=params
        )
    
    # ==================== Motion Methods ====================
    
    def get_motions(self, tournament_slug: str) -> List[Dict]:
        """Get all motions for a tournament."""
        return self._paginate(f"/tournaments/{tournament_slug}/motions")
    
    # ==================== Data Extraction Methods ====================
    
    def get_person_data(self, tournament_slug: str, speaker_name: str) -> Dict:
        """
        Get comprehensive data for a speaker, similar to the old scraper.
        
        Returns:
            Dict with keys: team_name, partner, speaks, team_points, positions, motions
        """
        # Find the speaker
        speaker = self.get_speaker_by_name(tournament_slug, speaker_name)
        if not speaker:
            raise ValueError(f"Speaker '{speaker_name}' not found in tournament")
        
        # Get team info from speaker's team URL
        team_url = speaker.get('team', '')
        team_id = self._extract_id_from_url(team_url)
        team = self.get_team(tournament_slug, team_id)
        
        team_name = team.get('short_name') or team.get('long_name', '')
        
        # Find partner from team speakers
        partner = None
        partner_url = None
        for team_speaker in team.get('speakers', []):
            team_speaker_name = team_speaker.get('name') or ''
            if not team_speaker_name:
                continue
            # Check if this is NOT the speaker we're looking for (i.e. it's the partner)
            last_name = team_speaker.get('last_name')
            combined_name = f"{team_speaker_name} {last_name}".strip() if last_name else team_speaker_name
            is_same = (team_speaker_name.lower() == speaker_name.lower() or
                       combined_name.lower() == speaker_name.lower())
            if not is_same:
                partner = team_speaker_name
                partner_url = team_speaker.get('url', '')
                break
        
        # Get round scores for speaker (this endpoint returns 500 on some servers)
        speaker_scores = []
        scores_from_standings = True
        try:
            speaker_round_scores = self.get_speaker_round_scores(tournament_slug)
            speaker_scores = self._find_speaker_scores(speaker_round_scores, speaker.get('url'))
        except Exception:
            scores_from_standings = False

        # Get partner's round scores to determine speech order
        partner_scores = []
        if scores_from_standings and partner_url:
            partner_scores = self._find_speaker_scores(speaker_round_scores, partner_url)
        
        # Get team round scores
        team_round_scores = self.get_team_round_scores(tournament_slug)
        team_scores = self._find_team_scores(team_round_scores, team.get('url'))
        
        # Get rounds info
        rounds = self.get_rounds(tournament_slug)
        
        # Get motions
        motions = self._build_motions_dict(self.get_motions(tournament_slug), rounds)
        
        # Build speaks dict and extract speech positions
        speaks = {}
        speech_positions_by_round = {}  # round_seq -> speech_position (1 or 2)
        
        for round_data in speaker_scores:
            round_url = round_data.get('round', '')
            round_seq = self._get_round_seq_from_url(round_url, rounds)
            if round_seq and round_data.get('speeches'):
                # Get the first non-ghost score and its position
                for speech in round_data['speeches']:
                    if not speech.get('ghost', False):
                        speaks[f"R{round_seq}"] = speech.get('score', 0)
                        # Extract speech position (1 = first speaker, 2 = second speaker)
                        speech_pos = speech.get('position')
                        if speech_pos is not None:
                            speech_positions_by_round[round_seq] = speech_pos
                        break
        
        # Build team points dict
        team_points = {}
        for round_data in team_scores:
            round_url = round_data.get('round', '')
            round_seq = self._get_round_seq_from_url(round_url, rounds)
            if round_seq:
                team_points[f"R{round_seq}"] = round_data.get('points', 0)
        
        # Build positions dict by checking each round's pairings
        positions = {}
        opponent_positions = {}
        speaker_url = speaker.get('url', '').rstrip('/')

        for round_info in rounds:
            round_seq = round_info.get('seq')
            if round_seq is None:
                continue

            try:
                pairings = self.get_round_pairings(tournament_slug, round_seq)
                position_data = self._find_team_position_in_round(
                    pairings, team.get('url'), speaker_name, speaker_scores, round_seq,
                    tournament_slug, team_points.get(f"R{round_seq}"), team_round_scores
                )
                if position_data:
                    team_position = position_data['team_position']

                    # If standings/rounds endpoint failed, extract speaks from ballots
                    if not scores_from_standings:
                        ballot_speaks = self._extract_speaks_from_ballots(
                            position_data, speaker_url, round_seq
                        )
                        if ballot_speaks is not None:
                            speaks[f"R{round_seq}"] = ballot_speaks['score']
                            if ballot_speaks.get('position') is not None:
                                speech_positions_by_round[round_seq] = ballot_speaks['position']

                    # Determine speaker position from speech data
                    speech_order = speech_positions_by_round.get(round_seq)
                    speaker_position = self._get_speaker_role(team_position, speech_order)

                    positions[f"R{round_seq}"] = {
                        "team_position": team_position,
                        "speaker_position": speaker_position
                    }
                    # Store full call if available, otherwise just opponents
                    full_call = position_data.get('full_call')
                    if full_call:
                        opponent_positions[f"R{round_seq}"] = full_call
                    else:
                        opponent_positions[f"R{round_seq}"] = position_data.get('opponent_positions', [])
            except Exception:
                # Round might not have pairings yet
                continue
        
        return {
            "team_name": team_name,
            "partner": partner,
            "speaks": speaks,
            "team_points": team_points,
            "positions": positions,
            "motions": motions,
            "opponent_positions": opponent_positions
        }
    
    def _get_speaker_role(self, team_position: str, speech_order: Optional[int]) -> Optional[str]:
        """
        Get the speaker role (PM, DPM, LO, etc.) based on team position and speech order.
        
        Args:
            team_position: The team position (OG, OO, CG, CO)
            speech_order: The speech position (1 for first speaker, 2 for second speaker)
        
        Returns:
            Speaker role string or None if cannot be determined
        """
        if not team_position or speech_order is None:
            return None
        
        position_map = self.SPEAKER_POSITIONS.get(team_position)
        if not position_map:
            return None
        
        return position_map.get(speech_order)
    
    def _extract_id_from_url(self, url: str) -> int:
        """Extract the ID from an API URL."""
        parts = url.rstrip('/').split('/')
        for part in reversed(parts):
            if part.isdigit():
                return int(part)
        raise ValueError(f"Could not extract ID from URL: {url}")
    
    def _find_speaker_scores(self, all_scores: List[Dict], 
                            speaker_url: str) -> List[Dict]:
        """Find scores for a specific speaker from the standings/rounds data."""
        for entry in all_scores:
            if entry.get('speaker', '').rstrip('/') == speaker_url.rstrip('/'):
                return entry.get('rounds', [])
        return []
    
    def _find_team_scores(self, all_scores: List[Dict], 
                         team_url: str) -> List[Dict]:
        """Find scores for a specific team from the standings/rounds data."""
        for entry in all_scores:
            if entry.get('team', '').rstrip('/') == team_url.rstrip('/'):
                return entry.get('rounds', [])
        return []
    
    def _get_round_seq_from_url(self, round_url: str, 
                                rounds: List[Dict]) -> Optional[int]:
        """Get the round sequence number from a round URL."""
        round_url_clean = round_url.rstrip('/')
        for round_info in rounds:
            if round_info.get('url', '').rstrip('/') == round_url_clean:
                return round_info.get('seq')
        # Try extracting from URL directly
        parts = round_url_clean.split('/')
        for part in reversed(parts):
            if part.isdigit():
                return int(part)
        return None
    
    def _build_motions_dict(self, motions: List[Dict], 
                           rounds: List[Dict]) -> Dict:
        """Build a dict of motions keyed by round."""
        result = {}
        
        # Create a mapping of round URLs to sequence numbers
        round_url_to_seq = {}
        for r in rounds:
            url = r.get('url', '').rstrip('/')
            round_url_to_seq[url] = r.get('seq')
        
        for motion in motions:
            motion_rounds = motion.get('rounds', [])
            motion_text = motion.get('text', '')
            info_slide = motion.get('info_slide', '')
            
            for round_data in motion_rounds:
                round_url = round_data.get('round', '').rstrip('/')
                round_seq = round_url_to_seq.get(round_url) or round_data.get('seq')
                
                if round_seq:
                    result[f"R{round_seq}"] = {
                        "motion": motion_text,
                        "info_slide": info_slide
                    }
        
        return result
    
    def _find_team_position_in_round(self, pairings: List[Dict], team_url: str,
                                     speaker_name: str, 
                                     speaker_scores: List[Dict],
                                     round_seq: int = None,
                                     tournament_slug: str = None,
                                     user_team_points: int = None,
                                     team_round_scores: List[Dict] = None) -> Optional[Dict]:
        """Find a team's position in a round from the pairings data."""
        team_url_clean = team_url.rstrip('/')
        
        for pairing in pairings:
            teams_in_debate = pairing.get('teams', [])
            opponent_positions = []
            team_position = None
            
            for debate_team in teams_in_debate:
                dt_team_url = debate_team.get('team', '').rstrip('/')
                side = debate_team.get('side')
                position = self._side_to_position(side)
                
                if dt_team_url == team_url_clean:
                    team_position = position
                else:
                    if position:
                        opponent_positions.append(position)
            
            if team_position:
                result = {
                    "team_position": team_position,
                    "opponent_positions": opponent_positions
                }
                
                # First, try to construct full call from ballots
                full_call = None
                ballots = None
                if tournament_slug and round_seq is not None:
                    try:
                        debate_id = pairing.get('id')
                        if debate_id:
                            ballots = self.get_pairing_ballot(tournament_slug, round_seq, debate_id, confirmed=True)
                            if ballots:
                                full_call = self._construct_full_call_from_ballots(ballots, teams_in_debate)
                    except Exception:
                        # If ballot fetch fails, continue to fallback method
                        pass
                
                # If ballots didn't work, fall back to team round scores
                if not full_call and user_team_points is not None and team_round_scores:
                    full_call = self._construct_full_call_from_scores(
                        teams_in_debate, team_url, team_position, user_team_points,
                        opponent_positions, team_round_scores, round_seq
                    )
                
                if full_call:
                    result['full_call'] = full_call
                if ballots:
                    result['ballots'] = ballots

                return result
        
        return None
    
    def _construct_full_call_from_ballots(self, ballots: List[Dict], 
                                         teams_in_debate: List[Dict]) -> Optional[List[str]]:
        """
        Construct the full call (all 4 teams in rank order) from ballot data.
        
        Ballots contain result.sheets[0].teams with side and points for each team.
        Returns a list of 4 team positions in rank order (1st to 4th), or None if insufficient data.
        """
        if not ballots or not teams_in_debate:
            return None
        
        # Use the first confirmed ballot (ballots should already be filtered to confirmed)
        ballot = ballots[0] if ballots else None
        if not ballot:
            return None
        
        result = ballot.get('result')
        if not result:
            return None
        
        sheets = result.get('sheets', [])
        if not sheets:
            return None
        
        # Get team results from the first sheet
        team_results = sheets[0].get('teams', [])
        if len(team_results) != 4:
            return None
        
        # Create a mapping of team URL to position and points
        team_url_to_data = {}
        for debate_team in teams_in_debate:
            dt_team_url = debate_team.get('team', '').rstrip('/')
            side = debate_team.get('side')
            position = self._side_to_position(side)
            if position:
                team_url_to_data[dt_team_url] = {'position': position}
        
        # Map team results to positions and points
        position_to_points = {}
        for team_result in team_results:
            team_url = team_result.get('team', '').rstrip('/')
            points = team_result.get('points')
            if team_url in team_url_to_data and points is not None:
                position = team_url_to_data[team_url]['position']
                position_to_points[position] = points
        
        # If we have points for all 4 teams, construct the call
        if len(position_to_points) == 4:
            # Sort positions by points (descending: 3, 2, 1, 0)
            sorted_positions = sorted(
                position_to_points.keys(),
                key=lambda pos: position_to_points.get(pos, -1),
                reverse=True
            )
            return sorted_positions
        
        return None
    
    def _construct_full_call_from_scores(self, teams_in_debate: List[Dict], user_team_url: str,
                                        user_position: str, user_points: int,
                                        opponent_positions: List[str],
                                        team_round_scores: List[Dict],
                                        round_seq: int) -> Optional[List[str]]:
        """
        Construct the full call (all 4 teams in rank order) from team round scores.
        
        Returns a list of 4 team positions in rank order (1st to 4th), or None if insufficient data.
        """
        if not teams_in_debate or not team_round_scores:
            return None
        
        # Create a mapping of team URL to position (for ALL teams in debate)
        team_url_to_position = {}
        for debate_team in teams_in_debate:
            dt_team_url = debate_team.get('team', '').rstrip('/')
            side = debate_team.get('side')
            position = self._side_to_position(side)
            if position:
                team_url_to_position[dt_team_url] = position
        
        # Map positions to points, starting with user's position
        position_to_points = {user_position: user_points}
        
        # Look up all team points from team round scores
        for entry in team_round_scores:
            team_url = entry.get('team', '').rstrip('/')
            rounds = entry.get('rounds', [])
            
            for round_data in rounds:
                round_url = round_data.get('round', '')
                # Extract round_seq from round_data.seq or from URL
                round_seq_from_data = round_data.get('seq')
                if round_seq_from_data is None and round_url:
                    # Fallback: extract from URL directly (same logic as _get_round_seq_from_url)
                    round_url_clean = round_url.rstrip('/')
                    parts = round_url_clean.split('/')
                    for part in reversed(parts):
                        if part.isdigit():
                            round_seq_from_data = int(part)
                            break
                if round_seq_from_data == round_seq:
                    points = round_data.get('points')
                    if points is not None and team_url in team_url_to_position:
                        position = team_url_to_position[team_url]
                        position_to_points[position] = points
                        break
        
        # If we have points for all 4 teams, construct the call
        if len(team_url_to_position) == 4 and len(position_to_points) == 4:
            # Sort positions by points (descending: 3, 2, 1, 0)
            sorted_positions = sorted(
                position_to_points.keys(),
                key=lambda pos: position_to_points.get(pos, -1),
                reverse=True
            )
            return sorted_positions
        
        return None
    
    def _extract_speaks_from_ballots(self, position_data: Dict, speaker_url: str,
                                     round_seq: int) -> Optional[Dict]:
        """
        Extract a speaker's score and speech position from ballot data.

        Returns dict with 'score' and 'position' keys, or None if not found.
        """
        ballots = position_data.get('ballots')
        if not ballots:
            return None

        ballot = ballots[0]
        result = ballot.get('result')
        if not result:
            return None

        for sheet in result.get('sheets', []):
            for team_result in sheet.get('teams', []):
                for speech_idx, speech in enumerate(team_result.get('speeches', []), start=1):
                    spk_url = speech.get('speaker', '').rstrip('/')
                    if spk_url == speaker_url and not speech.get('ghost', False):
                        return {
                            'score': speech.get('score', 0),
                            'position': speech_idx
                        }

        return None

    def _side_to_position(self, side: Any) -> Optional[str]:
        """Convert a side value to a team position."""
        if side is None:
            return None
        
        # Handle numeric sides (BP format)
        if isinstance(side, (int, float)):
            return self.SIDE_TO_POSITION.get(int(side))
        
        # Handle string sides
        side_lower = str(side).lower()
        return self.SIDE_TO_POSITION.get(side_lower)
    
def extract_tournament_slug_from_url(url: str) -> Optional[str]:
    """
    Extract the tournament slug from a Tabbycat URL.
    
    Examples:
        https://tabbycat.example.com/demo/ -> 'demo'
        https://tabbycat.example.com/demo/participants/ -> 'demo'
    """
    parsed = urlparse(url)
    path_parts = [p for p in parsed.path.split('/') if p]
    
    exclude_paths = ['api', 'v1', 'results', 'participants', 'motions', 
                    'standings', 'tab', 'break', 'draw', 'feedback',
                    'admin', 'accounts', 'privateurls', 'checkins',
                    'rounds', 'speakers', 'teams', 'adjudicators']
    
    for part in path_parts:
        if part not in exclude_paths:
            return part
    
    return None


def extract_base_url(url: str) -> str:
    """Extract the base URL (scheme + netloc) from a full URL."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


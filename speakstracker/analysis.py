import json
from collections import defaultdict
from django.db.models import Avg, Max


class speaks_analysis:
    """Analysis class for calculating speaker statistics."""
    
    # Team positions for BP format
    TEAM_POSITIONS = ["OG", "OO", "CG", "CO"]
    
    # Points to rank mapping
    POINTS_TO_RANK = {3: 1, 2: 2, 1: 3, 0: 4}

    def __init__(self, user_qs):
        self.user_qs = user_qs
    
    def _safe_round(self, value, default=0):
        """Helper method to safely round a value, returning default if None."""
        return round(value, 2) if value is not None else default
    
    def _calculate_averages(self, queryset):
        """Helper method to calculate averages for a queryset."""
        speak_avg = self._safe_round(queryset.aggregate(Avg('speaker_score'))['speaker_score__avg'])
        point_avg = self._safe_round(queryset.aggregate(Avg('team_points'))['team_points__avg'])
        count = queryset.count() or 0
        return speak_avg, point_avg, count

    def speaks_per_position(self):
        """Calculate average speaks per speaker position."""
        position_qs = self.user_qs.exclude(speaker_position__isnull=True)
        if not position_qs.exists():
            return None, None

        position_avg = {}
        positions = ["PM", "DPM", "LO", "DLO", "MG", "GW", "MO", "OW"]

        for position in positions:
            filtered_qs = self.user_qs.filter(speaker_position=position)
            speak_avg, point_avg, count = self._calculate_averages(filtered_qs)
            position_avg[position] = [position, count, speak_avg, point_avg]

        grouped_positions = {
            "PM and LO": ["PM and LO"],
            "Deputy": ["Deputy"],
            "Extension": ["Extension"],
            "Whip": ["Whip"],
            "OG": ["OG"],
            "OO": ["OO"],
            "CG": ["CG"],
            "CO": ["CO"]
        }

        groups = [
            ["PM and LO", "PM", "LO"],
            ["Deputy", "DPM", "DLO"],
            ["Extension", "MG", "MO"],
            ["Whip", "OW", "GW"],
            ["OG", "PM", "DPM"],
            ["OO", "LO", "DLO"],
            ["CG", "MG", "GW"],
            ["CO", "MO", "OW"]
        ]

        for group in groups:
            pos1_data = position_avg[group[1]]
            pos2_data = position_avg[group[2]]
            
            # Count should be summed, not averaged
            count1 = pos1_data[1] or 0
            count2 = pos2_data[1] or 0
            total_count = count1 + count2
            grouped_positions[group[0]].append(round(total_count, 2))
            
            # Calculate weighted averages for speak_avg and point_avg
            if total_count > 0:
                # Weighted average for speak_avg
                speak_avg1 = pos1_data[2] or 0
                speak_avg2 = pos2_data[2] or 0
                weighted_speak_avg = (speak_avg1 * count1 + speak_avg2 * count2) / total_count
                grouped_positions[group[0]].append(round(weighted_speak_avg, 2))
                
                # Weighted average for point_avg
                point_avg1 = pos1_data[3] or 0
                point_avg2 = pos2_data[3] or 0
                weighted_point_avg = (point_avg1 * count1 + point_avg2 * count2) / total_count
                grouped_positions[group[0]].append(round(weighted_point_avg, 2))
            else:
                # If no data, set to 0
                grouped_positions[group[0]].append(0)
                grouped_positions[group[0]].append(0)

        return position_avg, grouped_positions,

    def speaks_per_room_points(self):
        """Calculate average speaks per room points (legacy method)."""
        max_points = self.user_qs.aggregate(Max('room_points'))['room_points__max']

        if not max_points:
            return None
        
        room_points_avg = {}

        for points in range(max_points + 1):
            points_qs = self.user_qs.filter(room_points=points)
            speak_avg, point_avg, count = self._calculate_averages(points_qs)
            room_points_avg[points] = [points, count, speak_avg, point_avg]

        return room_points_avg
    
    def get_average_points_chart_data(self):
        """
        Get chart data for average points visualization.
        Each debate round is a separate data point (no bucketing/averaging).
        
        Returns:
            Tuple of (speaker_data, team_data, best_fit_line) where:
            - speaker_data: List of dicts with x (average points) and y (speaker_score) values
            - team_data: List of dicts with x (average points) and y (team_points) values
            - best_fit_line: Dict with 'speaker' and 'team' best fit line data
        """
        # Filter to only entries with valid round numbers
        valid_qs = self.user_qs.exclude(round__isnull=True)
        
        if not valid_qs.exists():
            return None, None, None
        
        # Speaker score chart data - individual points
        speaker_data = []
        # Team points chart data - individual points
        team_data = []
        
        for entry in valid_qs:
            # Use model property for average points calculation
            avg_pts = entry.average_points_so_far
            
            # Add speaker score point if available
            if entry.speaker_score is not None:
                speaker_data.append({
                    'x': round(avg_pts, 3),
                    'y': entry.speaker_score
                })
            
            # Add team points point if available
            if entry.team_points is not None:
                team_data.append({
                    'x': round(avg_pts, 3),
                    'y': entry.team_points
                })
        
        # Calculate best fit lines
        best_fit_line = self._calculate_best_fit_lines(speaker_data, team_data)
        
        return speaker_data, team_data, best_fit_line
    
    def _calculate_best_fit_line(self, data):
        """
        Calculate best fit line for given data.
        
        Args:
            data: List of dicts with 'x' and 'y' keys
        
        Returns:
            Dict with 'slope', 'intercept', and 'points', or None if insufficient data
        """
        import numpy as np
        
        if not data or len(data) < 2:
            return None
        
        x_vals = [d['x'] for d in data]
        y_vals = [d['y'] for d in data]
        
        try:
            slope, intercept = np.polyfit(x_vals, y_vals, 1)
            x_min, x_max = min(x_vals), max(x_vals)
            
            return {
                'slope': float(slope),
                'intercept': float(intercept),
                'points': [
                    {'x': x_min, 'y': float(slope * x_min + intercept)},
                    {'x': x_max, 'y': float(slope * x_max + intercept)}
                ]
            }
        except Exception:
            return None
    
    def _calculate_best_fit_lines(self, speaker_data, team_data):
        """
        Calculate best fit lines for speaker and team data.
        
        Returns:
            Dict with 'speaker' and 'team' keys, each containing:
            {'slope': float, 'intercept': float, 'points': [{'x': float, 'y': float}, ...]}
        """
        return {
            'speaker': self._calculate_best_fit_line(speaker_data),
            'team': self._calculate_best_fit_line(team_data)
        }

    def speaks_per_partner(self):
        """Calculate average speaks per partner."""
        partner_avg = {}
        partners = self.user_qs.exclude(partner__isnull=True).values_list("partner", flat=True).distinct()

        for partner in partners:
            partner_qs = self.user_qs.filter(partner=partner)
            speak_avg, point_avg, count = self._calculate_averages(partner_qs)
            partner_avg[partner] = [partner, count, speak_avg, point_avg]

        return partner_avg if partner_avg else None

    def speaks_per_motion_type(self):
        """Calculate average speaks per motion type."""
        motion_avg = {}
        motion_types = self.user_qs.exclude(motion_type__isnull=True).values_list("motion_type", flat=True).distinct()

        for motion_type in motion_types:
            motion_qs = self.user_qs.filter(motion_type=motion_type)
            speak_avg, point_avg, count = self._calculate_averages(motion_qs)
            motion_avg[motion_type] = [motion_type, count, speak_avg, point_avg]

        return motion_avg if motion_avg else None
    
    def positional_win_rate_heatmap(self):
        """
        Calculate win rates for each position against other positions.
        
        A "win" is when your position placed higher (got more points) 
        than the opponent position in the same round.
        
        For example, if you are CG and you are above OG in the call, that counts
        as a win against OG when you are CG.
        
        Returns:
            Dict structured as:
            {
                "OG": {"OG": null, "OO": 75.0, "CG": 70.0, "CO": 80.0},
                "OO": {...},
                ...
            }
            
            Each value is the percentage (0-100) of times the row position
            placed higher than the column position (i.e., how often you win against that position).
        """
        # Filter to entries with team position and team points
        valid_qs = self.user_qs.exclude(team_position__isnull=True).exclude(team_points__isnull=True)
        
        if not valid_qs.exists():
            return None
        
        # Initialize result structure
        result = {}
        for pos in self.TEAM_POSITIONS:
            result[pos] = {op: None for op in self.TEAM_POSITIONS}
        
        # Track wins and total matchups
        # Key: (my_position, opponent_position) -> {'wins': count, 'total': count}
        matchups = defaultdict(lambda: {'wins': 0, 'total': 0})
        
        for entry in valid_qs:
            my_position = entry.team_position
            my_points = entry.team_points
            my_rank = self.POINTS_TO_RANK.get(my_points)
            
            if not my_position or my_rank is None:
                continue
            
            # Get full call from stored data (4 positions in rank order: 1st to 4th)
            full_call = []
            if entry.opponent_positions:
                try:
                    full_call = json.loads(entry.opponent_positions)
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # If we have a full call (4 positions), use it to determine exact rankings
            if len(full_call) == 4 and my_position in full_call:
                # Find my position in the call to get my rank index
                my_index = full_call.index(my_position)
                
                # All positions ranked higher than me (lower index) beat me (no win)
                for i in range(my_index):
                    opponent_pos = full_call[i]
                    if opponent_pos != my_position and opponent_pos in self.TEAM_POSITIONS:
                        key = (my_position, opponent_pos)
                        matchups[key]['total'] += 1
                        # No win (they beat me)
                
                # All positions ranked lower than me (higher index) lost to me (win)
                for i in range(my_index + 1, len(full_call)):
                    opponent_pos = full_call[i]
                    if opponent_pos != my_position and opponent_pos in self.TEAM_POSITIONS:
                        key = (my_position, opponent_pos)
                        matchups[key]['total'] += 1
                        matchups[key]['wins'] += 1
            # Skip entries without full calls
        
        # Calculate win percentages
        for (my_pos, opp_pos), data in matchups.items():
            if data['total'] > 0:
                win_rate = round((data['wins'] / data['total']) * 100, 1)
                result[my_pos][opp_pos] = win_rate
        
        # Diagonal should be null (can't play against yourself)
        for pos in self.TEAM_POSITIONS:
            result[pos][pos] = None
        
        return result
    
    def get_heatmap_data_for_position(self, primary_position):
        """
        Get heatmap data when a specific primary position is selected.
        
        Args:
            primary_position: The selected primary position (OG, OO, CG, CO)
        
        Returns:
            Dict with win rates against each opponent position, or None if no data.
            Shows how often you beat each opponent position when you play the primary position.
        """
        if primary_position not in self.TEAM_POSITIONS:
            return None
        
        heatmap = self.positional_win_rate_heatmap()
        
        if not heatmap:
            return None
        
        return heatmap.get(primary_position)
    
    def get_filter_options(self):
        """
        Get available filter options based on the current queryset.
        
        Returns:
            Dict with available filter values for UI dropdowns/buttons.
        """
        return {
            'team_positions': list(self.user_qs.exclude(
                team_position__isnull=True
            ).values_list('team_position', flat=True).distinct()),
            
            'speaker_positions': list(self.user_qs.exclude(
                speaker_position__isnull=True
            ).values_list('speaker_position', flat=True).distinct()),
            
            'partners': list(self.user_qs.exclude(
                partner__isnull=True
            ).values_list('partner', flat=True).distinct()),
            
            'max_room_points': self.user_qs.aggregate(
                Max('room_points')
            )['room_points__max'] or 0,
            
            'date_range': {
                'min': self.user_qs.exclude(date__isnull=True).order_by('date').values_list('date', flat=True).first(),
                'max': self.user_qs.exclude(date__isnull=True).order_by('-date').values_list('date', flat=True).first(),
            }
        }

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

    def speaks_per_position(self):
        """Calculate average speaks per speaker position."""
        position_qs = self.user_qs.exclude(speaker_position__isnull=True)
        if not position_qs:
            return None, None

        position_avg = {}
        positions = ["PM", "DPM", "LO", "DLO", "MG", "GW", "MO", "OW"]

        for position in positions:
            position_qs = self.user_qs.filter(speaker_position=position)
            speak_avg = position_qs.aggregate(Avg('speaker_score'))['speaker_score__avg']
            point_avg = position_qs.aggregate(Avg('team_points'))['team_points__avg']
            no_entires = position_qs.count()

            if speak_avg is None:
                speak_avg = 0
            else:
                speak_avg = round(speak_avg, 2)
            
            if point_avg is None:
                point_avg = 0
            else:
                point_avg = round(point_avg, 2)

            if no_entires is None:
                no_entires = 0

            position_avg.update({position: [position, no_entires, speak_avg, point_avg]})

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
            for i in range(1,4):
                if position_avg[group[1]][i] and position_avg[group[2]][i]:
                    grouped_positions[group[0]].append(round(position_avg[group[1]][i] + position_avg[group[2]][i], 2)/2)
                else:
                    grouped_positions[group[0]].append(round(position_avg[group[1]][i] + position_avg[group[2]][i], 2))

        return position_avg, grouped_positions,

    def speaks_per_room_points(self):
        """Calculate average speaks per room points (legacy method)."""
        max_points = self.user_qs.aggregate(Max('room_points'))['room_points__max']

        if not max_points:
            return None
        
        room_points_avg = {}

        for points in range(max_points+1):
            points_qs = self.user_qs.filter(room_points=points)
            speak_avg = points_qs.aggregate(Avg('speaker_score'))['speaker_score__avg']
            point_avg = points_qs.aggregate(Avg('team_points'))['team_points__avg']
            no_entires = points_qs.count()

            if speak_avg is None:
                speak_avg = 0
            else:
                speak_avg = round(speak_avg, 2)
            
            if point_avg is None:
                point_avg = 0
            else:
                point_avg = round(point_avg, 2)

            if no_entires is None:
                no_entires = 0

            room_points_avg.update({points: [points, no_entires, speak_avg, point_avg]})

        return room_points_avg
    
    def speaks_per_average_points(self, bucket_size=0.25):
        """
        Calculate average speaks grouped by average points so far.
        
        Uses the model's average_points_so_far property for calculation.
        
        Args:
            bucket_size: Size of each average points bucket (default 0.25)
        
        Returns:
            Dict with bucket ranges as keys, containing:
            - bucket_label (str): The bucket range label (e.g., "1.00-1.25")
            - avg_points (float): The bucket midpoint for x-axis
            - count (int): Number of entries
            - speak_avg (float): Average speaker score
            - team_points_avg (float): Average team points in round
        """
        # Filter to only entries with valid round numbers
        valid_qs = self.user_qs.exclude(round__isnull=True)
        
        if not valid_qs.exists():
            return None
        
        # Calculate average points for each entry and group into buckets
        buckets = defaultdict(list)
        
        for entry in valid_qs:
            # Use model property for average points calculation
            avg_pts = entry.average_points_so_far
            
            # Determine bucket (floor to nearest bucket_size)
            bucket_floor = (avg_pts // bucket_size) * bucket_size
            bucket_key = round(bucket_floor, 2)
            
            buckets[bucket_key].append({
                'speaker_score': entry.speaker_score,
                'team_points': entry.team_points
            })
        
        # Calculate averages for each bucket
        result = {}
        
        for bucket_key in sorted(buckets.keys()):
            entries = buckets[bucket_key]
            count = len(entries)
            
            # Calculate speaker score average
            scores = [e['speaker_score'] for e in entries if e['speaker_score'] is not None]
            speak_avg = round(sum(scores) / len(scores), 2) if scores else 0
            
            # Calculate team points average
            points = [e['team_points'] for e in entries if e['team_points'] is not None]
            team_points_avg = round(sum(points) / len(points), 2) if points else 0
            
            bucket_end = round(bucket_key + bucket_size, 2)
            bucket_label = f"{bucket_key:.2f}-{bucket_end:.2f}"
            
            result[bucket_key] = {
                'bucket_label': bucket_label,
                'avg_points': round(bucket_key + bucket_size / 2, 3),  # Midpoint for x-axis
                'count': count,
                'speak_avg': speak_avg,
                'team_points_avg': team_points_avg
            }
        
        return result
    
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
    
    def _calculate_best_fit_lines(self, speaker_data, team_data):
        """
        Calculate best fit lines for speaker and team data.
        
        Returns:
            Dict with 'speaker' and 'team' keys, each containing:
            {'slope': float, 'intercept': float, 'points': [{'x': float, 'y': float}, ...]}
        """
        import numpy as np
        
        result = {'speaker': None, 'team': None}
        
        # Best fit line for speaker scores
        if speaker_data and len(speaker_data) > 1:
            x_vals = [d['x'] for d in speaker_data]
            y_vals = [d['y'] for d in speaker_data]
            
            try:
                slope, intercept = np.polyfit(x_vals, y_vals, 1)
                x_min, x_max = min(x_vals), max(x_vals)
                
                result['speaker'] = {
                    'slope': float(slope),
                    'intercept': float(intercept),
                    'points': [
                        {'x': x_min, 'y': float(slope * x_min + intercept)},
                        {'x': x_max, 'y': float(slope * x_max + intercept)}
                    ]
                }
            except Exception as e:
                pass
        
        # Best fit line for team points
        if team_data and len(team_data) > 1:
            x_vals = [d['x'] for d in team_data]
            y_vals = [d['y'] for d in team_data]
            
            try:
                slope, intercept = np.polyfit(x_vals, y_vals, 1)
                x_min, x_max = min(x_vals), max(x_vals)
                
                result['team'] = {
                    'slope': float(slope),
                    'intercept': float(intercept),
                    'points': [
                        {'x': x_min, 'y': float(slope * x_min + intercept)},
                        {'x': x_max, 'y': float(slope * x_max + intercept)}
                    ]
                }
            except Exception as e:
                pass
        
        return result

    def speaks_per_partner(self):
        """Calculate average speaks per partner."""
        partner_avg = {}
        partners = set(self.user_qs.values_list("partner"))
        
        for partner in partners:

            partner = partner[0]

            if partner != None:
                partner_qs = self.user_qs.filter(partner=partner)
                speak_avg = partner_qs.aggregate(Avg('speaker_score'))['speaker_score__avg']
                point_avg = partner_qs.aggregate(Avg('team_points'))['team_points__avg']
                no_entires = partner_qs.count()

                if speak_avg is None:
                    speak_avg = 0
                else:
                    speak_avg = round(speak_avg, 2)
                
                if point_avg is None:
                    point_avg = 0
                else:
                    point_avg = round(point_avg, 2)

                if no_entires is None:
                    no_entires = 0

                partner_avg.update({partner: [partner, no_entires, speak_avg, point_avg]})

        if not partner_avg:
            return None
        
        return partner_avg

    def speaks_per_motion_type(self):
        """Calculate average speaks per motion type."""
        motion_avg = {}
        motion_types = set(self.user_qs.values_list("motion_type"))

        for montion_type in motion_types:

            montion_type = montion_type[0]

            if montion_type != None:
                motion_qs = self.user_qs.filter(motion_type=montion_type)
                speak_avg = motion_qs.aggregate(Avg('speaker_score'))['speaker_score__avg']
                point_avg = motion_qs.aggregate(Avg('team_points'))['team_points__avg']
                no_entires = motion_qs.count()

                if speak_avg is None:
                    speak_avg = 0
                else:
                    speak_avg = round(speak_avg, 2)
                
                if point_avg is None:
                    point_avg = 0
                else:
                    point_avg = round(point_avg, 2)

                if no_entires is None:
                    no_entires = 0

                motion_avg.update({montion_type: [montion_type, no_entires, speak_avg, point_avg]})

        if not motion_avg:
            return None
            
        return motion_avg
    
    def positional_win_rate_heatmap(self, primary_position=None):
        """
        Calculate win rates for each position against other positions.
        
        A "win" is when your position placed higher (got more points) 
        than the opponent position in the same round.
        
        For example, if you are CG and you are above OG in the call, that counts
        as a win against OG when you are CG.
        
        Args:
            primary_position: If specified, only calculate for this position.
                            If None, calculate for all positions.
        
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
        valid_qs = self.user_qs.exclude(team_position__isnull=True)
        valid_qs = valid_qs.exclude(team_points__isnull=True)
        
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
            
            else:
                # Fallback: If we don't have full call, use points-based estimation
                # In BP, if I got N points, I beat (N) teams
                # We distribute wins proportionally across opponent positions
                opponent_positions = [p for p in self.TEAM_POSITIONS if p != my_position]
                
                if not opponent_positions:
                    continue
                
                # Number of teams I beat = my_points
                teams_i_beat = my_points
                
                for opponent_pos in opponent_positions:
                    key = (my_position, opponent_pos)
                    matchups[key]['total'] += 1
                    
                    # Distribute wins proportionally
                    if teams_i_beat > 0:
                        # Each opponent has equal chance of being beaten by me
                        matchups[key]['wins'] += teams_i_beat / len(opponent_positions)
        
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

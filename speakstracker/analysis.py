from django.db.models import Avg, Max

class speaks_analysis:

    def __init__(self, user_qs):

        self.user_qs = user_qs

    def speaks_per_position(self):

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

    def speaks_per_partner(self):
        
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
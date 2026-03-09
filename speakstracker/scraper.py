from bs4 import BeautifulSoup
import json
import requests
from requests.adapters import HTTPAdapter, Retry
import re


class PersonDataScraper:
    
    def __init__(self, path):

        self.path = self.__cut_url(path)
        
    def get_person(self, name):

        team_name, partner = self.__get_team_name_and_partner(name)
        speaks = self.__get_speaks(name)
        team_points = self.__get_points(team_name)
        
        motions = self.__get_motions()
        if not motions:
            for round_no in range(1, len(team_points) + 1):
                motions.update({f"R{round_no}":
                                {"motion": None, "info_slide": None}})
        
        all_positions = {}
        
        for round_no in range(1, len(team_points) + 1):
            full_path = self.path + f"results/round/{round_no}/"
            position, speaker_position = self.__get_round_results(full_path, team_name, name)
            all_positions.update({f"R{round_no}": {"team_position": position, "speaker_position": speaker_position} })
                     
        person_data = {
            "team_name": team_name,
            "partner": partner,
            "speaks": speaks,
            "team_points": team_points,
            "positions": all_positions,
            "motions": motions
            }
        
        return person_data

    def __cut_url(self, url):
        
        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        response = session.get(url)
        new_url = response.url
        
        ends = [
            '/motions/',
            '/participants/',
            '/privateurls/',
            '/results/',
            '/standings/',
            '/tab/',
            '/break/',
            '/checkins/',
            '/draw/',
            '/feedback/',
            "/admin/",
            "/accounts/"]
        
        for path in ends:
            index = url.find(path)
            if index != -1:
                return new_url[:index+1]        
            
        return new_url
        
    def __get_soup(self, page_path):

        html_content = requests.get(page_path).text

        soup = BeautifulSoup(html_content, 'html.parser')

        return soup

    def __extract_vue_data(self, soup):
        """Find the script tag containing tablesData/vueData and extract the JSON array."""
        for tag in soup.find_all('script'):
            text = tag.text
            if not text:
                continue
            # Try to find tablesData pattern (newer Tabbycat versions)
            if 'tablesData' in text:
                match = re.search(r'tablesData:\s*\[', text)
                if match:
                    # Find the start of the array
                    start = match.start() + text[match.start():].index('[')
                    # Extract from '[' to the end, trimming trailing JS
                    raw = text[start:]
                    # The array ends before the closing of the vueData object
                    # Parse by finding balanced brackets
                    bracket_depth = 0
                    end = 0
                    for i, ch in enumerate(raw):
                        if ch == '[':
                            bracket_depth += 1
                        elif ch == ']':
                            bracket_depth -= 1
                            if bracket_depth == 0:
                                end = i + 1
                                break
                    array_str = raw[:end]
                    data_list = json.loads(array_str)
                    return data_list
            # Legacy pattern: script tag text starts with data directly
            split_result = text.split("[", 1)
            if len(split_result) >= 2 and '"head"' in text:
                cut_tag_0 = split_result[1][:-10]
                return json.loads(cut_tag_0)
        raise ValueError("Could not find tablesData in any script tag")
    
    def __get_team_name_and_partner(self, name):
        new_path = self.path + "participants/list/"
        soup = self.__get_soup(new_path)
        data_list = self.__extract_vue_data(soup)
        # participants page has multiple tables; speaker data is the one with "name" and "team" keys
        raw_data_speaker = None
        for table in data_list:
            keys = [h["key"] for h in table.get("head", [])]
            if "name" in keys and "team" in keys:
                raw_data_speaker = table
                break
        if raw_data_speaker is None:
            raise ValueError("Could not find speaker table in participant data")
                
        team_index = None
        name_index = None
        for index, value in enumerate(raw_data_speaker["head"]):
            if value["key"] == "team":
                team_index = index
            elif value["key"] == "name":
                name_index = index
        
        if team_index is None or name_index is None:
            raise ValueError("Could not find 'team' or 'name' columns in participant data")
                
        team_name = None
        for row in raw_data_speaker["data"]:
            if row[name_index]["text"] == name:
                team_name = row[team_index]["text"]
                break
        
        if team_name is None:
            raise ValueError(f"Speaker '{name}' not found in participant list")
                
        partner_name = None
        for row in raw_data_speaker["data"]:
            if row[team_index]["text"] == team_name and row[name_index]["text"] != name:
                partner_name = row[name_index]["text"]
                break
        
        if partner_name is None:
            raise ValueError(f"Partner not found for speaker '{name}' in team '{team_name}'")
        
        return team_name, partner_name
    
    def __get_speaks(self, name):

        new_path = self.path + "tab/speaker/"
        soup = self.__get_soup(new_path)
        data_list = self.__extract_vue_data(soup)
        raw_data = data_list[0] if isinstance(data_list, list) and len(data_list) > 0 else data_list
        
        rounds = {}
        
        for index, value in enumerate(raw_data["head"]):
                key = value["key"]
                if len(key) == 2 and key[0] == "R" and key[1].isnumeric():
                    rounds.update({key: index})
                
                elif key == "name":
                    name_index = index
                    
        speaks = {}
        
        for row in raw_data["data"]:
            if row[name_index]["text"] == name:
                for key, value in rounds.items():
                    round_speaks = row[value]["text"]
                    speaks.update({key: round_speaks})                    

        return speaks
    
    def __get_points(self, team_name):

        new_path = self.path + "tab/team/"
        soup = self.__get_soup(new_path)
        data_list = self.__extract_vue_data(soup)
        raw_data = data_list[0] if isinstance(data_list, list) and len(data_list) > 0 else data_list
        
        rounds = {}
        
        for index, value in enumerate(raw_data["head"]):
                key = value["key"]
                if len(key) == 2 and key[0] == "R" and key[1].isnumeric():
                    rounds.update({key: index})
                
                elif key == "team":
                    name_index = index
                    
        points = {}
        point_values = {"1st":3, "2nd":2, "3rd":1, "4th": 0}
        
        for row in raw_data["data"]:
            if row[name_index]["text"] == team_name:
                for key, value in rounds.items():
                    round_points = row[value]["text"]
                    points.update({key: point_values[round_points]})

        return points
    
    def __get_round_results(self, path, team_name, name):
        soup = self.__get_soup(path)
        data_list = self.__extract_vue_data(soup)
        raw_data = data_list[0] if isinstance(data_list, list) and len(data_list) > 0 else data_list
        
        ballot_index = None
        
        for index, value in enumerate(raw_data["head"]):
            if value["key"] == "team":
                team_index = index
                
            elif value["key"] == "side":
                side_index = index
                
            elif value["key"] == "ballot":
                ballot_index = index
        
        positions = {
            "Opening Government": "OG",
            "Opening Opposition": "OO",
            "Closing Government": "CG",
            "Closing Opposition": "CO",
            }
        
        for row in raw_data["data"]:
                        
            if row[team_index]["text"] == team_name:

                position_name = row[side_index]["text"]
                position = positions[position_name]
                
                speaker_position = None
                
                if ballot_index != None:

                    ballot_path = row[ballot_index]["link"]
                    number = ballot_path.split("/")[-3]
                    full_path = self.path + f"results/debate/{number}/scoresheets/"
                    
                    soup = self.__get_soup(full_path)
                    
                    team_data_branchs = soup.find_all("div", {"class": "col-6 list-group mb-3"})
                    for team in team_data_branchs:

                        speakers_and_team = team.find_all("li", {"class": "list-group-item"})
                        speakers = speakers_and_team[:2]
                        
                        for speaker in speakers:
                            contents = speaker.contents
                            name_tab = contents[2].strip()
                            
                            if name_tab == name:
                                speaker_position = contents[1].text.strip()                    

        return position, speaker_position
    
    def __get_motions(self):
    
        new_path = self.path + "motions/statistics/"
        soup = self.__get_soup(new_path)
        
        rounds = soup.find_all('div', {'class': 'list-group mt-3'})
        
        motions = {}
                
        for round_ in rounds:
            
            round_name = round_.find('span', {'class': "badge badge-secondary"}).text
            
            if re.match("Round \d+", round_name):
                
                round_number = round_name[6:]
                motion = round_.find('h4').contents[0].text.strip()
                info_slide = round_.find('div', {'class': 'modal-body lead'})
                
                if info_slide:
                    info_slide = info_slide.text.strip()
            
            motions.update({f"R{round_number}": {"motion": motion,
                                            "info_slide": info_slide}
                            })
        
        return motions
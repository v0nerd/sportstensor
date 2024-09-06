import requests
import json
import http.client


class MonkAPI:
    def __init__(self, fixture_id):
        self.url = f"http://api.sportmonks.com/v3/football/predictions/probabilities/fixtures/{fixture_id}"
        
    def get_predictions(self):
        response = requests.get(self.url)
        if response.status_code == 200:
            return json.loads(response.text)
        return None

    def get_prediction_by_fixture(self, matchId):
        response = requests.get(f"{self.url}/{matchId}")
        if response.status_code == 200:
            return json.loads(response.text)
        return None

    def get_prediction_by_team(self, hometeam, awayteam):
        response = requests.get(f"{self.url}/team/{teamId}")
        if response.status_code == 200:
            return json.loads(response.text)
        return None

    def anaylze_prediction(self, prediction):
        # Analyze the prediction
        # For example, we can check if the prediction is correct
        predictions = self.get_predictions()
        for pred in predictions:
            if pred.get("id") == 127:
                home_team_score = pred.get("home_team_score")
                away_team_score = pred.get("away_team_score")


def get_latest_matches():
    # Get the latest matches
    url = "api.sportstensor.com"
    conn = http.client.HTTPSConnection(url)
    payload = ''
    headers = {}
    fixture_id = 19144684
    conn.request("GET", f"/matches", payload, headers)
    res = conn.getresponse()
    data = res.read()
    data = json.loads(data)
    # print(data)

    return data["matches"]


def get_team_id(team_name):
    conn = http.client.HTTPSConnection("api.sportmonks.com")
    payload = ''
    headers = {}
    conn.request("GET", f"/v3/football/teams/search/{team_name}?api_token=ptc81XCWgT5Fin9qz2hvGTQbKYZDKXeU0VCMZYsf2niY54Qfiu73QUkB88TB", payload, headers)
    res = conn.getresponse()
    data = res.read()
    data = json.loads(data)
    
    return data['data'][0]['id']


def get_fixture_by_date_range(start_date, end_date, home_team, away_team):
    home_team_id = get_team_id(home_team)

    conn = http.client.HTTPSConnection("api.sportmonks.com")
    payload = ''
    headers = {}
    conn.request("GET", f"/v3/football/fixtures/between/{start_date}/{end_date}/{home_team_id}?api_token=ptc81XCWgT5Fin9qz2hvGTQbKYZDKXeU0VCMZYsf2niY54Qfiu73QUkB88TB&include=participants", payload, headers)
    res = conn.getresponse()
    data = res.read()
    data = json.loads(data)
    fixtures = data['data']
    
    for fixture in fixtures:
        participants = fixture['participants']
        if participants[1]['name'] == away_team:
            return fixture


def get_predictions_by_fixture_id(fixture_id):
    conn = http.client.HTTPSConnection("api.sportmonks.com")
    payload = ''
    headers = {}
    conn.request("GET", f"/v3/football/predictions/probabilities/fixtures/{fixture_id}?api_token=ptc81XCWgT5Fin9qz2hvGTQbKYZDKXeU0VCMZYsf2niY54Qfiu73QUkB88TB&include=type&per_page=50", payload, headers)
    res = conn.getresponse()
    data = res.read()
    data = json.loads(data)

    return data["data"]


if __name__ == "__main__":
    home_team = None
    away_team = None

    matches = get_latest_matches()
    print([match for match in matches if match["matchDate"] >= "2024-09-05"])
    exit()

    for match in matches:
        if match["matchDate"] >= "2024-09-03" and match["sport"] == 1 and match["matchLeague"] != "American Major League Soccer":
            home_team = match["homeTeamName"]
            away_team = match["awayTeamName"]

    if home_team is None or away_team is None:
        print("No matches found")
        exit()

    fixture = get_fixture_by_date_range("2024-09-01", "2024-09-30", home_team, away_team)
    print(fixture)

    predictions = get_predictions_by_fixture_id(fixture['id'])

    for pred in predictions:
        print(f"{pred['id']}: {pred['type']['name']}: {pred['predictions']}")

    # matches = get_latest_match()
    # print(matches)

    # for match in matches:
    #     if match["matchDate"] >= "2024-09-01" and match["sport"] == 1:
    #         print(match)
    
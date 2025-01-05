#1 Prepare past games data:
- 20 for mlb, nba games
- 5 mls, epl games (including 2 draw games)
- 3 nfl games

#2 Mock response data from miners
- inf(), nan
- negative values
- positive values, close to 0, close to 1
- bigger than 1
- python minimum and maximum values
- some special values calculated via formula(depending on the scoring function design)

#3 Extract the util methods from `scoring_utils.py`:
- calculate_edge
- compute_significance_score
- apply_gaussian_filter
- calculate_incentive_score
- calculate_clv
- find_closest_odds
- calculate_incentives_and_update_scores

here remove database operations and feed mock data

#4 Plot the results
- 2d, 3d if possible


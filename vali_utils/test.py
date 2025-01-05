import numpy as np
from scipy.optimize import minimize_scalar
import random

def y(closing_odds, prob):
    t = 1.0 # Controls the spread/width of the Gaussian curve outside the plateau region. Larger t means slower decay in the exponential term
    a = -2 # Controls the height of the plateau boundary. More negative a means lower plateau boundary
    b = 0.3 # Controls how quickly the plateau boundary changes with odds. Larger b means faster exponential decay in plateau width
    c = 3 # Minimum plateau width/boundary

    w = a * np.exp(-b * (closing_odds - 1)) + c
    diff = abs(closing_odds - 1/prob)

    # note that sigma^2 = odds now
    # plateaued curve. 
    exp_component = 1.0 if diff <= w else np.exp(-np.power(diff, 2) / (t*2*closing_odds))

    return exp_component*(closing_odds-1/prob)

def find_extrema(c):
    # Find minimum of y
    result_min = minimize_scalar(lambda x: y(c, x), bounds=(0, 1 / c), method='bounded')
    # Find maximum of y by minimizing the negative of y
    result_max = minimize_scalar(lambda x: -y(c, x), bounds=(1 / c, 1), method='bounded')

    min_y = result_min.fun
    max_y = -result_max.fun
    x_min = result_min.x
    x_max = result_max.x

    return (min_y, x_min), (max_y, x_max)

def random_50_50():
    number = random.randint(1, 99)  # Choose a random integer between 1 and 99
    return number > 50  # Return True if the number is greater than 50, else False

if __name__ == '__main__':
    closing_odds = 10
    prob = 0.13
    print(y(closing_odds, prob))

    (min_y, x_min), (max_y, x_max) = find_extrema(closing_odds)
    print(f"Minimum: {min_y} at {x_min}")
    print(f"Maximum: {max_y} at {x_max}")
    print()

    left = (1 / closing_odds) + (x_max - (1 / closing_odds)) / 2.0
    right = min(x_max + (1 - x_max) / 2.0, 0.89)
    print(random.randint(int(left*10000), int(right*10000)) / 10000)
    left = x_min
    right = x_min + (float(1 / closing_odds) - x_min) / 2.0
    if right - left <= 0.03:
        right = 1 / closing_odds
    print(random.randint(int(left*10000), int(right*10000)) / 10000)
    

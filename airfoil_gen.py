import numpy as np
import math
from typing import List, Union

def naca_airfoil_4digits(chord, m, p, t, pitch, sweep, n_points: int = 50):
    """
    Generate a NACA 4-digits airfoil.

    Parameters
    ----------
    number : int or str
        NACA 4-digit number.
    n_points : int
        Number of points to generate the airfoil. The default is ``200``.
        Number of points in the upper side of the airfoil.
        The total number of points is ``2 * n_points - 1``.

    Returns
    -------
    list[Point2D]
        List of points that define the airfoil.
    """

    # Check if the number is a string
    #if isinstance(number, str):
    #    number = int(number)

        # Calculate the NACA parameters
    #m = number // 1000 * 0.01
    #p = number // 100 % 10 * 0.1
    #t = number % 100 * 0.01


    # Generate the airfoil
    points = []
    xy1 = np.zeros((n_points,2))
    xy2 = np.zeros((n_points,2))

    for i in range(n_points):

        # Make it a exponential distribution so the points are more concentrated
        # near the leading edge
        x = (1 - np.cos(i / (n_points - 1) * np.pi)) / 2

        X_CEN = 0.25 # airfoil center at quarter chord

        # Check if it is a symmetric airfoil
        if p == 0 and m == 0:
            # Camber line is zero in this case
            yc = 0
            dyc_dx = 0
        else:
            # Compute the camber line
            if x < p:
                yc = m / p**2 * (2 * p * x - x**2)
                dyc_dx = 2 * m / p**2 * (p - x)
            else:
                yc = m / (1 - p) ** 2 * ((1 - 2 * p) + 2 * p * x - x**2)
                dyc_dx = 2 * m / (1 - p) ** 2 * (p - x)

        # Compute the thickness
        yt = 5 * t * (0.2969 * x**0.5
                      - 0.1260 * x
                      - 0.3516 * x**2
                      + 0.2843 * x**3
                      - 0.1015 * x**4)

        # Compute the angle
        theta = np.arctan(dyc_dx)

        # Compute the points (upper and lower side of the airfoil)
        xu = (X_CEN - (x - yt * np.sin(theta))) * chord + sweep
        yu = (yc + yt * np.cos(theta)) * chord
        xl = (X_CEN - (x + yt * np.sin(theta))) * chord + sweep
        yl = (yc - yt * np.cos(theta)) * chord

        points.append([xu* math.cos(pitch) - yu * math.sin(pitch), xu * math.sin(pitch) + yu * math.cos(pitch)])
        points.insert(0,[xl * math.cos(pitch) - yl * math.sin(pitch), xl * math.sin(pitch) + yl * math.cos(pitch)])

        # Remove the first point since it is repeated
        if i == 0:
            points.pop(0)

    
        

    return points
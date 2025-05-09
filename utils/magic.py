from math import floor
from random import choice

from utils.infinity_norm import symmetric_mod


# Implementation of a hint function (sigma_{0,1}(x)) from article A Simple Provably Secure Key Exchange Scheme
# Based on the Learning with Errors Problem.
def hint_function(x, b, q):
    x %= q  # make sure that x is in Z_q

    l_bound = - floor(q / 4) + b
    r_bound = floor(q / 4) + b

    return 1 if r_bound < x < (l_bound % q) else 0


# Implementation of a signal function (Cha(y)) from article A Simple Provably Secure Key Exchange Scheme
# Based on the Learning with Errors Problem.
def signal_function(y, q):
    y %= q  # make sure that y is in Z_q
    b = choice([0, 1])
    return hint_function(y, b, q)


# Implementation of a robust extractor (Mod_2(x, w)) from article A Simple Provably Secure Key Exchange Scheme
# Based on the Learning with Errors Problem.
def robust_extractor(x, w, q, v02):
    if not v02:  # v01
        x %= q  # make sure that x is in Z_q
        return int((x + w * (q - 1) / 2) % q) % 2
    x = symmetric_mod(x, q)  # v02
    return int(symmetric_mod(x + w * (q - 1) / 2, q)) % 2

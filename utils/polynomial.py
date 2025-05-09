from math import floor
from random import randint
from numpy.random import normal
from numpy import round
from utils.infinity_norm import symmetric_mod


# Generates random polynomial of degree (n-1) with coefficients in Z_q.
def generate_random_polynomial(n, q, v02):
    poly = [0 for _ in range(n)]
    for i in range(n):
        poly[i] = randint(0, q - 1)
        if v02:
            poly[i] = symmetric_mod(poly[i], q)
    return poly


# Creates polynomial representing constant c.
def generate_constant_polynomial(c, n):
    poly = [0] * n
    poly[0] = c  # constant term (x^0)
    return poly


# Creates polynomial of degree (N-1) with coefficients based on Discrete Gaussian distribution
# with mean 0 and standard deviation STD_DEV.
def generate_discrete_gaussian_polynomial(n, std_dev, q):  # SOURCE: CHAT GPT
    # Generate float samples from normal distribution
    samples = normal(loc=0, scale=std_dev, size=n)
    # Round to nearest integer to get discrete values
    discrete_samples = round(samples).astype(int)
    polynomial = discrete_samples.tolist()
    return [symmetric_mod(p, q) for p in polynomial]  # just to make sure that it is in [-(q-1)/2, (q-1)/2]


# Generates random coefficient close to coefficient i, that fulfills the condition from 3.2. and (i - j) % 2 == 0 holds.
# Starts from wide spectrum and gradually shrinks the interval around coefficient i.
def generate_correct_complementary_coefficient(i, q, v02):
    if v02:
        distance = min(int((q - 1) / 2) - i, abs(-int((q - 1) / 2) - i))
    else:
        distance = min(q-1-i, i)
    while True:
        #j = randint(i - distance, i + distance)
        j = randint(0, q - 1)  # JUST A TEST, this way maybe I will have better possibility coverage
        j %= q  # make sure that j is in Z_q
        if v02:
            j = symmetric_mod(j, q)  # make sure that j is in v02
        if (i - j) % 2 != 0:
            continue
        k = i - j
        #if infinity_norm(k, q) <= floor(q / 4) - 2:
        if abs(k) <= floor(q / 4) - 2:
            return j
        distance //= 2  # Decrease distance by half


# Creates polynomial f used for modulo operations.
# So polynomial x^n + 1, so [1, 0, ..., 0, 1] of length n+1.
def generate_modulo_polynomial(n):
    poly = [0] * (n + 1)
    poly[0] = 1  # constant term (x^0)
    poly[-1] = 1  # x^n term
    return poly

# SOURCE for everything following: https://cryptographycaffe.sandboxaq.com/posts/kyber-01/

# Adds two polynomials modulo q.
def add(a, b, q, v02):
    result = [0] * max(len(a), len(b))
    for i in range(max(len(a), len(b))):
        if i < len(a):
            result[i] += a[i]
        if i < len(b):
            result[i] += b[i]
        result[i] %= q
        if v02:
            result[i] = symmetric_mod(result[i], q)
    return result


# Inverts a polynomial modulo q.
def inv(a, q):
  return list(map(lambda x: -x % q, a))


# Subtracts polynomial b from polynomial a modulo q.
def sub(a, b, q, v02):
  return add(a, inv(b, q), q, v02)


# Multiply 2 polynomials, coefficients modulo q, polynomials modulo f.
def mul_simple(a, b, f, q, v02):
    tmp = [0] * (len(a) * 2 - 1)  # the product of two degree n polynomial cannot exceed 2n  # CORRECT

    # schoolbook multiplication
    for i in range(len(a)):
        # perform a_i * b
        for j in range(len(b)):
            tmp[i + j] += a[i] * b[j]

    # take polynomial modulo f, so modulo x^n + 1
    degree_f = len(f) - 1

    for i in range(degree_f, len(tmp)):
        tmp[i - degree_f] -= tmp[i]
        tmp[i] = 0

    # take coefficients modulo q
    tmp = list(map(lambda x: x % q, tmp))
    if v02:
        tmp = list(map(lambda x: symmetric_mod(x, q), tmp))
    return tmp[:degree_f]


if __name__ == '__main__':
    pass
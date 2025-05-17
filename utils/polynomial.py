from utils.infinity_norm import symmetric_mod


# Converts array of ints to its byte representation.
def poly_to_bytes(p):
    return b"".join(x.to_bytes(4, signed=True) for x in p)  # length 4 is sufficient for q = 1073479681 using the representation [-(q-1)/2, (q-1)/2]


# Creates polynomial representing constant c.
def generate_constant_polynomial(c, n):
    poly = [0] * n
    poly[0] = c  # constant term (x^0)
    return poly


# Creates polynomial f used for modulo operations.
# So polynomial x^n + 1, so [1, 0, ..., 0, 1] of length n+1.
def generate_modulo_polynomial(n):
    poly = [0] * (n + 1)
    poly[0] = 1  # constant term (x^0)
    poly[-1] = 1  # x^n term
    return poly

# SOURCE for everything following: https://cryptographycaffe.sandboxaq.com/posts/kyber-01/

# Adds two polynomials modulo q.
def add(a, b, q):
    result = [0] * max(len(a), len(b))
    for i in range(max(len(a), len(b))):
        if i < len(a):
            result[i] += a[i]
        if i < len(b):
            result[i] += b[i]
        result[i] = symmetric_mod(result[i], q)
    return result


# Inverts a polynomial modulo q.
def inv(a, q):
  return list(map(lambda x: -x % q, a))


# Subtracts polynomial b from polynomial a modulo q.
def sub(a, b, q):
  return add(a, inv(b, q), q)


# Multiply 2 polynomials, coefficients modulo q, polynomials modulo f.
def mul_simple(a, b, f, q):
    tmp = [0] * (len(a) * 2 - 1)  # the product of two degree n polynomial cannot exceed 2n

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

    tmp = list(map(lambda x: symmetric_mod(x, q), tmp))
    return tmp[:degree_f]

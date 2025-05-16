# Extracted (and slightly modified) needed functions from https://github.com/mjosaarinen/py-acvp-pqc/blob/main/fips203.py

from Crypto.Hash import SHAKE128, SHAKE256
from utils.infinity_norm import symmetric_mod
from secrets import token_bytes


def prf(eta, s, b):
    return SHAKE256.new(s + bytes([b])).read(64*eta)


#   Algorithm 4, BytesToBits(B)

def bytes_to_bits(b):
    l = len(b)
    a = bytearray(8*l)
    for i in range(0, 8*l, 8):
        x = b[i // 8]
        for j in range(8):
            a[i + j] = (x >> j) & 1
    return a


#   Algorithm 7, SampleNTT(B)

def sample_ntt(b, q, a, frm):
    xof = SHAKE128.new(b)
    j   = 0
    while j < 256:
        c   = xof.read(3)
        d1  = c[0] + 256*(c[1] % 16)
        d2  = (c[1] // 16) + 16*c[2]
        if d1 < q:
            a[frm + j] = symmetric_mod(d1, q)
            j += 1
        if d2 < q and j < 256:
            a[frm + j] = symmetric_mod(d2, q)
            j += 1


#   Algorithm 8, SamplePolyCBD_eta(B)

def sample_poly_cbd(eta, b, q, f, frm):
    b = bytes_to_bits(b)
    for i in range(256):
        x = sum(b[2*i*eta:(2*i + 1)*eta])
        y = sum(b[(2*i + 1)*eta:(2*i + 2)*eta])
        #f[i] = (x - y) % self.q
        f[frm + i] = symmetric_mod(x - y, q)
    return f


def create_one_uniform_poly(n, q):
    assert n == 1024
    result = [0] * n
    seed = token_bytes(33)
    for i in range(n // 256):
        sample_ntt(seed + bytes([i]), q, result, i * 256)
    return result


# We need polynomial of length 1024, so calls sample_poly_cbd more times (as in Kyber).
def create_one_cbd_poly(n, eta, seed, q):
    assert n == 1024
    result = [0]*n
    m = 0  # in Kyber it is n in this context.
    for i in range(n // 256):
        sample_poly_cbd(eta, prf(eta, seed, m), q, result, i * 256)
        m += 1
    return result
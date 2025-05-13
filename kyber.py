# Extracted (and slightly modified) needed functions from https://github.com/mjosaarinen/py-acvp-pqc/blob/main/fips203.py

from Crypto.Hash import SHAKE256
from utils.infinity_norm import symmetric_mod


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


#   Algorithm 8, SamplePolyCBD_eta(B)

def sample_poly_cbd(eta, b, q, f, frm):
    b = bytes_to_bits(b)
    for i in range(256):
        x = sum(b[2*i*eta:(2*i + 1)*eta])
        y = sum(b[(2*i + 1)*eta:(2*i + 2)*eta])
        #f[i] = (x - y) % self.q
        f[frm + i] = symmetric_mod(x - y, q)
    return f


# We need polynomial of length 1024, so calls sample_poly_cbd more times (as in Kyber).
def create_one_cbd_poly(n, eta, seed, q):
    assert n == 1024
    result = [0]*n
    m = 0  # in Kyber it is n in this context.
    for i in range(n // 256):
        sample_poly_cbd(eta, prf(eta, seed, m), q, result, i * 256)
        m += 1
    return result
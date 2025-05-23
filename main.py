# Simple implementation of P-Q SRP from 2017: https://eprint.iacr.org/2017/1196.pdf
# Representation of polynomials: x^0, ..., x^n. E.g. 5x^3 + 2x^2 + 1 = [1, 0, 2, 5]

# CHANGES compared to the 2017 article:
# 1.   Instead of Gaussian distribution, CBD is used. For shortest explanation possible, let me cite Kyber's documentation:
#      “Theoretic treatments of LWE-based encryption typically consider LWE with Gaussian noise,
#      either rounded Gaussian [71] or discrete Gaussian [21]. As a result, many early implementations
#      also sampled noise from a discrete Gaussian distribution, which turns out to be either fairly
#      inefficient (see, for example, [19]) or vulnerable to timing attacks (see, for example, [22, 68, 33]).”
#      SOURCE for ^^: https://csrc.nist.gov/Projects/post-quantum-cryptography/post-quantum-cryptography-standardization/round-3-submissions
#                     -> ZIP file -> ./NIST-PQ-Submission-Kyber-20201001/Supporting_Documentation/kyber.pdf
# (2.) Public polynomial a is generated using Kyber's algorithm 7 (SampleNTT(B)) - output is understood to be in normal, not NTT domain.
#      This is because it seems to be more efficient to run secrets.token_bytes(33) once + 4-times SHAKE128 VS. random generator
#      for all 1024 coefficients.


from Crypto.Hash import SHAKE128, SHA3_256
from secrets import token_bytes
from utils.polynomial import add, sub, mul_simple, generate_modulo_polynomial, \
    generate_constant_polynomial, poly_to_bytes
from utils.magic import signal_function, robust_extractor
from cryptography.hazmat.primitives import hashes
from utils.kyber import create_one_cbd_poly, create_one_uniform_poly

# Params based on Section 4.1
N = 1024
Q = 1073479681

ETA = 2

# THIS IS NOT HOW TO DO IT !!! THIS IS JUST FOR PROOF-OF-CONCEPT !!! THIS IS NOT HOW TO DO IT
I = "identity123"
PWD = "password123"
SALT = "salt123".encode()
# THIS IS NOT HOW TO DO IT !!! THIS IS JUST FOR PROOF-OF-CONCEPT !!! THIS IS NOT HOW TO DO IT


def create_seeds():
    # seed1 = SHA3-256(salt||SHA3-256(I||pwd))
    digest_inner = hashes.Hash(hashes.SHA3_256())
    digest_inner.update((I + PWD).encode())
    inner_hash = digest_inner.finalize()
    digest_outer = hashes.Hash(hashes.SHA3_256())
    digest_outer.update(SALT + inner_hash)
    seed1 = digest_outer.finalize()
    # seed2 = SHA3-256(seed1)
    digest = hashes.Hash(hashes.SHA3_256())
    digest.update(seed1)
    seed2 = digest.finalize()
    return seed1, seed2


# Phase 0 in the protocol - verifier creation.
def phase_0(a):
    # CLIENT: v = asv + 2ev
    modulo_polynomial = generate_modulo_polynomial(N)
    # seed1 = SHA3-256(salt||SHA3-256(I||pwd)); seed2 = SHA3-256(seed1)
    seed1, seed2 = create_seeds()
    sv = create_one_cbd_poly(N, ETA, seed1, Q)
    ev = create_one_cbd_poly(N, ETA, seed2, Q)
    a_sv = mul_simple(a, sv, modulo_polynomial, Q)
    two_ev = mul_simple(generate_constant_polynomial(2, N), ev, modulo_polynomial, Q)
    v = add(a_sv, two_ev, Q)
    return v


# Phase 1 in the protocol - shared secret creation.
def phase_1(a, vs):  # {u,v}s = u / verifier on server's side, {u,v}c = u / verifier on client's side
    modulo_polynomial = generate_modulo_polynomial(N)
    constant_two_polynomial = generate_constant_polynomial(2, N)
    # CLIENT: pi = as1 + 2e1
    s1_seed = token_bytes(32)
    e1_seed = token_bytes(32)
    s1 = create_one_cbd_poly(N, ETA, s1_seed, Q)
    e1 = create_one_cbd_poly(N, ETA, e1_seed, Q)
    a_s1 = mul_simple(a, s1, modulo_polynomial, Q)
    two_e1 = mul_simple(constant_two_polynomial, e1, modulo_polynomial, Q)
    pi = add(a_s1, two_e1, Q)
    # SERVER: pj = as1' + 2e1' + v
    s1_prime_seed = token_bytes(32)
    e1_prime_seed = token_bytes(32)
    s1_prime = create_one_cbd_poly(N, ETA, s1_prime_seed, Q)
    e1_prime = create_one_cbd_poly(N, ETA, e1_prime_seed, Q)
    a_s1prime = mul_simple(a, s1_prime, modulo_polynomial, Q)
    two_e1prime = mul_simple(constant_two_polynomial, e1_prime, modulo_polynomial, Q)
    added_fst_two = add(a_s1prime, two_e1prime, Q)
    pj = add(added_fst_two, vs, Q)
    # SERVER: u = XOF(H(pi||pj))
    us = SHAKE128.new(SHA3_256.new(poly_to_bytes(pi + pj)).digest()).read(N)
    # SERVER: kj = (v + pi)s1' + uv + 2e1'''
    e1_tripleprime_seed = token_bytes(32)
    e1_tripleprime = create_one_cbd_poly(N, ETA, e1_tripleprime_seed, Q)
    bracket = add(vs, pi, Q)
    fst_multi = mul_simple(bracket, s1_prime, modulo_polynomial, Q)
    snd_multi = mul_simple(us, vs, modulo_polynomial, Q)
    trd_multi = mul_simple(constant_two_polynomial, e1_tripleprime, modulo_polynomial, Q)
    added_fst_two = add(fst_multi, snd_multi, Q)
    kj = add(added_fst_two, trd_multi, Q)
    # SERVER: wj = Cha(kj)
    wj = [signal_function(x, Q) for x in kj]
    # SERVER: sigmaj = Mod_2(kj, wj)
    sigmaj = [robust_extractor(k, w, Q) for k, w in zip(kj, wj)]
    # SERVER: skj = SHA3-256(sigmaj)
    skj = SHA3_256.new(bytes(sigmaj)).digest()
    # CLIENT: u = XOF(H(pi||pj))
    uc = SHAKE128.new(SHA3_256.new(poly_to_bytes(pi + pj)).digest()).read(N)
    # CLIENT: v = asv + 2ev
    seed1, seed2 = create_seeds()
    sv = create_one_cbd_poly(N, ETA, seed1, Q)
    ev = create_one_cbd_poly(N, ETA, seed2, Q)
    a_sv = mul_simple(a, sv, modulo_polynomial, Q)
    two_ev = mul_simple(generate_constant_polynomial(2, N), ev, modulo_polynomial, Q)
    vc = add(a_sv, two_ev, Q)
    # CLIENT ki = (pj − v)(sv + s1) + uv + 2e1''
    e1_doubleprime_seed = token_bytes(32)
    e1_doubleprime = create_one_cbd_poly(N, ETA, e1_doubleprime_seed, Q)
    fst_bracket = sub(pj, vc, Q)
    snd_bracket = add(sv, s1, Q)
    fst_multi = mul_simple(fst_bracket, snd_bracket, modulo_polynomial, Q)
    snd_multi = mul_simple(uc, vc, modulo_polynomial, Q)
    trd_multi = mul_simple(constant_two_polynomial, e1_doubleprime, modulo_polynomial, Q)
    added_fst_two = add(fst_multi, snd_multi, Q)
    ki = add(added_fst_two, trd_multi, Q)
    # CLIENT: sigmai = Mod_2(ki, wj)
    sigmai = [robust_extractor(k, w, Q) for k, w in zip(ki, wj)]
    # SERVER: ski = SHA3-256(sigmai)
    ski = SHA3_256.new(bytes(sigmai)).digest()
    return pi, pj, ski, skj


def phase_2(pi, pj, ski, skj):
    # CLIENT: M1 = SHA3-256(pi || pj || ski)
    m1 = SHA3_256.new(poly_to_bytes(pi + pj) + ski).digest()
    # SERVER: M1' = SHA3-256(pi || pj || skj)
    m1_prime = SHA3_256.new(poly_to_bytes(pi + pj) + skj).digest()
    # M1 = M1' => key exchange is successful and client is authenticated.
    print(f"M1 = M1\': {m1 == m1_prime}")
    # SERVER: M2' = SHA3-256(pi || M1' || skj) and sends to client.
    m2_prime = SHA3_256.new(poly_to_bytes(pi) + m1_prime + skj).digest()
    # CLIENT: M2 = SHA3-256(pi || M1 || ski).
    m2 = SHA3_256.new(poly_to_bytes(pi) + m1 + ski).digest()
    # M2 = M2' => key exchange is successful and mutual authentication is achieved.
    print(f"M2 = M2\': {m2 == m2_prime}")


def run_protocol():
    a = create_one_uniform_poly(N, Q)  # public parameter
    v = phase_0(a)
    pi, pj, ski, skj = phase_1(a, v)
    phase_2(pi, pj, ski, skj)


if __name__ == '__main__':
    run_protocol()

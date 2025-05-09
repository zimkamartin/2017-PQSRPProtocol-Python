# Simple implementation of P-Q SRP from 2017.
# Representation of polynomials: constant -> x^n. E.g. 5x^3 + 2x^2 + 1 = [1, 0, 2, 5]
# v02: if False, computations are in interval [0; q-1]. If true, computations are in interval [-(q-1)/2; (q-1)/2]
import math
import random
from utils.polynomial import add, sub, mul_simple, generate_modulo_polynomial, generate_random_polynomial, \
    generate_correct_complementary_coefficient, generate_constant_polynomial, generate_discrete_gaussian_polynomial
from utils.infinity_norm import infinity_norm_iterable, symmetric_mod
from utils.magic import signal_function, robust_extractor, hint_function

# Params based on Section 4.1
N = 1024
Q = 1073479681
STD_DEV = 3.192


# Checks error tolerance in article from 2017.
# So check that infinity norm of an iterable is <= smth.
def check_error_tolerance_iterable(iterable):
    return infinity_norm_iterable(iterable, Q) <= (math.floor(Q / 4) - 2)


# Makes sure that both elements have the same parity.
def check_parity(s):
    return all((a - b) % 2 == 0 for a, b in s)


# Name says it all.
def check_all_tuples_in_zq(s):
    return all(0 <= a <= Q - 1 and 0 <= b <= Q - 1 for a, b in s)


# Tests how many outputs are the same (they should be).
# Extracts k_i, k_j, computes Cha, Mod_2.
def test_set_of_tuples(s):
    num_of_correct_ones = 0

    for t in s:
        k_i, k_j = t[0], t[1]
        w_j = signal_function(k_j, Q)
        sigma_j = robust_extractor(k_j, w_j, Q, False)
        sigma_i = robust_extractor(k_i, w_j, Q, False)

        num_of_correct_ones += 1 if sigma_j == sigma_i else 0

    print(num_of_correct_ones)


# Name says it all.
def generate_n_possible_tuples(n, v02):
    result = set()

    while len(result) < n:
        a = random.randint(0, Q - 1)
        if v02:
            a = symmetric_mod(a, Q)
        b = generate_correct_complementary_coefficient(a, Q, v02)
        result.add((a, b))
    return result


# Check all conditions and call test_set_of_tuples.
def test_n_tuples(n):
    set_of_possible_tuples = generate_n_possible_tuples(n, False)
    if not check_all_tuples_in_zq(set_of_possible_tuples):
        print("Not all tuples are in Z_q. Exiting ...")
    if not check_parity(set_of_possible_tuples):
        print("Not all differences are odd or even. Exiting ...")
    if not check_error_tolerance_iterable([(a - b) % Q for a, b in set_of_possible_tuples]):
        print("Coefficients were not generated according to the error tolerance. Exiting ...")

    test_set_of_tuples(set_of_possible_tuples)


# Computes sigmas from k_i, k_j, b and based on the results divides triples to triples with same result and triples with different result.
def compute_sigmas_separate_triples(triples, v02):
    correct_triples = set()
    incorrect_triples = set()

    for t in triples:
        k_i, k_j, b = t[0], t[1], t[2]
        w_j = hint_function(k_j, b, Q)
        sigma_i = robust_extractor(k_i, w_j, Q, v02)
        sigma_j = robust_extractor(k_j, w_j, Q, v02)

        if sigma_j == sigma_i:
            correct_triples.add((k_i, k_j, b))
        else:
            incorrect_triples.add((k_i, k_j, b))

    print(f"There is {len(correct_triples)} correct triples. That is {len(correct_triples) * 100 / len(triples)} percent.")
    print(f"There is {len(incorrect_triples)} incorrect triples. That is {len(incorrect_triples) * 100 / len(triples)} percent.")


# Tests how many outputs are the same (they should be).
def test_n_triples(n, v02):
    tuples = generate_n_possible_tuples(n, v02)
    print("Tuples generated.")
    triples = {(a, b, x) for a, b in tuples for x in (0, 1)}  # To every tuple adds 0 and add 1, representing index b.

    compute_sigmas_separate_triples(triples, v02)


# Tests whether condition created by me works.
# Generates n possible tuples, adds b, filters them based on my condition, computes k, Cha, Mod_2 and number of same outputs.
def test_created_condition(n):
    tuples = generate_n_possible_tuples(n, False)
    tuples_b = {(a, b, x) for a, b in tuples for x in (0, 1)}
    print(f"GENERATED {len(tuples_b)} possible triples.")
    filtered = set()
    h = int(Q - 1 - (Q - 1) / 2)
    for t in tuples_b:
        k_i, k_j, b = t[0], t[1], t[2]
        w_j = hint_function(k_j, b, Q)
        if w_j == 1 and ((k_i <= h and k_j > h) or (k_j <= h and k_i > h)):
            print("WRONG: ", k_i, k_j, b)
            continue
        filtered.add((k_i, k_j, b))

    print(f"After FILTERING there is {len(filtered)} possible triples.")

    compute_sigmas_separate_triples(filtered)


# Phase 0 in the protocol - verifier creation.
def phase_0(a, v02):
    # CLIENT: v = asv + 2ev
    modulo_polynomial = generate_modulo_polynomial(N)
    sv = generate_discrete_gaussian_polynomial(N, STD_DEV, Q)  # TODO for future: use seed1
    ev = generate_discrete_gaussian_polynomial(N, STD_DEV, Q)  # TODO for future: use seed2
    a_sv = mul_simple(a, sv, modulo_polynomial, Q, v02)
    two_ev = mul_simple(generate_constant_polynomial(2, N), ev, modulo_polynomial, Q, v02)
    v = add(a_sv, two_ev, Q, v02)
    return v, sv  # Returning sv just for debugging reasons - In phase1 client should generate new, not use the old one.


# Prints both sigmas and compute statistics on how many bits they agree.
def compare_sigmas(si, sj):
    #print("Client's side: ", si)
    #print("Server's side: ", sj)
    assert len(si) == len(sj)
    num_of_correct_ones = 0
    for i in range(len(si)):
        num_of_correct_ones += 1 if si[i] == sj[i] else 0
    print(f"Sigmas agreed on {num_of_correct_ones} number of bits out of {len(si)} number of bits. That is {num_of_correct_ones * 100 / len(si)} percent.")


# Checks how many tuples (also with positions) of ki and kj have the same parity, correct error tolerance,
# how many tuples (again with positions) fulfill my condition.
# Lastly checks how many of those (without and with my condition) generate the same output.
def compare_ki_kj(ki, kj, si, sj):  # TODO: maybe do better statistics?
    ok_parity = []
    ok_error_tolerance = []
    assert len(ki) == len(kj) == len(si) == len(sj)
    for i in range(len(si)):
        parity = (ki[i] - kj[i]) % 2 == 0  # they have the same parity
        #error_tolerance = infinity_norm(ki[i] - kj[i], Q) <= math.floor(Q / 4) - 2
        error_tolerance = abs(ki[i] - kj[i]) <= math.floor(Q / 4) - 2
        if parity:
            ok_parity.append(i)
        if error_tolerance:
            ok_error_tolerance.append(i)
    #print(ok_parity)
    #print(f"Number of elements with same parity: {len(ok_parity)}. That is {len(ok_parity) * 100 / len(si)} percent.")
    #print(ok_error_tolerance)
    #print(f"Number of elements with correct error tolerance: {len(ok_error_tolerance)}. That is {len(ok_error_tolerance) * 100 / len(si)} percent.")


# Phase 1 in the protocol - shared secret creation.
def phase_1(a, vs, sv, v02):  # {u,v}s = u / verifier on server's side, {u,v}c = u / verifier on client's side
    modulo_polynomial = generate_modulo_polynomial(N)
    constant_two_polynomial = generate_constant_polynomial(2, N)
    # CLIENT: pi = as1 + 2e1
    s1 = generate_discrete_gaussian_polynomial(N, STD_DEV, Q)
    e1 = generate_discrete_gaussian_polynomial(N, STD_DEV, Q)
    a_s1 = mul_simple(a, s1, modulo_polynomial, Q, v02)
    two_e1 = mul_simple(constant_two_polynomial, e1, modulo_polynomial, Q, v02)
    pi = add(a_s1, two_e1, Q, v02)
    # SERVER: pj = as1' + 2e1' + v
    s1prime = generate_discrete_gaussian_polynomial(N, STD_DEV, Q)
    e1prime = generate_discrete_gaussian_polynomial(N, STD_DEV, Q)
    a_s1prime = mul_simple(a, s1prime, modulo_polynomial, Q, v02)
    two_e1prime = mul_simple(constant_two_polynomial, e1prime, modulo_polynomial, Q, v02)
    added_fst_two = add(a_s1prime, two_e1prime, Q, v02)
    pj = add(added_fst_two, vs, Q, v02)
    # SERVER: u = XOF(H(pi||pj))
    us = generate_random_polynomial(N, Q, v02)  # TODO for future: use XOF(H(pi||pj))
    # SERVER: kj = (v + pi)s1' + uv + 2e1'''
    e1_triple_prime = generate_discrete_gaussian_polynomial(N, STD_DEV, Q)
    bracket = add(vs, pi, Q, v02)
    fst_multi = mul_simple(bracket, s1prime, modulo_polynomial, Q, v02)
    snd_multi = mul_simple(us, vs, modulo_polynomial, Q, v02)
    trd_multi = mul_simple(constant_two_polynomial, e1_triple_prime, modulo_polynomial, Q, v02)
    added_fst_two = add(fst_multi, snd_multi, Q, v02)
    kj = add(added_fst_two, trd_multi, Q, v02)
    # SERVER: wj = Cha(kj)
    wj = [signal_function(x, Q) for x in kj]
    # SERVER: sigmaj = Mod_2(kj, wj)
    sigmaj = [robust_extractor(k, w, Q, v02) for k, w in zip(kj, wj)]
    # SERVER: skj = SHA3-256(sigmaj)  # TODO for future: implement it, now it is not useless
    # CLIENT: u = XOF(H(pi||pj))  # TODO for future: compute it again
    uc = us
    # CLIENT: v = asv + 2ev  # TODO for future: compute it again using seeds
    vc = vs
    # CLIENT ki = (pj − v)(sv + s1) + uv + 2e1''
    e1_double_prime = generate_discrete_gaussian_polynomial(N, STD_DEV, Q)
    fst_bracket = sub(pj, vc, Q, v02)
    snd_bracket = add(sv, s1, Q, v02)
    fst_multi = mul_simple(fst_bracket, snd_bracket, modulo_polynomial, Q, v02)
    snd_multi = mul_simple(uc, vc, modulo_polynomial, Q, v02)
    trd_multi = mul_simple(constant_two_polynomial, e1_double_prime, modulo_polynomial, Q, v02)
    added_fst_two = add(fst_multi, snd_multi, Q, v02)
    ki = add(added_fst_two, trd_multi, Q, v02)
    # CLIENT: sigmai = Mod_2(ki, wj)
    sigmai = [robust_extractor(k, w, Q, v02) for k, w in zip(ki, wj)]
    # SERVER: ski = SHA3-256(sigmai)  # TODO for future: implement it, now it is useless
    compare_sigmas(sigmai, sigmaj)  # Created just for debugging reasons.
    compare_ki_kj(ki, kj, sigmai, sigmaj)  # Created just for debugging reasons.


def phase_2():  # TODO for future: implement it, now it is useless
    pass


def run_protocol(v02):
    a = generate_random_polynomial(N, Q, v02)  # public parameter
    v, sv = phase_0(a, v02)
    phase_1(a, v, sv, v02)
    phase_2()


if __name__ == '__main__':
    # test_n_tuples(N)
    # test_created_condition(N)
    # run_protocol()
    # test_n_triples(N, False)

    run_protocol(True)

from optisolveapi.sat import CNF


def test_cardinality():
    for n in range(1, 10):
        for k in range(1, n + 5):
            print(n, k)
            C = CNF.new(solver="pysat/cadical")
            xs = [C.var() for _ in range(n)]
            card = C.Cardinality(xs, lim=k)
            nsol = 0
            for sol in C.solve_all():
                nsol += 1
                # print(sol, xs, card)
                vxs = C.sol_eval(sol, xs)
                vcard = C.sol_eval(sol, card)
                for i, vc in enumerate(vcard):
                    assert vc == (sum(vxs) >= i + 1)
            assert nsol == 2**n, nsol


def test_constraint_and():
    C = CNF.new(solver="pysat/cadical")
    a, b, ab = [C.var() for _ in range(3)]
    C.constraint_and(a, b, ab)
    nsol = 0
    for sol in C.solve_all():
        nsol += 1
        va, vb, vab = C.sol_eval(sol, [a, b, ab])
        assert vab == va & vb
    assert nsol == 4, nsol


def test_constraint_or():
    C = CNF.new(solver="pysat/cadical")
    a, b, ab = [C.var() for _ in range(3)]
    C.constraint_or(a, b, ab)
    nsol = 0
    for sol in C.solve_all():
        nsol += 1
        va, vb, vab = C.sol_eval(sol, [a, b, ab])
        assert vab == va | vb
    assert nsol == 4, nsol


if __name__ == '__main__':
    test_cardinality()

from propositionalcalculus.examples.proofs import valid_proofs


def pytest_addoption(parser):
    parser.addoption(
        "--repeat", action="store", help="Number of times to repeat each test"
    )


def pytest_generate_tests(metafunc):
    if metafunc.config.option.repeat:
        count = int(metafunc.config.option.repeat)
    else:
        count = 100

    if "random_formula" in metafunc.fixturenames:
        metafunc.fixturenames.append("tmp_ct")
        metafunc.parametrize("tmp_ct", range(count))

    if "valid_proof" in metafunc.fixturenames:
        metafunc.parametrize("valid_proof", valid_proofs)

    if "valid_proof_" in metafunc.fixturenames:
        metafunc.parametrize("valid_proof_", valid_proofs)

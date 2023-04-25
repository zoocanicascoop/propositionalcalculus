def pytest_addoption(parser):
    parser.addoption(
        "--repeat", action="store", help="Number of times to repeat each test"
    )


def pytest_generate_tests(metafunc):
    if metafunc.config.option.repeat:
        count = int(metafunc.config.option.repeat)
    else:
        count = 500
    if "random_formula" in metafunc.fixturenames:
        metafunc.fixturenames.append("tmp_ct")
        metafunc.parametrize("tmp_ct", range(count))

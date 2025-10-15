EPS = 1e-12


def assert_approx_equal(a: float, b: float, rtol: float = 1e-6) -> None:
    """Assert that two floating-point numbers are approximately equal."""
    if abs(a - b) / (abs(a) + EPS) > rtol:
        raise AssertionError(f"{a} and {b} differ by more than {rtol*100}%")

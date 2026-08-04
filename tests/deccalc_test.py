from _tools.deccalc import DecCalc

# The values from a real calibration (dec-cal.txt at fc8a2c8): the inclinometer
# was mounted so raw readings fall as dec rises. Non-uniform spacing matters —
# it catches a wrong segment being picked, which a linear table would not.
DESCENDING_X = [
    68.603, 60.448, 58.347, 55.463, 53.311, 51.224, 49.191, 47.359, 45.894,
    44.59, 42.324, 40.641, 38.921, 35.19, 33.45, 30.177, 28.19, 26.998,
    25.576, 23.723, 21.015, 18.716, 17.186, 13.65, 11.165, -7.255,
]


def load_calc(tmp_path, monkeypatch, x_values) -> DecCalc:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "dec-cal.txt").write_text("".join(f"{x}\n" for x in x_values))
    calc = DecCalc()
    calc.load_dec_cal()
    return calc


def test_descending_mount_round_trip(tmp_path, monkeypatch):
    calc = load_calc(tmp_path, monkeypatch, DESCENDING_X)
    for x, dec in zip(DESCENDING_X, DecCalc.get_dec_list()):
        assert abs(calc.calculate_declination(x) - dec) < 1e-9


def test_ascending_mount_round_trip(tmp_path, monkeypatch):
    ascending_x = list(reversed(DESCENDING_X))
    calc = load_calc(tmp_path, monkeypatch, ascending_x)
    for x, dec in zip(ascending_x, DecCalc.get_dec_list()):
        assert abs(calc.calculate_declination(x) - dec) < 1e-9


def test_interpolates_between_calibration_points(tmp_path, monkeypatch):
    calc = load_calc(tmp_path, monkeypatch, DESCENDING_X)
    decs = DecCalc.get_dec_list()
    for (x0, dec0), (x1, dec1) in zip(
        zip(DESCENDING_X, decs), zip(DESCENDING_X[1:], decs[1:])
    ):
        midpoint = (x0 + x1) / 2
        expected = (dec0 + dec1) / 2
        assert abs(calc.calculate_declination(midpoint) - expected) < 1e-9


def test_extrapolates_beyond_table_ends(tmp_path, monkeypatch):
    calc = load_calc(tmp_path, monkeypatch, DESCENDING_X)
    # Raw readings fall as dec rises, so beyond the low-x end is above 100 dec
    # and beyond the high-x end is below -25 dec.
    assert calc.calculate_declination(-10.0) > 100.0
    assert calc.calculate_declination(75.0) < -25.0

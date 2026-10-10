"""Presets: Vollständigkeit, gültige Werte, Einrasten der Permalink-Werte."""

import srm_constants as C
import srm_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP) == set(C.PRESET_ORDER)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds_and_on_the_grid():
    for preset in C.PRESETS.values():
        assert C.Z_MIN <= preset["z"] <= C.Z_MAX and preset["z"] in C.Z_GRID
        assert C.N_MIN <= preset["n"] <= C.N_MAX and (preset["n"] - C.N_MIN) % C.N_STEP == 0
        assert C.LOSS_MIN <= preset["loss"] <= C.LOSS_MAX
        assert 0 <= preset["mech"] < len(C.MECHANISMS)
        assert 0 <= preset["seed"] <= C.SEED_MAX


def test_mechanisms_have_label_and_help():
    assert set(C.MECH_LABELS) == set(C.MECH_HELP) == set(C.MECHANISMS)


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_permalink_values_are_clamped_and_snapped_to_the_slider_grid():
    z_spec = P.SETTING_SPECS["z_slider"]
    assert P.clamp_to_spec(z_spec, 1.47) == 1.5 and P.clamp_to_spec(z_spec, 9.0) == 2.0
    n_spec = P.SETTING_SPECS["n_slider"]
    assert P.clamp_to_spec(n_spec, 410) == 400 and P.clamp_to_spec(n_spec, 5) == 40 and P.clamp_to_spec(n_spec, 99999) == 2000
    loss_spec = P.SETTING_SPECS["loss_slider"]
    assert P.clamp_to_spec(loss_spec, -4) == 0 and P.clamp_to_spec(loss_spec, 50) == 20
    mech_spec = P.SETTING_SPECS["mech_radio"]
    assert P.clamp_to_spec(mech_spec, 7) == 3 and P.clamp_to_spec(mech_spec, -1) == 0

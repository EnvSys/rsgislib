import os

import pytest

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
IMGCALC_DATA_DIR = os.path.join(DATA_DIR, "imagecalc")


def test_countPxlsOfVal_band1():
    import rsgislib.imagecalc

    input_img = os.path.join(IMGCALC_DATA_DIR, "test_int_pxls.kea")
    val_counts = rsgislib.imagecalc.countPxlsOfVal(input_img, [1, 2, 3, 4], img_band=1)
    assert (
        (val_counts[0] == 614)
        and (val_counts[1] == 612)
        and (val_counts[2] == 618)
        and (val_counts[3] == 656)
    )


def test_countPxlsOfVal_band1_selVals():
    import rsgislib.imagecalc

    input_img = os.path.join(IMGCALC_DATA_DIR, "test_int_pxls.kea")
    val_counts = rsgislib.imagecalc.countPxlsOfVal(input_img, [2, 1], img_band=1)
    assert (val_counts[0] == 612) and (val_counts[1] == 614)


def test_countPxlsOfVal_all_bands():
    import rsgislib.imagecalc

    input_img = os.path.join(IMGCALC_DATA_DIR, "test_int_pxls.kea")
    val_counts = rsgislib.imagecalc.countPxlsOfVal(
        input_img, [1, 2, 3, 4], img_band=None
    )
    assert (
        (val_counts[0] == 1890)
        and (val_counts[1] == 1868)
        and (val_counts[2] == 1861)
        and (val_counts[3] == 1881)
    )


def test_getUniqueValues():
    import rsgislib.imagecalc

    input_img = os.path.join(IMGCALC_DATA_DIR, "test_int_pxls.kea")
    unq_vals = rsgislib.imagecalc.getUniqueValues(input_img, img_band=1)
    for val in [1, 2, 3, 4]:
        if val not in unq_vals:
            assert False
    assert True


def test_areImgsEqual_True():
    import rsgislib.imagecalc

    input_img = os.path.join(IMGCALC_DATA_DIR, "test_int_pxls.kea")
    img_eq, prop_match = rsgislib.imagecalc.areImgsEqual(input_img, input_img)
    assert img_eq


def test_areImgsEqual_False():
    import rsgislib.imagecalc

    in_ref_img = os.path.join(IMGCALC_DATA_DIR, "test_int_pxls.kea")
    in_cmp_img = os.path.join(IMGCALC_DATA_DIR, "test_int_pxls_v2.kea")
    img_eq, prop_match = rsgislib.imagecalc.areImgsEqual(in_ref_img, in_cmp_img)
    assert not img_eq


def test_areImgBandsEqual_True():
    import rsgislib.imagecalc

    input_img = os.path.join(IMGCALC_DATA_DIR, "test_int_pxls.kea")
    img_eq, prop_match = rsgislib.imagecalc.areImgBandsEqual(input_img, 1, input_img, 1)
    assert img_eq


def test_areImgBandsEqual_DifBands_False():
    import rsgislib.imagecalc

    input_img = os.path.join(IMGCALC_DATA_DIR, "test_int_pxls.kea")
    img_eq, prop_match = rsgislib.imagecalc.areImgBandsEqual(input_img, 1, input_img, 2)
    assert not img_eq


def test_areImgBandsEqual_False():
    import rsgislib.imagecalc

    in_ref_img = os.path.join(IMGCALC_DATA_DIR, "test_int_pxls.kea")
    in_cmp_img = os.path.join(IMGCALC_DATA_DIR, "test_int_pxls_v2.kea")
    img_eq, prop_match = rsgislib.imagecalc.areImgBandsEqual(
        in_ref_img, 1, in_cmp_img, 1
    )
    assert not img_eq


def test_BandMaths_SglBand(tmp_path):
    import rsgislib.imagecalc

    input_img = os.path.join(DATA_DIR, "sen2_20210527_aber.kea")
    band_def_seq = list()
    band_def_seq.append(
        rsgislib.imagecalc.BandDefn(band_name="Blue", input_img=input_img, img_band=1)
    )
    output_img = os.path.join(tmp_path, "sen2_20210527_aber_b1.kea")
    rsgislib.imagecalc.bandMath(
        output_img, "Blue", "KEA", rsgislib.TYPE_16UINT, band_defs=band_def_seq
    )

    img_eq, prop_match = rsgislib.imagecalc.areImgBandsEqual(
        input_img, 1, output_img, 1
    )
    assert img_eq


def test_BandMaths_MultiBand(tmp_path):
    import rsgislib.imagecalc

    input_img = os.path.join(DATA_DIR, "sen2_20210527_aber.kea")
    ref_ndvi_img = os.path.join(IMGCALC_DATA_DIR, "sen2_20210527_aber_ndvi.kea")
    band_def_seq = list()
    band_def_seq.append(
        rsgislib.imagecalc.BandDefn(band_name="red", input_img=input_img, img_band=3)
    )
    band_def_seq.append(
        rsgislib.imagecalc.BandDefn(band_name="nir", input_img=input_img, img_band=8)
    )
    output_img = os.path.join(tmp_path, "ndvi_test.kea")
    exp = "(nir-red)/(nir+red)"
    rsgislib.imagecalc.bandMath(
        output_img, exp, "KEA", rsgislib.TYPE_32FLOAT, band_defs=band_def_seq
    )

    img_eq, prop_match = rsgislib.imagecalc.areImgBandsEqual(
        ref_ndvi_img, 1, output_img, 1
    )
    assert img_eq


def test_BandMaths_BinaryOut(tmp_path):
    import rsgislib.imagecalc

    input_img = os.path.join(IMGCALC_DATA_DIR, "sen2_20210527_aber_ndvi.kea")
    ref_ndvi_cats_img = os.path.join(
        IMGCALC_DATA_DIR, "sen2_20210527_aber_ndvi_cats.kea"
    )
    band_def_seq = list()
    band_def_seq.append(
        rsgislib.imagecalc.BandDefn(band_name="ndvi", input_img=input_img, img_band=1)
    )
    output_img = os.path.join(tmp_path, "ndvi_cats_test.kea")
    exp = "ndvi>0.5?1:ndvi>0.75?2:0"
    rsgislib.imagecalc.bandMath(
        output_img, exp, "KEA", rsgislib.TYPE_32FLOAT, band_defs=band_def_seq
    )

    img_eq, prop_match = rsgislib.imagecalc.areImgBandsEqual(
        ref_ndvi_cats_img, 1, output_img, 1
    )
    assert img_eq


def test_BandMaths_ExpErr(tmp_path):
    import rsgislib.imagecalc

    input_img = os.path.join(IMGCALC_DATA_DIR, "sen2_20210527_aber_ndvi.kea")
    band_def_seq = list()
    band_def_seq.append(
        rsgislib.imagecalc.BandDefn(band_name="ndvi", input_img=input_img, img_band=1)
    )
    output_img = os.path.join(tmp_path, "ndvi_cats_test.kea")
    exp = "ndvi>0.5?1:ndvi>0.75?2:0?"
    with pytest.raises(Exception):
        rsgislib.imagecalc.bandMath(
            output_img, exp, "KEA", rsgislib.TYPE_32FLOAT, band_defs=band_def_seq
        )

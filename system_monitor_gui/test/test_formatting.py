from system_monitor_gui.formatting import format_stamp, human_bytes, human_rate


def test_human_bytes_units():
    assert human_bytes(0) == "0 B"
    assert human_bytes(1024) == "1.0 KiB"
    assert human_bytes(1536) == "1.5 KiB"
    assert human_bytes(1024 ** 3) == "1.0 GiB"


def test_human_bytes_invalid():
    assert human_bytes(None) == "n/a"
    assert human_bytes(-1) == "n/a"
    assert human_bytes("oops") == "n/a"


def test_human_rate():
    assert human_rate(2048) == "2.0 KiB/s"
    assert human_rate(None) == "n/a"


def test_format_stamp_is_stable_for_epoch():
    # Local timezone is intentionally not asserted; just make sure it formats.
    rendered = format_stamp(0, 0)
    assert len(rendered) == 19
    assert rendered[4] == "-" and rendered[7] == "-"
    assert rendered[10] == " " and rendered[13] == ":"

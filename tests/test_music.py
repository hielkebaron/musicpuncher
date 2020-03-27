import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from musicpuncher.music import *

C_MAJOR_SINGLE = [60, 62, 64, 65, 67, 69, 71, 72]


def test_calculate_transposition_finds_nearest_match():
    keyboard = Keyboard(C_MAJOR_SINGLE)

    noteseq = [DelayNotes(1, [61]), DelayNotes(1, [64, 65]), DelayNotes(1, [67])]
    result = autofit(noteseq, keyboard, transposition=3)

    # Oorspronkelijke sequece is ongewijzigd
    assert noteseq == [DelayNotes(1, [61]), DelayNotes(1, [64, 65]), DelayNotes(1, [67])]

    assert result == [DelayNotes(1, [64]), DelayNotes(1, [67]), DelayNotes(1, [])]


def test_consolidate():
    noteseq = [DelayNotes(1, [64]), DelayNotes(1, []), DelayNotes(1, [67])]

    result = consolidate(noteseq)

    # Oorspronkelijke sequece is ongewijzigd
    assert noteseq == [DelayNotes(1, [64]), DelayNotes(1, []), DelayNotes(1, [67])]

    assert result == [DelayNotes(1, [64]), DelayNotes(2, [67])]

import pytest

from keyboard import Keyboard

C_MAJOR_SINGLE = [60, 62, 64, 65, 67, 69, 71, 72]


def test_calculate_transposition_finds_nearest_match():
    keyboard = Keyboard(C_MAJOR_SINGLE)

    assert keyboard.calculate_transposition([57, 58]) == 7
    assert keyboard.calculate_transposition([58, 59]) == 6
    assert keyboard.calculate_transposition([59, 60]) == 5
    assert keyboard.calculate_transposition([60, 61]) == 4
    assert keyboard.calculate_transposition([61, 62]) == 3
    assert keyboard.calculate_transposition([62, 63]) == 2
    assert keyboard.calculate_transposition([63, 64]) == 1
    assert keyboard.calculate_transposition([64, 65]) == 0
    assert keyboard.calculate_transposition([65, 66]) == -1
    assert keyboard.calculate_transposition([66, 67]) == -2
    assert keyboard.calculate_transposition([67, 68]) == -3
    assert keyboard.calculate_transposition([68, 69]) == 3
    assert keyboard.calculate_transposition([69, 70]) == 2
    assert keyboard.calculate_transposition([70, 71]) == 1
    assert keyboard.calculate_transposition([71, 72]) == 0
    assert keyboard.calculate_transposition([72, 73]) == -1
    assert keyboard.calculate_transposition([73, 74]) == -2
    assert keyboard.calculate_transposition([74, 75]) == -3
    assert keyboard.calculate_transposition([75, 76]) == -4


def test_calculate_transposition_throws_exception_if_impossible():
    keyboard = Keyboard(C_MAJOR_SINGLE)

    with pytest.raises(RuntimeError):
        keyboard.calculate_transposition({60, 61, 62})

    with pytest.raises(RuntimeError):
        keyboard.calculate_transposition({60, 74})


def test_calculate_transposition_is_independent_on_keyboard_order():
    keyboard = Keyboard(reversed(C_MAJOR_SINGLE))

    assert keyboard.calculate_transposition([57, 58]) == 7
    assert keyboard.calculate_transposition([64, 65]) == 0
    assert keyboard.calculate_transposition([72, 73]) == -1
    assert keyboard.calculate_transposition([75, 76]) == -4


def test_get_index():
    keyboard = Keyboard(C_MAJOR_SINGLE)

    assert keyboard.get_index(60) == 0
    assert keyboard.get_index(62) == 1
    assert keyboard.get_index(71) == 6
    assert keyboard.get_index(72) == 7

    with pytest.raises(KeyError):
        keyboard.get_index(59)
    with pytest.raises(KeyError):
        keyboard.get_index(61)

def test_get_index_respects_keyboard_order():
    keyboard = Keyboard(reversed(C_MAJOR_SINGLE))

    assert keyboard.get_index(60) == 7
    assert keyboard.get_index(62) == 6
    assert keyboard.get_index(71) == 1
    assert keyboard.get_index(72) == 0

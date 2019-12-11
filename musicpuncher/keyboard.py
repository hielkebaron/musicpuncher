from typing import Set, Iterator


class Keyboard(object):
    def __init__(self, keyboard: Iterator[int]):
        self.keyboard = list(keyboard)
        self.indexed = {note: idx for idx, note in enumerate(self.keyboard)}

    def get_index(self, note: int) -> int:
        """Returns the index of the note in the keyboard array"""
        return self.indexed[note]

    def calculate_transposition(self, noteset: Set[int]) -> int:
        """
        Calculates the transposition needed for the notes to fit on the keyboard
        Throws an exception if it can not fit the notes
        """
        minimum = min(self.keyboard) - min(noteset)
        maximum = max(self.keyboard) - max(noteset)

        transposition = 0
        while -transposition >= minimum or transposition <= maximum:
            for signedTransposition in [transposition, -transposition]:
                if self.__fits(noteset, signedTransposition):
                    return signedTransposition
            transposition += 1
        raise RuntimeError(f"Cannot fit notes {noteset} on keyboard {self.keyboard}")

    def __fits(self, notes, transposition: int) -> bool:
        for note in notes:
            if not (note + transposition) in self.indexed:
                return False
        return True

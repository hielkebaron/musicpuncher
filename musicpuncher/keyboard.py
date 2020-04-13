import sys
from typing import Set, Iterator, Dict


class TransposeError(Exception):
    pass


class Keyboard(object):
    def __init__(self, keyboard: Iterator[int]):
        self.keyboard = list(keyboard)
        self.indexed = {note: idx for idx, note in enumerate(self.keyboard)}

    def size(self):
        return len(self.keyboard)

    def get_index(self, note: int) -> int:
        """Returns the index of the note in the keyboard array"""
        return self.indexed[note]

    def calculate_transposition(self, noteset: Set[int], best_effort=False) -> int:
        minimum = min(self.keyboard) - min(noteset) - 12
        maximum = max(self.keyboard) - max(noteset) + 12

        result = []
        for transposition in range(minimum, maximum + 1):
            unmapped = self.__get_unmapped_notes(noteset, transposition)
            result.append((transposition, unmapped))
        result.sort(key=lambda tp: len(tp[1]) * 100 + abs(tp[0]))

        if len(result) > 0 and len(result[0][1]) == 0:
            return result[0][0]

        if best_effort:
            return result[0][0]

        raise TransposeError(
            f"Cannot fit notes on keyboard. Try Autofit. Suggested transpositions: {[tp[0] for tp in result[:5]]}")

    def calculate_adjustments(self, noteset: Set[int]) -> Dict[int, int]:
        adjustments = dict()
        for note in noteset:
            adjustment = sys.maxsize
            for key in self.keyboard:
                diff = key - note
                if diff % 12 == 0 and abs(diff) < abs(adjustment):
                    adjustment = diff
            if adjustment == sys.maxsize:
                print(f"Can not fit note {note} on the keyboard, skipping!")
                adjustments[note] = sys.maxsize
            elif adjustment != 0:
                adjustments[note] = note + adjustment
        return adjustments

    def __get_unmapped_notes(self, notes, transposition: int) -> Set[int]:
        return {note for note in notes if not (note + transposition) in self.indexed}

    def does_fit(self, notes) -> bool:
        return len(self.__get_unmapped_notes(notes, 0)) == 0

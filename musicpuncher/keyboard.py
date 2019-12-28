from typing import Set, Iterator


class Keyboard(object):
    def __init__(self, keyboard: Iterator[int]):
        self.keyboard = list(keyboard)
        self.indexed = {note: idx for idx, note in enumerate(self.keyboard)}

    def size(self):
        return len(self.keyboard)

    def get_index(self, note: int) -> int:
        """Returns the index of the note in the keyboard array"""
        return self.indexed[note]

    def calculate_transposition(self, noteset: Set[int]) -> int:
        minimum = min(self.keyboard) - min(noteset) - 12
        maximum = max(self.keyboard) - max(noteset) + 12

        result = []
        for transposition in range(minimum, maximum + 1):
            unmapped = self.__get_unmapped_notes(noteset, transposition)
            result.append((transposition, unmapped))
        result.sort(key=lambda tp: len(tp[1]) * 100 + tp[0])

        if len(result) > 0 and len(result[0][1]) == 0:
            return result[0][0]

        bestfits = '\n'.join([f"{tp[0]}: {sorted(tp[1])}" for tp in result[:3]])
        raise RuntimeError(
            f"Cannot fit\nnotes       {sorted(noteset)}\non keyboard {sorted(self.keyboard)}.\nBest fits:\n{bestfits}")

    def __get_unmapped_notes(self, notes, transposition: int) -> Set[int]:
        return {note for note in notes if not (note + transposition) in self.indexed}

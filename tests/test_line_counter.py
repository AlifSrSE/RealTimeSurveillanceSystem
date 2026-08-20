import pytest
from line_counter import LineCounter

def test_line_counter_initial():
    counter = LineCounter(line_position=100)
    assert counter.count_in == 0
    assert counter.count_out == 0

def test_line_counter_crossing():
    counter = LineCounter(line_position=100)
    counter.update({1: (50, 90)})
    assert counter.count_in == 0
    assert counter.count_out == 0
    counter.update({1: (50, 110)})
    assert counter.count_in == 1
    assert counter.count_out == 0

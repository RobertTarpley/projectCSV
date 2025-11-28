# test_reader.py
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from reader import read_file

df = read_file("test_scripts/reader_scripts/test_reader3.xlsx")
print(df)

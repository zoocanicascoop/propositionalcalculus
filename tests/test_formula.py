import pytest
from liar.formula import Var

    
def test_var_str():
    vars = Var.generate(10, random=True)
    for v in vars:
        assert str(v) == v.value

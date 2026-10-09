"""Check that fallback mutation targets implementation dependencies, excluding unrelated fixtures and quoted names."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
from mutation_helpers_e12 import reachable_helpers


def test_transitive_implementation_helpers_only():
    source = '''namespace Demo
def inputFixture : Nat := 123
def leaf (n : Nat) : Nat := n + 1
def helper (n : Nat) : Nat := leaf n
def tested (n : Nat) : Nat := helper n
def unrelated : String := "inputFixture leaf"
end Demo
'''
    assert [d['full_name'] for d in reachable_helpers(source, [{'full_name': 'Demo.tested'}])] == ['Demo.leaf', 'Demo.helper']

import Mathlib
namespace Tiny
def solution (xs ys : List Int) : Bool := decide (xs.toFinset ⊆ ys.toFinset)
theorem spec_true_iff (xs ys : List Int) : solution xs ys = true ↔ xs.toFinset ⊆ ys.toFinset := by
  simp [solution]
theorem test_subset : solution [1, 1] [2, 1] = true := by decide
theorem test_not_subset : solution [1, 3] [1, 2] = false := by decide
end Tiny
#print axioms Tiny.spec_true_iff
#print axioms Tiny.test_subset
#print axioms Tiny.test_not_subset
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (-2)] [(3), (2), (1), (-3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (1), (4), (3)] [(-2), (2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (4), (3), (-3), (1), (-4)] [(-4), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (2), (-1), (2)] [(-2), (-2), (3), (-1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (-1), (-2), (-2), (4)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-4), (0), (0), (-4)] [(-4), (-2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (2), (2)] [(1), (3), (1), (-3), (1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3)] [(0), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-2), (2), (2), (-4)] [(4), (-1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (2), (2), (2)] [(-3), (4), (1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(-3), (3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (2), (3)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (2), (-4)] [(-1), (0), (3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (-4)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (-1), (1), (0), (2), (3)] [(1), (2), (3), (0), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (3), (-3), (-3), (2)] [(1), (-2), (2), (-2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (1), (-3), (-1)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-4)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(0), (-3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (-4), (4), (4), (-2)] [(2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (1), (3), (4), (3), (2)] [(4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2)] [(2), (0), (1), (-3), (3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4)] [(-2), (2), (4), (0), (-2), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (1), (2), (-3), (0)] [(-4), (-1), (2), (-3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (0), (3), (2), (-4)] [(3), (1), (0), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-3), (2)] [(0), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (2), (-4), (1), (0), (-4)] [(-3), (2), (1), (2), (1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (-3), (-1), (-4), (-4), (-2)] [(2), (3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (-4)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(-2), (-3), (2)])))

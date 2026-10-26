import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Bool := !(xs.count x == 0)
theorem spec_cons (x a : Int) (xs : List Int) :
    solution x (a :: xs) = if a = x then true else solution x xs := by
  by_cases h : a = x <;> simp [solution, h]
theorem test_present : solution 2 [1, 2] = true := by decide
theorem test_absent : solution 2 [1, 3] = false := by decide
end Tiny
#print axioms Tiny.spec_cons
#print axioms Tiny.test_present
#print axioms Tiny.test_absent
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-2), (1), (-3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-4), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(0), (-2), (-2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(-4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(-3), (0), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(-1), (-4), (-4), (1), (-3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(0), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-2), (1), (0), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-1), (2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(-4), (4), (1), (2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(1), (4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(-2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(0), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(3), (-3), (-1), (2), (1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(3), (1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(4), (0), (-1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(0), (4), (1), (0), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(1), (-1), (-1), (1), (1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(-3), (0), (4), (-1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [])))

import Mathlib
namespace Tiny
def solution (n : Nat) : List Int := (List.range n).map fun a => a * 2
theorem spec_length (n : Nat) : (solution n).length = n := by simp [solution]
theorem test_empty : solution 0 = [] := by decide
theorem test_four : solution 4 = [0, 2, 4, 6] := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1))))

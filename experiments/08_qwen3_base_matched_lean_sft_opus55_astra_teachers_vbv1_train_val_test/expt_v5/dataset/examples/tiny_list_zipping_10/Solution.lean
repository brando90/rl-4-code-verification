import Mathlib
namespace Tiny
def solution (xs ys : List Int) : List Int := (xs.zip ys).map Prod.snd
theorem spec_cons (a b : Int) (xs ys : List Int) : solution (a :: xs) (b :: ys) = b :: solution xs ys := rfl
theorem test_rights : solution [1] [3, 4] = [3] := by decide
theorem test_empty : solution [1] [] = [] := by decide
end Tiny

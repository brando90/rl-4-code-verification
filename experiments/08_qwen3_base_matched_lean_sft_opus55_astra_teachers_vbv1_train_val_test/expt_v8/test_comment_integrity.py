"""Exercise comment insertion against Lean lexical contexts and exact preservation of existing comments."""
import unittest

from comment_integrity import insert_comments


class CommentIntegrityTests(unittest.TestCase):
    def header(self):
        return [dict(before_line=1,text='Proof sketch: reduce the stated equality.'),
                dict(before_line=1,text='The unchanged reflexivity proof closes the goal.')]

    def test_preserves_existing_nested_and_line_comments(self):
        source='/- outer\n/- inner -/\nend -/\n-- keep this original line\nexample : 1 = 1 := by\n  rfl\n'
        result=insert_comments(source,self.header()+[dict(before_line=6,text='Reflexivity identifies the same numeral.')])
        self.assertTrue(result.endswith('  -- Reflexivity identifies the same numeral.\n  rfl\n'))
        self.assertIn('/- outer\n/- inner -/\nend -/\n-- keep this original line\n',result)

    def test_rejects_insertion_inside_nested_comment(self):
        with self.assertRaisesRegex(ValueError,'unsafe insertion'):
            insert_comments('/- block\ninside\n-/\n',self.header()+[dict(before_line=2,text='Would not be a Lean line comment here.')])

    def test_rejects_insertion_inside_multiline_string(self):
        with self.assertRaisesRegex(ValueError,'unsafe insertion'):
            insert_comments('def s := "first\nsecond"\n',self.header()+[dict(before_line=2,text='Would alter the string value.')])

    def test_rejects_control_characters_and_unicode_line_separators(self):
        for char in ('\n','\r','\x00','\u2028','\u2029'):
            with self.subTest(char=repr(char)),self.assertRaises(ValueError):
                insert_comments('example : True := trivial\n',self.header()+[dict(before_line=1,text='bad'+char+'text')])

    def test_requires_actual_top_sketch(self):
        with self.assertRaisesRegex(ValueError,'Proof sketch'):
            insert_comments('example : 1 = 1 := rfl\n',[dict(before_line=1,text='Just one generic line.')])

    def test_retains_original_bytes_with_no_final_newline(self):
        source='example : 1 = 1 := rfl'
        self.assertTrue(insert_comments(source,self.header()).endswith(source))

    def test_escaped_quote_does_not_end_string_context(self):
        source='def s := "quote: \\" and\nnext"\nexample : 1 = 1 := rfl\n'
        with self.assertRaisesRegex(ValueError,'unsafe insertion'):
            insert_comments(source,self.header()+[dict(before_line=2,text='Still inside string.')])


if __name__=='__main__':unittest.main()

"""Verify model-specific queue ownership and recovered result attribution without model calls or compilation."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import review_flagged as review


class ReviewRoutingTests(unittest.TestCase):
    def setup_case(self,root,name,state):
        folder=root/'cases'/name
        review.base.write(folder/'status.json',dict(state=state,attempts=0))
        return folder

    def test_sol_does_not_claim_routine_terra_cases(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            self.setup_case(root,'a_routine','TERRA_PENDING')
            wanted=self.setup_case(root,'b_ambiguous','ESCALATE_SOL')
            with patch.object(review,'ROOT',root),patch.object(review,'MODEL','gpt-6.1-sol'):
                self.assertEqual(review.claim(1),wanted)
            self.assertEqual(json.loads((root/'cases/a_routine/status.json').read_text())['state'],'TERRA_PENDING')

    def test_terra_does_not_claim_explicit_sol_escalation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            self.setup_case(root,'a_ambiguous','ESCALATE_SOL')
            wanted=self.setup_case(root,'b_routine','TERRA_PENDING')
            with patch.object(review,'ROOT',root),patch.object(review,'MODEL','gpt-5.6-terra'):
                self.assertEqual(review.claim(2),wanted)

    def test_recovery_uses_actual_recorded_model_for_attribution(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            review.base.write(folder/'input.json',dict(task_id='t'))
            review.base.write(folder/'status.json',dict(state='RUNNING',model='gpt-5.6-terra',effort='medium'))
            review.base.write(folder/'output.json',dict(task_id='t',decision='needs_sol',proof_index=-1,rationale='ambiguous statement',comments=[]))
            with patch.object(review,'MODEL','gpt-6.1-sol'):
                result=review.check_output(folder,folder/'output.json')
            self.assertEqual(result['review_model'],'gpt-5.6-terra')
            self.assertEqual(result['review_effort'],'medium')
            self.assertFalse(result['verified'])

    def test_native_route_receipt_overrides_missing_blocked_state_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            review.base.write(folder/'input.json',dict(task_id='t'))
            review.base.write(folder/'status.json',dict(state='BLOCKED'))
            review.base.write(folder/'route_1.json',dict(model='gpt-5.6-terra',effort='medium'))
            review.base.write(folder/'output_1.json',dict(task_id='t',decision='unresolved',proof_index=-1,rationale='bounded timeout',comments=[]))
            result=review.check_output(folder,folder/'output_1.json')
            self.assertEqual(result['review_model'],'gpt-5.6-terra')

    def verified_fixture(self,folder,receipt_hash=None):
        row=dict(task_id='t',formal_statement='theorem t : True := by sorry',all_proof_alternatives=['exact True.intro'])
        source=review.selection.assemble(row,row['all_proof_alternatives'][0])
        review.base.write(folder/'input.json',row)
        review.base.write(folder/'status.json',dict(state='RUNNING',model='gpt-5.6-terra',effort='medium'))
        review.base.write(folder/'checks/proof_00/result.json',dict(passed=True,source_sha256=receipt_hash or review.base.sha(source)))
        comments=[dict(before_line=1,text='Proof sketch: introduce the constructor of True.'),dict(before_line=1,text='The named constructor supplies a proof of the stated proposition.')]
        review.base.write(folder/'output_0.json',dict(task_id='t',decision='use_alternative',proof_index=0,rationale='supplied zero-index proof is valid',comments=comments))

    def test_label_normalization_does_not_change_selected_proof_or_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);self.verified_fixture(folder)
            original=json.loads((folder/'output_0.json').read_text())
            result=review.check_output(folder,folder/'output_0.json')
            self.assertEqual(result['decision'],'keep_original')
            self.assertEqual(result['model_decision_label'],'use_alternative')
            self.assertEqual(result['proof_index'],0)
            self.assertEqual(result['comments'],original['comments'])
            self.assertEqual(result['rationale'],original['rationale'])

    def test_pass_receipt_for_different_bytes_cannot_admit_selected_proof(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);self.verified_fixture(folder,receipt_hash='wrong source hash')
            with self.assertRaisesRegex(AssertionError,'different source bytes'):
                review.check_output(folder,folder/'output_0.json')


if __name__=='__main__':unittest.main()

"""Adapters that run open-weight policies on VeriBench tasks with experiment 103's single-call protocol.

The prompt, system prompt and Lean extraction rule are imported from the pinned VeriBench
checkout (experiment 103's `single_call.py`), never copied, so a baseline produced here stays
byte-comparable with experiment 103's table. Scoring is delegated to VeriBench's own scorer and
FSC judge; this package only writes their inputs and reads their outputs.
"""

# Adaptive 1.7B training toward25% validation binary success

**Doc link:** [protocol](PROTOCOL.md)

**TLDR:** Coordinate all-current training, parallel Terra proof cleanup, a cleaned-data continuation and validation-driven improvements. The latest user authorization permits up to $900 additional API spend and GX10 execution; [the prospective amendment](AMENDMENT_finish_cleanup_gx10.md) records the scope and historical phase boundaries.

[Runbook](cc.md) · [Live results](results.md) · [Checkpoint](CKPT_campaign.md)

Version12 owns both initial training pipelines; version13 owns teacher proof rewrites; version14 owns public-source preparation and the GX10 environment. This folder owns outcome-triggered adaptation and campaign monitoring. The current file has10,940 examples and13,168,888 assistant loss tokens.

`supervise.py` runs on skampere1 in a named persistent session. It calls Terra only on a new completed outcome or actual failed job, checks the full1080-cell target denominator, and preserves existing measurements and the sealed test split. Compact reports and per-row tables are mirrored into Git by the laptop publisher; raw models and outputs stay remote. Sessions survive disconnection; automatic node-reboot recovery is not configured.

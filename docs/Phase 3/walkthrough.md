## FINDING 1: DeepEval threshold=None Verification

Installed version: 4.1.8

Constructor result: FaithfulnessMetric(threshold=None, model=...) creates successfully without raising a validation error.

threshold attribute: None

is_successful() before measure(): None

Assessment: threshold=None is accepted syntactically by DeepEval 4.1.8 and initializes correctly.

OD #1 firewall guarantee: metric.success is explicitly overwritten with "PENDING_OD_1" regardless of DeepEval's internal computation. This is the primary firewall mechanism. threshold=None is belt-and-suspenders.

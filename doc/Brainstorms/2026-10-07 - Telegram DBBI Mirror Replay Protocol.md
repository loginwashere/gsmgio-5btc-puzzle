# Telegram DBBI mirror replay protocol

This is a small exploratory check of Flo Sku's messages 74731 and 75455,
written before calculating the mirror counts. It does not audit every
possible visual pattern or estimate the original discovery significance.

Freeze DBBI as seven rows of thirteen symbols, in native order. The pictured
horizontal mirror axes are zero-based rows 2 and 4, each comparing two pairs
of rows: 26 comparisons per axis. Count exact equal symbols in matching
columns. Include the middle eligible axis, row 3, in the comparison family.
Report all three counts and the sum of the two largest counts as a family
statistic. No partial selection of matching columns, alphabet substitution,
or variable mirror radius is allowed. Also report three-pair cyclic counts
for all seven centers to expose the effect of dropping edge rows.

Use 9,999 controls for each of three null models: a full same-multiset raw
shuffle, and a residual shuffle under each of DBBI's two exact prime-host
parses (83 and 84 logical tokens). The latter preserve every host token and
its width, while permuting only nonprime single-symbol tokens. Seeds are
202610070, 202610083 and 202610084. Recompute the complete three-axis family
for every control. Report add-one tail fractions, maxima and quantiles;
these are conditional exploratory diagnostics, not discovery p-values.

Independently check counts by explicit pair enumeration. A planted all-equal
matrix must score 26 at each axis; a seven-row constant-per-row matrix with
distinct rows must score zero. Verify histogram conservation and exact host
retention for both scaffold models. Compare the three centers' aligned
Stage-3.2.2 plaintext rows without modifying that plaintext.

Separately replay the exact 18 indices in message 75172 on the established
BTCSEED decode, with both zero- and one-based conventions. Keep complete
outputs. This is index extraction only; it does not select or validate an
intended consumer. No password oracle, new broad cipher sweep or address
search belongs to this protocol.

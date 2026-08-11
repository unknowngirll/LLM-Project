Splits fixed with seed=42 over the papers that have both a
gold record and an abstract on disk.

dev       267  evaluation set used throughout the project
heldout   400  reserved for final evaluation, never queried
pool      301  may be queried for k-nearest examples

The three sets are disjoint. All true negatives are currently in
dev, so heldout and pool contain positives only; curated negatives
will need adding before the held-out evaluation can measure
specificity.

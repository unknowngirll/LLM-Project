# bootstrap.R - confidence intervals for held-out performance, and paired
# comparison between models. Papers are the resampling unit, since a paper
# is the independent observation and the genes within it are not.
source("figures/scripts/setup.R")
set.seed(42)

# make_table.py writes only papers with a TP, FP or FN, so papers that were
# correctly rejected are absent. They are added back with zero counts, since
# they belong to the evaluation set and must be resampled with the rest.
ALL <- readLines("data/splits/final_eval_pmids.txt")
ALL <- ALL[nzchar(ALL)]

load_counts <- function(path) {
  d <- read_csv(path, show_col_types = FALSE) %>%
    group_by(PMID) %>%
    summarise(tp = n_distinct(gene_gold[row_type == "TP"]),
              fp = n_distinct(gene_LLM[row_type == "FP"]),
              fn = n_distinct(gene_gold[row_type == "FN"]),
              .groups = "drop")
  d$PMID <- as.character(d$PMID)
  missing <- setdiff(ALL, d$PMID)
  bind_rows(d, tibble(PMID = missing, tp = 0L, fp = 0L, fn = 0L))
}

f1 <- function(d) {
  tp <- sum(d$tp); fp <- sum(d$fp); fn <- sum(d$fn)
  2 * tp / (2 * tp + fp + fn)
}
prec <- function(d) { tp <- sum(d$tp); tp / (tp + sum(d$fp)) }
rec  <- function(d) { tp <- sum(d$tp); tp / (tp + sum(d$fn)) }

mag <- load_counts("figdata/heldout_magistral_table.csv")
qwn <- load_counts("figdata/heldout_qwen_table.csv")

B <- 5000

cat("\n=== Bootstrap confidence intervals, held-out set ===\n")
for (nm in c("Magistral-Small", "Qwen3-8B")) {
  d <- if (nm == "Magistral-Small") mag else qwn
  n <- nrow(d)
  boot <- replicate(B, {
    s <- d[sample(n, n, replace = TRUE), ]
    c(f1(s), prec(s), rec(s))
  })
  obs <- c(f1(d), prec(d), rec(d))
  for (i in seq_len(3)) {
    lab <- c("F1", "precision", "recall")[i]
    ci <- quantile(boot[i, ], c(0.025, 0.975), na.rm = TRUE)
    cat(sprintf("%-16s %-10s %.3f  95%% CI [%.3f, %.3f]\n",
                nm, lab, obs[i], ci[1], ci[2]))
  }
}

cat("\n=== Paired difference, Magistral minus Qwen ===\n")
papers <- intersect(mag$PMID, qwn$PMID)
m <- mag[match(papers, mag$PMID), ]
q <- qwn[match(papers, qwn$PMID), ]
n <- length(papers)

diffs <- replicate(B, {
  idx <- sample(n, n, replace = TRUE)
  c(f1(m[idx, ]) - f1(q[idx, ]),
    prec(m[idx, ]) - prec(q[idx, ]),
    rec(m[idx, ]) - rec(q[idx, ]))
})

obs <- c(f1(m) - f1(q), prec(m) - prec(q), rec(m) - rec(q))
for (i in seq_len(3)) {
  lab <- c("F1", "precision", "recall")[i]
  ci <- quantile(diffs[i, ], c(0.025, 0.975), na.rm = TRUE)
  p <- 2 * min(mean(diffs[i, ] <= 0), mean(diffs[i, ] >= 0))
  cat(sprintf("%-10s difference %+.3f  95%% CI [%+.3f, %+.3f]  p = %s\n",
              lab, obs[i], ci[1], ci[2],
              if (p < 1/B) sprintf("< %.4f", 1/B) else sprintf("%.4f", p)))
}

cat(sprintf("\n%d papers, %d bootstrap replicates\n", n, B))

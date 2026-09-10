# mcnemar.R - paired comparison of two models on the held-out set.
# Both models saw the same abstracts, so gene recovery is paired data
# and an unpaired test would overstate the uncertainty.
source("R/setup.R")

a <- read_csv("figdata/heldout_magistral_table.csv", show_col_types = FALSE)
b <- read_csv("figdata/heldout_qwen_table.csv", show_col_types = FALSE)

# a curated gene is either recovered by a model or not
recovered <- function(d) {
  d %>% filter(row_type %in% c("TP", "FN")) %>%
    group_by(key = paste(PMID, gene_gold)) %>%
    summarise(hit = any(row_type == "TP"), .groups = "drop")
}

ra <- recovered(a); rb <- recovered(b)
m <- full_join(ra, rb, by = "key", suffix = c("_mag", "_qwen"))
m$hit_mag[is.na(m$hit_mag)] <- FALSE
m$hit_qwen[is.na(m$hit_qwen)] <- FALSE

tab <- table(Magistral = m$hit_mag, Qwen = m$hit_qwen)
cat("\nCurated genes recovered, paired:\n")
print(tab)

cat(sprintf("\nboth: %d   Magistral only: %d   Qwen only: %d   neither: %d\n",
            tab["TRUE","TRUE"], tab["TRUE","FALSE"],
            tab["FALSE","TRUE"], tab["FALSE","FALSE"]))

mc <- mcnemar.test(tab, correct = TRUE)
cat(sprintf("\nMcNemar chi-square = %.2f, df = %d, p = %s\n",
            mc$statistic, mc$parameter, format.pval(mc$p.value, digits = 3)))

bt <- binom.test(tab["TRUE","FALSE"],
                 tab["TRUE","FALSE"] + tab["FALSE","TRUE"])
cat(sprintf("exact binomial on discordant pairs: p = %s\n",
            format.pval(bt$p.value, digits = 3)))

cat(sprintf("\nrecall: Magistral %.3f, Qwen %.3f\n",
            mean(m$hit_mag), mean(m$hit_qwen)))

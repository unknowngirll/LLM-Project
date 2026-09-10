# stats_replicates.R - formal tests on the replicate runs.
# Welch t-tests between models, and a one-way ANOVA across temperatures.
source("figures/scripts/setup.R")

rep <- read_csv("figdata/fig5b_replicates.csv", show_col_types = FALSE)

cat("\n=== Replicate summary ===\n")
rep %>%
  pivot_longer(c(F1, precision, recall), names_to = "metric",
               values_to = "value") %>%
  group_by(model, metric) %>%
  summarise(n = n(), mean = mean(value), sd = sd(value),
            .groups = "drop") %>%
  as.data.frame() %>% print(digits = 4)

cat("\n=== Welch two-sample t-tests, Magistral against Qwen ===\n")
res <- lapply(c("F1", "precision", "recall"), function(m) {
  a <- rep[[m]][rep$model == "Magistral-Small"]
  b <- rep[[m]][rep$model == "Qwen3-8B"]
  tt <- t.test(a, b)
  data.frame(metric = m,
             diff = round(mean(a) - mean(b), 4),
             ci_low = round(tt$conf.int[1], 4),
             ci_high = round(tt$conf.int[2], 4),
             t = round(unname(tt$statistic), 3),
             df = round(unname(tt$parameter), 2),
             p = signif(tt$p.value, 3))
})
print(do.call(rbind, res), row.names = FALSE)

tmp <- read_csv("figdata/fig5a_temperature.csv", show_col_types = FALSE)
tmp$temperature <- factor(tmp$temperature)

cat("\n=== One-way ANOVA, F1 against temperature ===\n")
fit <- aov(F1 ~ temperature, data = tmp)
print(summary(fit))

cat("\n=== Variance components ===\n")
s <- summary(fit)[[1]]
within_sd <- sqrt(s[["Mean Sq"]][2])
cat(sprintf("residual (seed-to-seed) SD: %.4f\n", within_sd))
cat(sprintf("spread of temperature means: %.4f\n",
            diff(range(tapply(tmp$F1, tmp$temperature, mean)))))

pooled <- sd(residuals(lm(F1 ~ model, data = rep)))
cat(sprintf("pooled run-to-run SD from replicates: %.4f\n", pooled))
cat(sprintf("two standard deviations: %.4f\n", 2 * pooled))
RSTATScd ~/LLM_Project && cat > R/stats_replicates.R << 'RSTATS'
# stats_replicates.R - formal tests on the replicate runs.
# Welch t-tests between models, and a one-way ANOVA across temperatures.
source("figures/scripts/setup.R")

rep <- read_csv("figdata/fig5b_replicates.csv", show_col_types = FALSE)

cat("\n=== Replicate summary ===\n")
rep %>%
  pivot_longer(c(F1, precision, recall), names_to = "metric",
               values_to = "value") %>%
  group_by(model, metric) %>%
  summarise(n = n(), mean = mean(value), sd = sd(value),
            .groups = "drop") %>%
  as.data.frame() %>% print(digits = 4)

cat("\n=== Welch two-sample t-tests, Magistral against Qwen ===\n")
res <- lapply(c("F1", "precision", "recall"), function(m) {
  a <- rep[[m]][rep$model == "Magistral-Small"]
  b <- rep[[m]][rep$model == "Qwen3-8B"]
  tt <- t.test(a, b)
  data.frame(metric = m,
             diff = round(mean(a) - mean(b), 4),
             ci_low = round(tt$conf.int[1], 4),
             ci_high = round(tt$conf.int[2], 4),
             t = round(unname(tt$statistic), 3),
             df = round(unname(tt$parameter), 2),
             p = signif(tt$p.value, 3))
})
print(do.call(rbind, res), row.names = FALSE)

tmp <- read_csv("figdata/fig5a_temperature.csv", show_col_types = FALSE)
tmp$temperature <- factor(tmp$temperature)

cat("\n=== One-way ANOVA, F1 against temperature ===\n")
fit <- aov(F1 ~ temperature, data = tmp)
print(summary(fit))

cat("\n=== Variance components ===\n")
s <- summary(fit)[[1]]
within_sd <- sqrt(s[["Mean Sq"]][2])
cat(sprintf("residual (seed-to-seed) SD: %.4f\n", within_sd))
cat(sprintf("spread of temperature means: %.4f\n",
            diff(range(tapply(tmp$F1, tmp$temperature, mean)))))

pooled <- sd(residuals(lm(F1 ~ model, data = rep)))
cat(sprintf("pooled run-to-run SD from replicates: %.4f\n", pooled))
cat(sprintf("two standard deviations: %.4f\n", 2 * pooled))

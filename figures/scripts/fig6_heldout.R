# fig6_heldout.R - development against held-out performance.
# The generalisation gap and its confinement to recall.
source("figures/scripts/setup.R")

SD <- 0.018   # run-to-run standard deviation, Figure 5B

d <- read_csv("figdata/fig6_heldout.csv", show_col_types = FALSE) %>%
  mutate(metric = factor(metric, levels = c("precision", "recall", "F1"),
                         labels = c("Precision", "Recall", "F1")),
         set = factor(set, levels = c("development", "held-out"),
                      labels = c("Development", "Held-out")),
         model = factor(model, levels = c("Magistral-Small", "Qwen3-8B",
                                          "Gemma-4-12B")))

p <- ggplot(d, aes(metric, value, fill = set)) +
  geom_col(position = position_dodge(width = 0.72), width = 0.62) +
  geom_text(aes(label = sprintf("%.3f", value)),
            position = position_dodge(width = 0.72),
            vjust = -0.45, size = 2.9, colour = "black") +
  facet_wrap(~ model) +
  scale_fill_manual(values = c("Development" = "#999999",
                               "Held-out" = "#009E73")) +
  scale_y_continuous(limits = c(0, 1), expand = expansion(mult = c(0, 0.08))) +
  labs(x = NULL, y = "Score") +
  theme_report() +
  theme(legend.position = "top")

save_fig(p, "fig6_heldout", width = 9, height = 4.2)

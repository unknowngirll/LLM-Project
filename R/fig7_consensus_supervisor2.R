source("R/setup.R")

# Panel A: Supervisor's Style (Grouped Bars WITHOUT Text Labels)
s <- read_csv("figdata/fig7_consensus_scores.csv", show_col_types = FALSE) %>%
  mutate(rule = fct_reorder(rule, F1)) %>%
  pivot_longer(c(precision, recall, F1),
               names_to = "metric", values_to = "value") %>%
  mutate(metric = factor(metric, levels = c("precision", "recall", "F1"),
                         labels = c("Precision", "Recall", "F1")))

a <- ggplot(s, aes(x = rule, y = value, fill = metric)) +
  geom_col(position = position_dodge(width = 0.8), width = 0.7) +
  scale_fill_manual(values = c("Precision" = "#1F77B4", 
                               "Recall"    = "#FF7F0E", 
                               "F1"        = "#2CA02C")) +
  scale_y_continuous(limits = c(0, 1), breaks = seq(0, 1, 0.2), 
                     expand = expansion(mult = c(0, 0.05))) +
  labs(x = NULL, y = "Score", tag = "A", fill = NULL) +
  theme_classic() +
  theme(
    legend.position = "top",
    text = element_text(size = 14),
    axis.text.x = element_text(angle = 45, hjust = 1, size = 11),
    axis.line = element_line(color = "black")
  )

# Panel B: Trend Line
l <- read_csv("figdata/fig7b_ladder.csv", show_col_types = FALSE) %>%
  filter(set == "held-out") %>%
  mutate(subset = fct_inorder(subset), pct = 100 * proportion)

b <- ggplot(l, aes(x = subset, y = pct, group = 1)) +
  geom_line(color = "#3B528B", linewidth = 1) +
  geom_point(color = "#21918C", size = 3.5) +
  geom_text(aes(label = sprintf("%.1f%%", pct)),
            vjust = -1.3, size = 3.5) +
  scale_y_continuous(limits = c(0, 120), breaks = seq(0, 100, 25), expand = c(0, 0)) +
  labs(x = "Number of Models in Agreement",
       y = "Matching Curated Data (%)", tag = "B") +
  theme_classic() +
  theme(
    text = element_text(size = 14),
    axis.text.x = element_text(angle = 45, hjust = 1, size = 11),
    axis.line = element_line(color = "black")
  )

p <- a / b + plot_layout(heights = c(1.15, 1))
save_fig(p, "fig7_consensus_supervisor2", width = 8.5, height = 9)

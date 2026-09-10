source("figures/scripts/setup.R")

# Panel A: Bar chart (Sorted by F1, Colorblind-friendly light palette)
s <- read_csv("figdata/fig7_consensus_scores.csv", show_col_types = FALSE) %>%
  mutate(rule = fct_reorder(rule, F1)) %>%
  pivot_longer(c(precision, recall, F1),
               names_to = "metric", values_to = "value") %>%
  mutate(metric = factor(metric, levels = c("precision", "recall", "F1"),
                         labels = c("Precision", "Recall", "F1")))

a <- ggplot(s, aes(rule, value, fill = metric)) +
  geom_col(position = position_dodge(width = 0.78), width = 0.7) +
  coord_flip() +
  scale_fill_manual(values = c("Precision" = "#56B4E9",  # Sky Blue (Light & Colorblind safe)
                               "Recall"    = "#E69F00",  # Orange (Colorblind safe)
                               "F1"        = "#009E73")) + # Bluish Green (Light & Colorblind safe)
  scale_y_continuous(limits = c(0, 1), expand = expansion(mult = c(0, 0.04))) +
  labs(x = NULL, y = "Score", tag = "A") +
  theme_report() +
  theme(legend.position = "top")

# Panel B: Trend Line for Agreement Reliability
l <- read_csv("figdata/fig7b_ladder.csv", show_col_types = FALSE) %>%
  filter(set == "held-out") %>%
  mutate(subset = fct_inorder(subset), pct = 100 * proportion)

b <- ggplot(l, aes(x = subset, y = pct, group = 1)) +
  geom_line(color = "#3B528B", linewidth = 1) +
  geom_point(color = "#21918C", size = 3) +
  geom_text(aes(label = sprintf("%.1f%%", pct)),
            vjust = -1.2, size = 3) +
  scale_y_continuous(limits = c(0, 115), breaks = seq(0, 100, 25)) +
  labs(x = "Number of Models in Agreement",
       y = "Matching Curated Data (%)", tag = "B") +
  theme_report() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))

p <- a / b + plot_layout(heights = c(1.15, 1))
save_fig(p, "fig7_consensus_final", width = 8.5, height = 9)

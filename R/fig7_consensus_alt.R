source("R/setup.R")

# Panel A: Precision-Recall Scatter Plot
s_wide <- read_csv("figdata/fig7_consensus_scores.csv", show_col_types = FALSE)

a <- ggplot(s_wide, aes(x = recall, y = precision, color = F1)) +
  geom_point(size = 3.5, alpha = 0.8) +
  geom_text(aes(label = rule), size = 3, vjust = -1, show.legend = FALSE) +
  scale_color_viridis_c(option = "mako", direction = -1) +
  scale_x_continuous(limits = c(0, 1)) +
  scale_y_continuous(limits = c(0, 1)) +
  labs(x = "Recall", y = "Precision", color = "F1 Score", tag = "A") +
  theme_report() +
  theme(legend.position = "right")

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

p <- a / b + plot_layout(heights = c(1.2, 1))
save_fig(p, "fig7_consensus_alt", width = 8.5, height = 9)

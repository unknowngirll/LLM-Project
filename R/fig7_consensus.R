# fig7_consensus.R - agreement rules and the reliability of agreement.
# Panel A: no rule beats the best single model. Panel B: agreement still
# predicts which individual calls are correct.
source("R/setup.R")

s <- read_csv("figdata/fig7_consensus_scores.csv", show_col_types = FALSE) %>%
  mutate(rule = fct_reorder(rule, F1)) %>%
  pivot_longer(c(precision, recall, F1),
               names_to = "metric", values_to = "value") %>%
  mutate(metric = factor(metric, levels = c("precision", "recall", "F1"),
                         labels = c("Precision", "Recall", "F1")))

a <- ggplot(s, aes(rule, value, fill = metric)) +
  geom_col(position = position_dodge(width = 0.78), width = 0.7) +
  coord_flip() +
  scale_fill_manual(values = c("Precision" = "#4E79A7",
                               "Recall" = "#F28E2B", 
                               "F1" = "#59A14F")) +
  scale_y_continuous(limits = c(0, 1), expand = expansion(mult = c(0, 0.04))) +
  labs(x = NULL, y = "Score", tag = "A") +
  theme_report() +
  theme(legend.position = "top")

l <- read_csv("figdata/fig7b_ladder.csv", show_col_types = FALSE) %>%
  filter(set == "held-out") %>%
  mutate(subset = fct_inorder(subset), pct = 100 * proportion)

b <- ggplot(l, aes(fct_rev(subset), pct)) +
  geom_col(fill = "#59A14F", width = 0.62) +
  geom_text(aes(label = sprintf("%.1f%%  (%d of %d)", pct, correct, genes)),
            hjust = -0.06, size = 4.2, colour = "black") +
  coord_flip() +
  scale_y_continuous(limits = c(0, 118),
                     breaks = seq(0, 100, 25),
                     expand = expansion(mult = c(0, 0))) +
  labs(x = "Models recovering the gene",
       y = "Extracted genes matching the curated data (%)", tag = "B") +
  theme_report()

p <- a / b + plot_layout(heights = c(1.15, 1))
save_fig(p, "fig7_consensus", width = 10, height = 10)

# fig2_normalisation.R - effect of gene symbol normalisation on prompt v1.
# Introduces the two leading models and the three metrics used throughout.
source("R/setup.R")

d <- read_csv("figdata/fig2_normalisation.csv", show_col_types = FALSE) %>%
  filter(mode == "reasoning") %>%
  mutate(
    metric = factor(metric, levels = c("precision", "recall", "F1"),
                    labels = c("Precision", "Recall", "F1")),
    normalisation = factor(normalisation, levels = c("raw", "HGNC"),
                           labels = c("Raw output", "After normalisation")),
    model = factor(model, levels = c("Magistral-Small", "Qwen3-8B"))
  )

p <- ggplot(d, aes(metric, value, fill = normalisation)) +
  geom_col(position = position_dodge(width = 0.72), width = 0.62) +
  geom_text(aes(label = sprintf("%.3f", value)),
            position = position_dodge(width = 0.72),
            vjust = -0.45, size = 3.1, colour = "black") +
  facet_wrap(~ model) +
  scale_fill_manual(values = c("Raw output" = "#999999",
                               "After normalisation" = "#0072B2")) +
  scale_y_continuous(limits = c(0, 1), expand = expansion(mult = c(0, 0.06))) +
  labs(x = NULL, y = "Score") +
  theme_report() +
  theme(legend.position = "top")

save_fig(p, "fig2_normalisation", width = 7.5, height = 4.2)

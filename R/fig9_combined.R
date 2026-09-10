source("R/setup.R")

# Panel A: Gene Level (از داده‌های fig6)
d_gene <- read_csv("figdata/fig6_heldout.csv", show_col_types = FALSE) %>%
  mutate(metric = factor(metric, levels = c("precision", "recall", "F1"),
                         labels = c("Precision", "Recall", "F1")),
         set = factor(set, levels = c("development", "held-out"),
                      labels = c("Development", "Held-out")),
         model = factor(model, levels = c("Magistral-Small", "Qwen3-8B",
                                          "Gemma-4-12B")))

a <- ggplot(d_gene, aes(metric, value, fill = set)) +
  geom_col(position = position_dodge(width = 0.72), width = 0.62) +
  geom_text(aes(label = sprintf("%.3f", value)),
            position = position_dodge(width = 0.72),
            vjust = -0.45, size = 2.9, colour = "black") +
  facet_wrap(~ model) +
  scale_fill_manual(values = c("Development" = "#999999",
                               "Held-out" = "#009E73")) +
  scale_y_continuous(limits = c(0, 1), expand = expansion(mult = c(0, 0.08))) +
  labs(x = NULL, y = "Score", tag = "A") +
  theme_report()

# Panel B: Attribute Level (از داده‌های fig8)
d_attr <- read_csv("figdata/attributes.csv", show_col_types = FALSE) %>%
  group_by(model, set, field) %>%
  summarise(accuracy = mean(accuracy), .groups = "drop") %>%
  mutate(field = factor(field, levels = c("species", "outcome", "induction"),
                        labels = c("Species", "Outcome", "Induction")),
         set = factor(set, levels = c("development", "held-out"),
                      labels = c("Development", "Held-out")),
         model = factor(model, levels = c("Magistral-Small", "Qwen3-8B",
                                          "Gemma-4-12B")))

b <- ggplot(d_attr, aes(field, accuracy, fill = set)) +
  geom_col(position = position_dodge(width = 0.72), width = 0.62) +
  geom_text(aes(label = sprintf("%.3f", accuracy)),
            position = position_dodge(width = 0.72),
            vjust = -0.45, size = 2.9, colour = "black") +
  facet_wrap(~ model) +
  scale_fill_manual(values = c("Development" = "#999999",
                               "Held-out" = "#009E73")) +
  scale_y_continuous(limits = c(0, 1), expand = expansion(mult = c(0, 0.08))) +
  labs(x = NULL, y = "Accuracy", tag = "B") +
  theme_report()

# ترکیب دو پنل و مشترک کردن راهنمای رنگ در بالا
p <- a / b + plot_layout(guides = 'collect') & theme(legend.position = 'top')
save_fig(p, "fig9_combined", width = 9, height = 8.5)

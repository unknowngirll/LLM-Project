# fig8_attributes.R - development against held-out performance for attributes.
# Shows the generalisation gap at the attribute extraction level.
source("figures/scripts/setup.R")

d <- read_csv("figdata/attributes.csv", show_col_types = FALSE) %>%
  # چون چندین run داریم، اول میانگین می‌گیریم
  group_by(model, set, field) %>%
  summarise(accuracy = mean(accuracy), .groups = "drop") %>%
  # مرتب‌سازی فیلدها و مجموعه‌ها
  mutate(field = factor(field, levels = c("species", "outcome", "induction"),
                        labels = c("Species", "Outcome", "Induction")),
         set = factor(set, levels = c("development", "held-out"),
                      labels = c("Development", "Held-out")),
         model = factor(model, levels = c("Magistral-Small", "Qwen3-8B",
                                          "Gemma-4-12B")))

p <- ggplot(d, aes(field, accuracy, fill = set)) +
  geom_col(position = position_dodge(width = 0.72), width = 0.62) +
  geom_text(aes(label = sprintf("%.3f", accuracy)),
            position = position_dodge(width = 0.72),
            vjust = -0.45, size = 2.9, colour = "black") +
  facet_wrap(~ model) +
  scale_fill_manual(values = c("Development" = "#999999",
                               "Held-out" = "#009E73")) +
  scale_y_continuous(limits = c(0, 1), expand = expansion(mult = c(0, 0.08))) +
  labs(x = NULL, y = "Accuracy") +
  theme_report() +
  theme(legend.position = "top")

# ابعاد عکس دقیقا مثل fig6 تنظیم شده است
save_fig(p, "fig8_attributes", width = 9, height = 4.2)

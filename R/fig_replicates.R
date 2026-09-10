source("R/setup.R")

rep <- read_csv("figdata/fig5b_replicates.csv", show_col_types = FALSE) %>%
  pivot_longer(c(F1, precision, recall),
               names_to = "metric", values_to = "value") %>%
  mutate(metric = factor(metric, levels = c("precision", "recall", "F1"),
                         labels = c("Precision", "Recall", "F1")),
         model = factor(model, levels = c("Magistral-Small", "Qwen3-8B")))

# محاسبه مقدار ماکزیمم برای قرار دادن متن در بالاترین نقطه
rsum <- rep %>% group_by(model, metric) %>%
  summarise(mean = mean(value), sd = sd(value),
            max_val = max(value), .groups = "drop")

b <- ggplot(rep, aes(model, value, colour = model)) +
  geom_point(position = position_jitter(width = 0.09, seed = 2),
             size = 2.4, alpha = 0.85) +
  geom_point(data = rsum, aes(model, mean), shape = 95, size = 11,
             colour = "black", inherit.aes = FALSE) +
  # قرار دادن تکست روی نقطه ماکزیمم به جای میانگین
  geom_text(data = rsum,
            aes(x = model, y = max_val, label = sprintf("%.3f\n\u00b1%.3f", mean, sd)),
            vjust = -0.6, size = 3, colour = "black", inherit.aes = FALSE) +
  facet_wrap(~ metric, scales = "free_y") +
  scale_colour_manual(values = PAL, guide = "none") +
  # افزایش فضای بالای نمودار برای جا شدن اعداد
  scale_y_continuous(expand = expansion(mult = c(0.14, 0.35))) +
  labs(x = NULL, y = "Score") +
  theme_report() +
  theme(axis.text.x = element_text(angle = 20, hjust = 1))

save_fig(b, "fig_replicates", width = 8, height = 4.5)

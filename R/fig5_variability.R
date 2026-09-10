# fig5_variability.R - decoding temperature and run-to-run variability.
# Panel A is a null result; panel B measures the noise it sits within.
source("R/setup.R")

tmp <- read_csv("figdata/fig5a_temperature.csv", show_col_types = FALSE)
tsum <- tmp %>% group_by(temperature) %>%
  summarise(mean = mean(F1), sd = sd(F1), .groups = "drop")

a <- ggplot(tmp, aes(factor(temperature), F1)) +
  geom_point(position = position_jitter(width = 0.10, seed = 1),
             size = 2.4, colour = PAL[["Qwen3-8B"]], alpha = 0.85) +
  geom_errorbar(data = tsum,
                aes(x = factor(temperature), y = mean,
                    ymin = mean - sd, ymax = mean + sd),
                width = 0.16, linewidth = 0.5, inherit.aes = FALSE) +
  geom_point(data = tsum, aes(factor(temperature), mean),
             shape = 95, size = 9, inherit.aes = FALSE) +
  labs(x = "Decoding temperature", y = "F1", tag = "A") +
  theme_report()

rep <- read_csv("figdata/fig5b_replicates.csv", show_col_types = FALSE) %>%
  pivot_longer(c(F1, precision, recall),
               names_to = "metric", values_to = "value") %>%
  mutate(metric = factor(metric, levels = c("precision", "recall", "F1"),
                         labels = c("Precision", "Recall", "F1")),
         model = factor(model, levels = c("Magistral-Small", "Qwen3-8B")))

rsum <- rep %>% group_by(model, metric) %>%
  summarise(mean = mean(value), sd = sd(value), .groups = "drop")

b <- ggplot(rep, aes(model, value, colour = model)) +
  geom_point(position = position_jitter(width = 0.09, seed = 2),
             size = 2.4, alpha = 0.85) +
  geom_point(data = rsum, aes(model, mean), shape = 95, size = 11,
             colour = "black", inherit.aes = FALSE) +
  geom_text(data = rsum,
            aes(model, mean, label = sprintf("%.3f\n\u00b1%.3f", mean, sd)),
            vjust = -0.7, size = 2.9, colour = "black", inherit.aes = FALSE) +
  facet_wrap(~ metric, scales = "free_y") +
  scale_colour_manual(values = PAL, guide = "none") +
  scale_y_continuous(expand = expansion(mult = c(0.14, 0.22))) +
  labs(x = NULL, y = "Score", tag = "B") +
  theme_report() +
  theme(axis.text.x = element_text(angle = 20, hjust = 1))

p <- a / b + plot_layout(heights = c(1, 1.1))
save_fig(p, "fig5_variability", width = 8, height = 7.5)

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
  labs(x = "Decoding temperature", y = "F1") +
  theme_report()

save_fig(a, "fig_temperature", width = 6, height = 4.5)

# fig3_prompt.R - performance across prompt versions, with rejection rate.
# Panel A shows F1 before and after normalisation, so that the contribution
# of the prompt can be separated from that of symbol resolution.
source("figures/scripts/setup.R")

VERS <- c("v1","v2","v3","v4","v5","v6full","v7full")
LABS <- c("v1","v2","v3","v4","v5","v6","v7")

d <- read_csv("figdata/fig3_prompt.csv", show_col_types = FALSE)
d <- d[d$version %in% VERS, ]
d$version <- factor(d$version, levels = VERS, labels = LABS)
d$model <- factor(d$model, levels = c("Magistral-Small", "Qwen3-8B"))
d$pct <- 100 * as.numeric(d$rejection_precision)

long <- d %>%
  select(model, version, F1, F1_raw) %>%
  pivot_longer(c(F1, F1_raw), names_to = "stage", values_to = "value") %>%
  mutate(stage = factor(stage, levels = c("F1_raw", "F1"),
                        labels = c("Raw output", "After normalisation")))

a <- ggplot(long, aes(version, value, colour = model,
                      linetype = stage, group = interaction(model, stage))) +
  geom_line(linewidth = 0.85) +
  geom_point(aes(shape = stage), size = 2.4) +
  scale_colour_manual(values = PAL) +
  scale_linetype_manual(values = c("Raw output" = "dashed",
                                   "After normalisation" = "solid")) +
  scale_shape_manual(values = c("Raw output" = 1,
                                "After normalisation" = 16)) +
  scale_y_continuous(expand = expansion(mult = c(0.10, 0.10))) +
  labs(x = NULL, y = "F1", tag = "A") +
  theme_report() +
  theme(legend.position = "top", legend.box = "vertical",
        legend.spacing.y = unit(-4, "pt"),
        axis.text.x = element_text(angle = 45, hjust = 1))

b <- ggplot(d, aes(version, rejected, fill = model)) +
  geom_col(position = position_dodge(width = 0.78), width = 0.68) +
  geom_text(aes(label = paste0(round(pct), "%")),
            position = position_dodge(width = 0.78),
            vjust = -0.5, size = 2.6, colour = "black") +
  geom_hline(yintercept = 92, linetype = "dashed", linewidth = 0.5) +
  scale_fill_manual(values = PAL, guide = "none") +
  scale_y_continuous(expand = expansion(mult = c(0, 0.16))) +
  labs(x = "Prompt version", y = "Abstracts rejected", tag = "B") +
  theme_report() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))

p <- a / b + plot_layout(heights = c(1.15, 0.9))
save_fig(p, "fig3_prompt", width = 8, height = 8)

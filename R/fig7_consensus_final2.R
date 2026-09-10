source("R/setup.R")

# Panel A: Cleveland Dot Plot (Sorted by F1, minimal & elegant)
s <- read_csv("figdata/fig7_consensus_scores.csv", show_col_types = FALSE) %>%
  # رتبه‌بندی مدل‌ها بر اساس افزایش F1
  mutate(rule = fct_reorder(rule, F1)) %>%
  pivot_longer(c(precision, recall, F1),
               names_to = "metric", values_to = "value") %>%
  mutate(metric = factor(metric, levels = c("precision", "recall", "F1"),
                         labels = c("Precision", "Recall", "F1")))

a <- ggplot(s, aes(x = value, y = rule)) +
  # کشیدن یک خط خاکستری ملایم برای وصل کردن ۳ نقطه هر قانون
  geom_line(aes(group = rule), color = "gray80", linewidth = 1) +
  # قرار دادن نقطه‌ها به جای میله‌ها
  geom_point(aes(color = metric), size = 4.5, alpha = 0.9) +
  scale_color_manual(values = c("Precision" = "#56B4E9", 
                               "Recall"    = "#E69F00", 
                               "F1"        = "#009E73")) +
  scale_x_continuous(limits = c(0, 1), expand = expansion(mult = c(0, 0.04))) +
  labs(x = "Score", y = NULL, tag = "A", color = NULL) +
  theme_report() +
  theme(
    legend.position = "top",
    text = element_text(size = 14), # بزرگتر کردن فونت کل پنل
    axis.text.y = element_text(size = 11)
  )

# Panel B: Trend Line (با فونت بزرگتر و تنظیم فاصله)
l <- read_csv("figdata/fig7b_ladder.csv", show_col_types = FALSE) %>%
  filter(set == "held-out") %>%
  mutate(subset = fct_inorder(subset), pct = 100 * proportion)

b <- ggplot(l, aes(x = subset, y = pct, group = 1)) +
  geom_line(color = "#3B528B", linewidth = 1) +
  geom_point(color = "#21918C", size = 3.5) +
  geom_text(aes(label = sprintf("%.1f%%", pct)),
            vjust = -1.3, size = 3.5) +
  scale_y_continuous(limits = c(0, 115), breaks = seq(0, 100, 25)) +
  # تایتل‌ها
  labs(x = "Number of Models in Agreement",
       y = "Matching Curated Data (%)", tag = "B") +
  theme_report() +
  theme(
    text = element_text(size = 14), # بزرگتر کردن فونت کل پنل
    axis.text.x = element_text(angle = 45, hjust = 1, size = 11),
    # کم کردن فاصله تایتل محورها با خود نمودار
    axis.title.x = element_text(margin = margin(t = 6)),
    axis.title.y = element_text(margin = margin(r = 6))
  )

p <- a / b + plot_layout(heights = c(1.15, 1))
save_fig(p, "fig7_consensus_final2", width = 8.5, height = 9)

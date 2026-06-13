library(ggplot2)

# Prepare dataset
df <- data.frame(
  Metric = rep(c('Target (Gene)', 'Species', 'Perturbation', 'Phenotype (OA Effect)'), each = 3),
  LLM = factor(rep(c('ChatGPT', 'Claude', 'Gemini'), 4), levels = c('ChatGPT', 'Claude', 'Gemini')),
  Accuracy = c(80, 90, 90,   
               90, 100, 100, 
               80, 80, 90,   
               80, 90, 90)   
)

# Define facet labels
facet_labels <- c(
  'Target (Gene)' = 'A. Target (Gene)',
  'Species' = 'B. Species',
  'Perturbation' = 'C. Perturbation',
  'Phenotype (OA Effect)' = 'D. Phenotype (OA Effect)'
)

# Generate plot
ggplot(df, aes(x = LLM, y = Accuracy, fill = LLM)) +
  geom_bar(stat = "identity", width = 0.7, color = "black", size = 0.2) +
  geom_text(aes(label = Accuracy), vjust = -0.5, fontface = "bold", size = 4) +
  facet_wrap(~ Metric, ncol = 2, labeller = as_labeller(facet_labels)) +
  scale_fill_manual(values = c('ChatGPT' = '#4C72B0', 'Claude' = '#DD8452', 'Gemini' = '#55A868')) +
  scale_y_continuous(limits = c(0, 115)) +
  labs(
    title = "Comparative LLM Accuracy by Extraction Feature",
    y = "Accuracy (%)",
    x = NULL
  ) +
  theme_minimal(base_size = 14) +
  theme(
    strip.text = element_text(face = "bold", size = 12, hjust = 0),
    strip.background = element_rect(fill = "#f0f0f0", color = NA),
    panel.spacing = unit(1.5, "lines"),
    plot.title = element_text(face = "bold", hjust = 0.5, size = 16, margin = margin(b = 20)),
    legend.position = "none",
    panel.grid.major.x = element_blank()
  )

# Export high-resolution image
# ggsave("LLM_Feature_Specific_Charts_R.png", width = 10, height = 10, dpi = 300)
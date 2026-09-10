
# fig1_trend.R - osteoarthritis animal-model publications over time.

# Shows the scale of literature a curated resource must keep pace with.

source("figures/scripts/setup.R")

master_data <- read.delim("PubmedIDs/All_Species_PMID_Dates_Master.tsv")

cleaned_data <- master_data %>%

  mutate(PubDate_char = as.character(PubDate)) %>%

  mutate(Year = as.numeric(stringr::str_extract(PubDate_char, "\\d{4}"))) %>%

  drop_na(Year) %>%

  filter(Year >= 1990 & Year < 2026)

plot_data <- cleaned_data %>%

  group_by(Year, Species) %>%

  summarise(Count = n(), .groups = "drop")

p <- ggplot(plot_data, aes(x = Year, y = Count, colour = Species)) +

  geom_line(linewidth = 1) +

  scale_colour_manual(values = c("#E69F00", "#56B4E9", "#009E73",

                                 "#F0E442", "#0072B2")) +

  labs(y = "Number of articles published", x = "Publication year",

       colour = "Species") +

  scale_x_continuous(breaks = scales::pretty_breaks(n = 8)) +

  theme_report(base_size =16) +

  theme(legend.position = "bottom", legend.title = element_text(face = "bold"))

save_fig(p, "fig1_trend", width = 8, height = 5)

cat("\ntotal records plotted:", nrow(cleaned_data), "\n")

print(as.data.frame(count(cleaned_data, Species)))


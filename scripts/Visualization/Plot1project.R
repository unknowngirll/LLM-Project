library(tidyverse)
library(ggplot2)
install.packages("cowplot")
library(cowplot)
master_data <- read.delim("All_Species_PMID_Dates_Master.tsv")

cleaned_data <- master_data %>%
  mutate(PubDate_char = as.character(PubDate)) %>%
  
  #stringr::str_extract -> this line will extract the 4 number in a row (to extract the year only)
  mutate(Year = as.numeric(stringr::str_extract(PubDate_char, "\\d{4}"))) %>%
  drop_na(Year) %>%
  filter(Year >= 1990)
plot_data <- cleaned_data %>%
  group_by(Year, Species) %>%
  summarise(Count = n()) %>%
  ungroup()
p<-ggplot(plot_data, aes(x = Year, y = Count, color = Species)) +
  
  geom_line(linewidth = 1) + 
  
  scale_color_manual(values = c("#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2")) +
 
  labs(title = NULL,
       y = "Number of Articles Published",
       x = "Publication Year",
       color = "Species") +
  
  scale_x_continuous(breaks = scales::pretty_breaks(n = 8)) + 
  cowplot::theme_minimal_grid() +
  
  theme(legend.position = "bottom")
  
#p + xlim(c(as.Date("2000-01-01"),as.Date("2025-01-01")))
p

ggsave("OA_Research_Trend.png", plot = p, width = 8, height = 6, dpi = 300)
ggsave("OA_Research_Trend.pdf", plot = p, width = 8, height = 6)


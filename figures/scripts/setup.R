# setup.R - packages, shared theme and palette for every figure.
# Sourced by each figure script; run once on its own to install.

lib <- file.path(Sys.getenv("HOME"), "R", "library")
dir.create(lib, recursive = TRUE, showWarnings = FALSE)
.libPaths(c(lib, .libPaths()))

need <- c("ggplot2", "dplyr", "tidyr", "readr", "scales",
          "patchwork", "forcats", "stringr")
missing <- need[!need %in% rownames(installed.packages())]
if (length(missing)) {
  install.packages(missing, lib = lib,
                   repos = "https://cloud.r-project.org")
}
invisible(lapply(need, library, character.only = TRUE))

# Okabe-Ito, chosen for colour-vision deficiency
PAL <- c(
  "Magistral-Small" = "#009E73",
  "Qwen3-8B"        = "#0072B2",
  "Gemma-4-12B"     = "#E69F00",
  "Gemma-4"         = "#E69F00",
  "raw"             = "#999999",
  "HGNC"            = "#0072B2",
  "development"     = "#999999",
  "held-out"        = "#009E73",
  "F1"              = "#555555",
  "precision"       = "#0072B2",
  "recall"          = "#E69F00"
)

theme_report <- function(base_size = 15) {
  theme_bw(base_size = base_size, base_family = "sans") +
    theme(
      panel.grid.minor  = element_blank(),
      panel.grid.major.x = element_blank(),
      panel.border      = element_blank(),
      axis.line         = element_line(colour = "black", linewidth = 0.4),
      strip.background  = element_rect(fill = "grey95", colour = NA),
      strip.text        = element_text(face = "bold", size = base_size - 1),
      legend.key        = element_blank(),
      legend.title      = element_blank(),
      plot.title        = element_text(face = "bold", size = base_size),
      plot.tag          = element_text(face = "bold", size = base_size + 3)
    )
}

save_fig <- function(p, name, width, height) {
  for (ext in c("png", "pdf")) {
    ggsave(file.path("figs", paste0(name, ".", ext)), p,
           width = width, height = height, dpi = 300)
  }
  message("saved figs/", name, ".png")
}

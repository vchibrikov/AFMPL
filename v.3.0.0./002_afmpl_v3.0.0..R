# ==============================================================================
# AFMPL v.3.0.0 - R Data Analysis & Visualization Script
# ==============================================================================
# A statistical analysis and plotting tool for AFM image data processed by AFMPL.
# Features:
# - Merges coordinate and aggregate datasets.
# - Calculates contour length statistics for segmented fibers.
# - Extracts Persistence Length (Lp) using Mean Squared End-to-End Distance (MSED) 
#   and 2D Worm-Like Chain (WLC) model fitting.
# - Calculates exact aggregate volumes in nm³.
# - Performs permutation tests with Bonferroni correction for statistical significance.
# - Generates publication-ready boxplots with jitter and significance stars.
# 
# Author: Vadym Chibrikov
# License: MIT
# ==============================================================================

#### import libraries ####
library("agricolae")
library("tidyverse")
library("RColorBrewer")
library("Cairo")
library("pals")
library("ggrepel")
library("gridExtra")
library("readxl")
library("openxlsx")
library("writexl")
library("readr")
library("minpack.lm")
library(dunn.test)
library(FSA)
library(multcompView)
library(ggsignif)
library(writexl)
library(coin)
library(readxl)

pacman::p_load('dplyr', 'tidyr', 'gapminder',
               'ggplot2',  'ggalt',
               'forcats', 'R.utils', 'png',
               'grid', 'ggpubr', 'scales',
               'bbplot', 'purrr', 'stringr')

#### merge datafiles ####

merge_sheets_by_row <- function(file_paths) {
  all_sheets_data <- list()

  for (file in file_paths) {
    sheet_names <- excel_sheets(file)

    for (sheet_name in sheet_names) {
      sheet_data <- read_excel(file, sheet = sheet_name)

      if (sheet_name %in% names(all_sheets_data)) {
        all_sheets_data[[sheet_name]] <- bind_rows(all_sheets_data[[sheet_name]], sheet_data)
      } else {
        all_sheets_data[[sheet_name]] <- sheet_data
      }
    }
  }

  return(all_sheets_data)
}

folder_path <- "./your/folder/path"

file_paths <- list.files(folder_path, pattern = "\\.xlsx$", full.names = TRUE)

merged_data <- merge_sheets_by_row(file_paths)

write_csv(merged_data[[1]], "./output/fiber_height_merged_output.csv")
write_csv(merged_data[[2]], "./output/path_coordinates_merged_output.csv")
write_csv(merged_data[[3]], "./output/aggregates_merged_output.csv")

rm(list = ls())

#### calculate MSED persistence length (internal segment method) ####
rm(list = ls(all.names = TRUE), envir = .GlobalEnv)

# Re-load necessary parameters after cleaning environment
pacman::p_load('dplyr', 'tidyr', 'readr', 'purrr', 'openxlsx', 'stringr')

image_length_nm <- 2000
image_quality_px <- 1024
pixel_scale <- image_length_nm/image_quality_px

l_min_nm <- 20.0   # Ignore segments shorter than 20 nm to avoid pixelation noise
l_max_ratio <- 1 # Max segment length is 100% of the total chain's contour length
bin_size_nm <- 20   # Group segments into 20 nm bins to calculate mean R^2

file_path <- "./path_coordinates_merged_output.csv"
data.path.coordinates <- read_csv(file_path, show_col_types = FALSE)

data.path.coordinates$fiber_id <- str_c(data.path.coordinates$filename, "_", data.path.coordinates$structure_id)

# Step 1: Calculate cumulative contour length (s) and nm coordinates for every point
cat("Calculating cumulative distances...\n")
data.path.scaled <- data.path.coordinates %>%
  group_by(fiber_id) %>%
  mutate(
    x_nm = x * pixel_scale,
    y_nm = y * pixel_scale,
    dx = x_nm - lag(x_nm, default = first(x_nm)),
    dy = y_nm - lag(y_nm, default = first(y_nm)),
    step_len = sqrt(dx^2 + dy^2),
    s = cumsum(step_len)
  ) %>%
  ungroup()

# Step 2: Split by chain to calculate all internal segments
chain_list <- split(data.path.scaled, data.path.scaled$fiber_id)

calc_internal_segments <- function(df) {
  n <- nrow(df)
  if (n < 10) return(NULL)

  idx <- expand.grid(i = 1:(n-1), j = 2:n)
  idx <- idx[idx$j > idx$i, ]

  max_s <- max(df$s)

  l <- df$s[idx$j] - df$s[idx$i]
  R2 <- (df$x_nm[idx$j] - df$x_nm[idx$i])^2 + (df$y_nm[idx$j] - df$y_nm[idx$i])^2

  valid <- l >= l_min_nm & l <= (l_max_ratio * max_s)

  if (sum(valid, na.rm = TRUE) == 0) {
    return(NULL)
  }

  data.frame(
    fiber_id = df$fiber_id[1],
    l = l[valid],
    R2 = R2[valid]
  )
}

cat("Extracting internal segments (this may take a moment)...\n")
all_segments <- bind_rows(lapply(chain_list, calc_internal_segments))

all_segments <- filter(all_segments, l > 20 & l < 500)

rm(list = c("data.path.coordinates", "chain_list", "data.path.scaled"))

# Step 3: Bin the lengths and calculate mean R^2 for each bin per chain
msed_binned <- all_segments %>%
  mutate(l_bin = round(l / bin_size_nm) * bin_size_nm) %>%
  group_by(fiber_id, l_bin) %>%
  summarise(
    mean_R2 = mean(R2),
    n_pairs = n(),
    .groups = 'drop'
  ) %>%
  filter(n_pairs >= 3)

# Step 4: Fit the 2D WLC model to extract Persistence Length (Lp)
fit_wlc <- function(df) {
  tryCatch({
    if (nrow(df) < 4) return(NA)

    fit <- nlsLM(mean_R2 ~ 4 * Lp * l_bin * (1 - (2 * Lp / l_bin) * (1 - exp(-l_bin / (2 * Lp)))),
                 data = df,
                 start = list(Lp = 15),
                 lower = c(Lp = 0.001),
                 control = nls.lm.control(maxiter = 500))

    coef(fit)["Lp"]
  }, error = function(e) {
    NA
  })
}

cat("Fitting WLC equations to extract Lp...\n")
chain_results <- msed_binned %>%
  group_by(fiber_id) %>%
  nest() %>%
  mutate(persistence_length_nm = map_dbl(data, fit_wlc)) %>%
  select(-data) %>%
  ungroup() %>%
  filter(!is.na(persistence_length_nm))

filename_split <- chain_results %>%
  separate_wider_regex(
    fiber_id,
    patterns = c(
      project              = "^[^_]+", "_",
      fraction             = "[^_]+", "_",
      concentration_mg_mL  = "[^_]+", "_",
      ripening_stage       = "[^_]+", "_",
      imaging_mode         = "[^_]+", "_",
      deposition_method   = "[^_]+", "_",
      drops_nr             = "[^_]+", "_",
      variable             = "[^.]+\\.[^_]+", "_",
      remainder            = "[^_]+", "_",
      segment              = "[^_]+$"
    )
  )

filename_split$variable <- substr(filename_split$variable, 1, nchar(filename_split$variable) - 4)

data <- filename_split

rm(list = c("all_segments", "chain_results", "filename_split", "msed_binned"))

# Create summary statistics
persistence.length.msed.summary <- data %>%
  group_by(fraction, ripening_stage, variable) %>%
  summarise(
    mean_msed_pl_nm = mean(persistence_length_nm),
    sd_msed_pl_nm = sd(persistence_length_nm),
    median_msed_pl_nm = median(persistence_length_nm),
    Q1_msed_pl_nm = quantile(persistence_length_nm, 0.25),
    Q3_msed_pl_nm = quantile(persistence_length_nm, 0.75),
    min_msed_pl_nm = min(persistence_length_nm),
    max_msed_pl_nm = max(persistence_length_nm),
    n_measurements = n(),
    .groups = 'drop'
  )

# Save results to an Excel file
wb_msed <- createWorkbook()

addWorksheet(wb_msed, "data")
writeData(wb_msed, "data", data)

addWorksheet(wb_msed, "summary")
writeData(wb_msed, "summary", persistence.length.msed.summary)

saveWorkbook(wb_msed, "./persistence_length_msed_statistics.xlsx", overwrite = TRUE)
cat("Success! Persistence length results saved.\n")


#### plot msed ####
file_path <- "./persistence_length_msed_statistics.xlsx"
data <- read_excel(file_path, sheet = 1)

axis.text.font.size = 18
axis.title.font.size = 18
group.labels.font.size = 6
legend.font.size = 18
dodge.value <- 0.5
x.axis.title.angle = 45
width_index = 0.2

colors <- c("#4C72B0", "#55A868", "#C44E52", "#E7BA52")

data$sample <- str_c(data$fraction, "_", data$ripening_stage, "_", data$variable)

data <- filter(data, persistence_length_nm > 1)

# Modifiable sample naming and ordering
data$sample <- ifelse(data$sample == "DASP_S1_pH_04", "DASP_O\npH = 4",
                           ifelse(data$sample == "DASP_S1_pH_07", "DASP_O\npH = 7",
                                  ifelse(data$sample == "DASP_S1_pH_09", "DASP_O\npH = 9",
                                         ifelse(data$sample == "DASP_S1_pH_11", "DASP_O\npH = 11",NA))))

logical_order <- c("DASP_O\npH = 4", "DASP_O\npH = 7", "DASP_O\npH = 9", "DASP_O\npH = 11")
data$sample <- factor(data$sample, levels = logical_order)

# Pair formation
unique_groups <- levels(data$sample)
group_pairs <- combn(unique_groups, 2, simplify = FALSE)

# Overall permutation test
pairwise_perm_results <- lapply(group_pairs, function(pair) {
  subset_data <- data %>% dplyr::filter(sample %in% pair)
  test <- oneway_test(persistence_length_nm ~ sample,
                      data = subset_data,
                      distribution = approximate(nresample = nrow(data)))
  data.frame(
    group1 = pair[1],
    group2 = pair[2],
    p.value = as.numeric(coin::pvalue(test))
  )
}) %>% bind_rows()

# Adjust p-values
pairwise_perm_results <- pairwise_perm_results %>%
  mutate(p.adj = p.adjust(p.value, method = "bonferroni"))

# Assign significance stars
sig_comparisons <- pairwise_perm_results %>%
  mutate(stars = case_when(
    p.adj < 0.01 ~ "p < 0.01",
    p.adj < 0.05 ~ "p < 0.05",
    TRUE ~ "Non-significant"))

sig_comparisons <- sig_comparisons[c(1, 2, 3, 4, 5, 6), ]

data %>%
  group_by(sample) %>%
  mutate(anova_point = 123,
         median = round(median(persistence_length_nm), 2),
         iqr = round(IQR(persistence_length_nm), 2),
         n = n()) %>%
  ungroup() -> data

data$group <- str_c("Median: ", data$median, "\n",  "IQR: ", data$iqr, "\n", "n: ", data$n)

# Plot function (boxplot + jitter)
get_data_plot <- function(my.data, point.size, padding, ymin, ymax, anova_text_margin,
                          hline_linewidth, xlabel, aspect.ratio.plot, axis.title.font.size,
                          axis.text.font.size, legend.font.size, legend.title.font.size,
                          plot.tag.size, plot.tag, y.scale.gaps, shape.values,
                          sig_comparisons = NULL) {
  
  ymin_rounded <- round(ymin, 2)
  ymax_rounded <- round(ymax, 2)
  y.scale.gaps_rounded <- round(y.scale.gaps, 2)
  
  summary_data <- my.data %>%
    dplyr::group_by(sample) %>%
    dplyr::summarise(
      group = first(group),
      anova_point = first(anova_point),
      .groups = "drop"
    )  
  
  result <- ggplot(data = my.data,
                   mapping = aes(x = sample,
                                 y = persistence_length_nm,
                                 color = sample,
                                 group = sample,
                                 shape = sample)) +
    # geom_violin(trim = F, aes(fill = sample), color = NA, bounds = c(0, 120), width = 0.2) + # violin if needed
    
    geom_jitter(mapping = aes(color = sample, shape = sample),
                position = position_jitterdodge(
                  jitter.width = 0.35, 
                  jitter.height = 0,   
                  dodge.width = 0.5),
                size = 1,
                alpha = 0.1) +
    
    geom_text(data = summary_data, 
              aes(x = sample, label = group, y = anova_point, color = sample),
              vjust = 0, 
              size = 2.75, 
              show.legend = FALSE,
              inherit.aes = FALSE) +
    
    geom_boxplot(aes(fill = sample), color = "black", width = 0.05, outlier.shape = NA, linewidth = 0.5) +
    geom_hline(yintercept = ymin_rounded, linewidth = hline_linewidth, colour = "#333333") +
    labs(x = xlabel, y = "Persistence length (nm)") +
    scale_color_manual(values = colors, name = "Sample") +
    scale_shape_manual(values = shape.values, name = "Sample") +
    scale_fill_manual(values = colors, name = "Sample") +
    scale_y_continuous(
      limits = c(ymin_rounded, ymax_rounded),
      breaks = seq(ymin_rounded, 120, by = 20)
    ) +
    bbc_style() +
    guides(shape = guide_legend(ncol = 1, byrow = TRUE)) +
    theme(
      panel.border = element_rect(color = "black", linewidth = 1, fill = NA),
      panel.background = element_blank(),
      plot.background = element_blank(),
      plot.margin = margin(0.2, 0.2, 0.2, 0.2, "cm"),
      axis.title = element_text(family = "TT Arial", size = axis.title.font.size,
                                face = "bold", color = "#222222"),
      axis.text.y = element_text(size = axis.text.font.size),
      axis.text.x = element_text(size = axis.text.font.size - 5.5, angle = 0, face = "bold"),
      legend.position = "none",
      legend.text = element_text(size = legend.font.size),
      legend.key.size = unit(0.2, "cm"),
      legend.title = element_text(size = legend.title.font.size, face = "bold"),
      legend.spacing.y = unit(0.2, "cm"),
      plot.tag = element_text(size = plot.tag.size),
      plot.tag.position = c(0.02, 0.02)
    ) +
    labs(tag = plot.tag)
  
  if (!is.null(sig_comparisons) && nrow(sig_comparisons) > 0) {
    comparisons_list <- sig_comparisons %>%
      select(group1, group2) %>%
      split(seq(nrow(.))) %>%
      lapply(as.character)
    
    y_start <- 20
    y_end   <- 602.5
    y_positions <- c(128, 135, 142, 149, 156, 163)
    
    result <- result +
      geom_signif(
        comparisons = comparisons_list,
        annotations = sig_comparisons$stars,
        y_position = y_positions,
        step_increase = 0.00001,
        textsize = axis.text.font.size / 5.5,
        tip_length = 0.0005
      )
  }
  
  return(result)
}

# Generate and save plot
a <- get_data_plot(
  my.data = data,
  point.size = 4,
  padding = 3,
  ymin = 0,
  ymax = 180,
  y.scale.gaps = 20,
  anova_text_margin = 1,
  hline_linewidth = 0.5,
  xlabel = "",
  # aspect.ratio.plot = 0.75,
  axis.title.font.size = 18,
  axis.text.font.size = 15,
  legend.font.size = 11,
  legend.title.font.size = 12,
  plot.tag.size = 18,
  shape.values = c(16, 15, 17, 18),
  plot.tag = "a)",
  sig_comparisons = sig_comparisons
)

plot_width <- 15
plot_height <- 17
plot_filename <- "./persistence_length_nm_boplot_jitter.jpeg"
ggsave(g, filename = plot_filename, dpi = 600, type = "cairo",
       width = plot_width, height = plot_height, units = "cm")

rm(list = ls(all.names = TRUE), envir = .GlobalEnv)

#### plot aggregate volume ####
file_path <- "./aggregates_merged_output.csv"
data <- read_csv(file_path, show_col_types = FALSE)

axis.text.font.size = 18
axis.title.font.size = 18
group.labels.font.size = 6
legend.font.size = 18
dodge.value <- 0.5
x.axis.title.angle = 45
width_index = 0.2
pixel_area_nm2 = (2000/1024)^2

colors <- c("#4C72B0", "#55A868", "#C44E52", "#E7BA52")

data$aggregare_volume_nm3 <- pixel_area_nm2 * data$volume_exact

data <- data %>%
  separate_wider_regex(
    filename,
    patterns = c(
      project             = "[^_]+", "_",
      fraction            = "[^_]+", "_",
      concentration_mg_mL = "[^_]+", "_",
      ripening_stage      = "[^_]+", "_",
      imaging_mode        = "[^_]+", "_",
      deposition_method   = "[^_]+", "_",
      drops_nr            = "[^_]+", "_",
      variable            = "[^_]+", "_",
      remainder           = ".*"
    )
  )

data$remainder <- substr(data$remainder, 1, nchar(data$remainder) - 4)
data$variable <- str_c(data$variable, "_", data$remainder)
data$sample <- str_c(data$fraction, "_", data$ripening_stage, "_", data$variable)

data <- data %>%
  select(sample, aggregare_volume_nm3)

# Modifiable sample naming and ordering
data$sample <- ifelse(data$sample == "DASP_S1_pH_04", "DASP_O\npH = 4",
                      ifelse(data$sample == "DASP_S1_pH_07", "DASP_O\npH = 7",
                             ifelse(data$sample == "DASP_S1_pH_09", "DASP_O\npH = 9",
                                    ifelse(data$sample == "DASP_S1_pH_11", "DASP_O\npH = 11",NA))))

logical_order <- c("DASP_O\npH = 4", "DASP_O\npH = 7", "DASP_O\npH = 9", "DASP_O\npH = 11")
data$sample <- factor(data$sample, levels = logical_order)

# Sample pairing
unique_groups <- levels(data$sample)
group_pairs <- combn(unique_groups, 2, simplify = FALSE)

# Overall permutation test
pairwise_perm_results <- lapply(group_pairs, function(pair) {
  subset_data <- data %>% dplyr::filter(sample %in% pair)
  test <- oneway_test(aggregare_volume_nm3 ~ sample,
                      data = subset_data,
                      distribution = approximate(nresample = nrow(data)))
  data.frame(
    group1 = pair[1],
    group2 = pair[2],
    p.value = as.numeric(coin::pvalue(test))
  )
}) %>% bind_rows()

# Adjust p-values
pairwise_perm_results <- pairwise_perm_results %>%
  mutate(p.adj = p.adjust(p.value, method = "bonferroni"))

# Assign significance stars
sig_comparisons <- pairwise_perm_results %>%
  mutate(stars = case_when(
    p.adj < 0.01 ~ "p < 0.01",
    p.adj < 0.05 ~ "p < 0.05",
    TRUE ~ "Non-significant"))

sig_comparisons <- sig_comparisons[c(1, 2, 3, 4, 5, 6), ]

data %>%
  group_by(sample) %>%
  mutate(anova_point = 710,
         median = round(median(aggregare_volume_nm3), 2),
         iqr = round(IQR(aggregare_volume_nm3), 2),
         n = n()) %>%
  ungroup() -> data

data$group <- str_c("Median: ", data$median, "\n",  "IQR: ", data$iqr, "\n", "n: ", data$n)

# Plot function
get_data_plot <- function(my.data, point.size, padding, ymin, ymax, anova_text_margin,
                          hline_linewidth, xlabel, aspect.ratio.plot, axis.title.font.size,
                          axis.text.font.size, legend.font.size, legend.title.font.size,
                          plot.tag.size, plot.tag, y.scale.gaps, shape.values,
                          sig_comparisons = NULL) {
  
  ymin_rounded <- round(ymin, 2)
  ymax_rounded <- round(ymax, 2)
  y.scale.gaps_rounded <- round(y.scale.gaps, 2)
  
  summary_data <- my.data %>%
    dplyr::group_by(sample) %>%
    dplyr::summarise(
      group = first(group),
      anova_point = first(anova_point),
      .groups = "drop"
    )  
  
  result <- ggplot(data = my.data,
                   mapping = aes(x = sample,
                                 y = aggregare_volume_nm3,
                                 color = sample,
                                 group = sample,
                                 shape = sample)) +
    # geom_violin(trim = F, aes(fill = sample), color = NA, bounds = c(0, 120), width = 0.2) + # violin if needed
    
    geom_jitter(mapping = aes(color = sample, shape = sample),
                position = position_jitterdodge(
                  jitter.width = 0.35, 
                  jitter.height = 0,   
                  dodge.width = 0.5),
                size = 1,
                alpha = 0.1) +
    
    geom_text(data = summary_data, 
              aes(x = sample, label = group, y = anova_point, color = sample),
              vjust = 0, 
              size = 2.75, 
              show.legend = FALSE,
              inherit.aes = FALSE) +
    
    geom_boxplot(aes(fill = sample), color = "black", width = 0.05, outlier.shape = NA, linewidth = 0.5) +
    geom_hline(yintercept = ymin_rounded, linewidth = hline_linewidth, colour = "#333333") +
    labs(x = xlabel, y = "Aggregate volume (nm³)") +
    scale_color_manual(values = colors, name = "Sample") +
    scale_shape_manual(values = shape.values, name = "Sample") +
    scale_fill_manual(values = colors, name = "Sample") +
    scale_y_continuous(
      limits = c(ymin_rounded, ymax_rounded),
      breaks = seq(ymin_rounded, 800, by = 100)
    ) +
    bbc_style() +
    guides(shape = guide_legend(ncol = 1, byrow = TRUE)) +
    theme(
      panel.border = element_rect(color = "black", linewidth = 1, fill = NA),
      panel.background = element_blank(),
      plot.background = element_blank(),
      plot.margin = margin(0.2, 0.2, 0.2, 0.2, "cm"),
      axis.title = element_text(family = "TT Arial", size = axis.title.font.size,
                                face = "bold", color = "#222222"),
      axis.text.y = element_text(size = axis.text.font.size),
      axis.text.x = element_text(size = axis.text.font.size - 5.5, angle = 0, face = "bold"),
      legend.position = "none",
      legend.text = element_text(size = legend.font.size),
      legend.key.size = unit(0.2, "cm"),
      legend.title = element_text(size = legend.title.font.size, face = "bold"),
      legend.spacing.y = unit(0.2, "cm"),
      plot.tag = element_text(size = plot.tag.size),
      plot.tag.position = c(0.02, 0.02)
    ) +
    labs(tag = plot.tag)
  
  if (!is.null(sig_comparisons) && nrow(sig_comparisons) > 0) {
    comparisons_list <- sig_comparisons %>%
      select(group1, group2) %>%
      split(seq(nrow(.))) %>%
      lapply(as.character)
    
    y_start <- 20
    y_end   <- 1002.5
    y_positions <- c(-120, -85, -50, -15, 20, 55)
    
    result <- result +
      geom_signif(
        comparisons = comparisons_list,
        annotations = sig_comparisons$stars,
        y_position = y_positions,
        step_increase = 0.00001,
        textsize = axis.text.font.size / 5.5,
        tip_length = 0.00005
      )
  }
  
  return(result)
}

# Generate and save plot
a <- get_data_plot(
  my.data = data,
  point.size = 4,
  padding = 3,
  ymin = 0,
  ymax = 1000,
  y.scale.gaps = 20,
  anova_text_margin = 1,
  hline_linewidth = 0.5,
  xlabel = "",
  # aspect.ratio.plot = 0.75,
  axis.title.font.size = 18,
  axis.text.font.size = 15,
  legend.font.size = 11,
  legend.title.font.size = 12,
  plot.tag.size = 18,
  shape.values = c(16, 15, 17, 18),
  plot.tag = "a)",
  sig_comparisons = sig_comparisons
)

plot_width <- 15
plot_height <- 17
plot_filename <- "./aggregate_volume_nm3_boxplot_jitter.jpeg"
ggsave(g, filename = plot_filename, dpi = 600, type = "cairo",
       width = plot_width, height = plot_height, units = "cm")

rm(list = ls(all.names = TRUE), envir = .GlobalEnv)

#### plot degree of aggregation ####
file_path <- "./aggregates_merged_output.csv"
data_aggregates <- read_csv(file_path, show_col_types = FALSE)

data_aggregates <- data_aggregates %>%
  separate_wider_regex(
    filename,
    patterns = c(
      project             = "[^_]+", "_",
      fraction            = "[^_]+", "_",
      concentration_mg_mL = "[^_]+", "_",
      ripening_stage      = "[^_]+", "_",
      imaging_mode        = "[^_]+", "_",
      deposition_method   = "[^_]+", "_",
      drops_nr            = "[^_]+", "_",
      variable            = "[^_]+", "_",
      remainder           = ".*"
    )
  )

data_aggregates$image_number <- substr(data_aggregates$remainder, nchar(data_aggregates$remainder) - 2, nchar(data_aggregates$remainder))

data_aggregates$remainder <- substr(data_aggregates$remainder, 1, nchar(data_aggregates$remainder) - 4)
data_aggregates$variable <- str_c(data_aggregates$variable, "_", data_aggregates$remainder)
data_aggregates$sample <- str_c(data_aggregates$fraction, "_", data_aggregates$ripening_stage, "_", data_aggregates$variable, "_", data_aggregates$image_number)

data_aggregates <- data_aggregates %>%
  select(sample, aggregate_id)

data_aggregates <- data_aggregates %>%
  group_by(sample) %>%
  summarise(n_aggregates = max(aggregate_id, na.rm = TRUE), .groups = "drop")

data_aggregates$n_aggregates <- as.numeric(data_aggregates$n_aggregates)

file_path <- "./path_coordinates_merged_output.csv"
data_chains <- read_csv(file_path, show_col_types = FALSE)

data_chains <- data_chains %>%
  separate_wider_regex(
    filename,
    patterns = c(
      project             = "[^_]+", "_",
      fraction            = "[^_]+", "_",
      concentration_mg_mL = "[^_]+", "_",
      ripening_stage      = "[^_]+", "_",
      imaging_mode        = "[^_]+", "_",
      deposition_method   = "[^_]+", "_",
      drops_nr            = "[^_]+", "_",
      variable            = "[^_]+", "_",
      remainder           = ".*"
    )
  )

data_chains$image_number <- substr(data_chains$remainder, nchar(data_chains$remainder) - 2, nchar(data_chains$remainder))

data_chains$remainder <- substr(data_chains$remainder, 1, nchar(data_chains$remainder) - 4)
data_chains$variable <- str_c(data_chains$variable, "_", data_chains$remainder)
data_chains$sample <- str_c(data_chains$fraction, "_", data_chains$ripening_stage, "_", data_chains$variable, "_", data_chains$image_number)

data_chains <- data_chains %>%
  select(sample, structure_id)

data_chains <- data_chains %>%
  filter(endsWith(structure_id, "_0")) %>%
  distinct()

data_chains$structure_id <- substr(data_chains$structure_id, 1, nchar(data_chains$structure_id) - 2)
data_chains$structure_id <- as.numeric(data_chains$structure_id)


data_chains <- data_chains %>%
  group_by(sample) %>%
  summarise(n_chains = max(structure_id, na.rm = TRUE), .groups = "drop")

data <- merge(data_aggregates, data_chains, by = "sample")

data$aggregation_degree_percent <- (data$n_aggregates/(data$n_aggregates + data$n_chains)) * 100

data$sample <- substr(data$sample, 1, nchar(data$sample) - 4)

axis.text.font.size = 18
axis.title.font.size = 18
group.labels.font.size = 6
legend.font.size = 18
dodge.value <- 0.5
x.axis.title.angle = 45
width_index = 0.2
pixel_area_nm2 = (2000/1024)^2

colors <- c("#4C72B0", "#55A868", "#C44E52", "#E7BA52")

# Modifiable sample naming and ordering
data$sample <- ifelse(data$sample == "DASP_S1_pH_04", "DASP_O\npH = 4",
                      ifelse(data$sample == "DASP_S1_pH_07", "DASP_O\npH = 7",
                             ifelse(data$sample == "DASP_S1_pH_09", "DASP_O\npH = 9",
                                    ifelse(data$sample == "DASP_S1_pH_11", "DASP_O\npH = 11",NA))))

logical_order <- c("DASP_O\npH = 4", "DASP_O\npH = 7", "DASP_O\npH = 9", "DASP_O\npH = 11")
data$sample <- factor(data$sample, levels = logical_order)

# Sample pairing
unique_groups <- levels(data$sample)
group_pairs <- combn(unique_groups, 2, simplify = FALSE)

# Overall permutation test
pairwise_perm_results <- lapply(group_pairs, function(pair) {
  subset_data <- data %>% dplyr::filter(sample %in% pair)
  test <- oneway_test(aggregation_degree_percent ~ sample,
                      data = subset_data,
                      distribution = approximate(nresample = nrow(data)))
  data.frame(
    group1 = pair[1],
    group2 = pair[2],
    p.value = as.numeric(coin::pvalue(test))  # Convert to numeric here
  )
}) %>% bind_rows()

# Adjust p-values
pairwise_perm_results <- pairwise_perm_results %>%
  mutate(p.adj = p.adjust(p.value, method = "bonferroni"))

# Assign significance stars
sig_comparisons <- pairwise_perm_results %>%
  mutate(stars = case_when(
    p.adj < 0.01 ~ "p < 0.01",
    p.adj < 0.05 ~ "p < 0.05",
    TRUE ~ "Non-significant"))

sig_comparisons <- sig_comparisons[c(1, 2, 3, 4, 5, 6), ]

data %>%
  group_by(sample) %>%
  mutate(anova_point = 41,
         median = round(median(aggregation_degree_percent), 2),
         iqr = round(IQR(aggregation_degree_percent), 2),
         n = n()) %>%
  ungroup() -> data

data$group <- str_c("Median: ", data$median, "\n",  "IQR: ", data$iqr, "\n", "n: ", data$n)

# Plot function
get_data_plot <- function(my.data, point.size, padding, ymin, ymax, anova_text_margin,
                          hline_linewidth, xlabel, aspect.ratio.plot, axis.title.font.size,
                          axis.text.font.size, legend.font.size, legend.title.font.size,
                          plot.tag.size, plot.tag, y.scale.gaps, shape.values,
                          sig_comparisons = NULL) {
  
  ymin_rounded <- round(ymin, 2)
  ymax_rounded <- round(ymax, 2)
  y.scale.gaps_rounded <- round(y.scale.gaps, 2)
  
  summary_data <- my.data %>%
    dplyr::group_by(sample) %>%
    dplyr::summarise(
      group = first(group),
      anova_point = first(anova_point),
      .groups = "drop"
    )  
  
  result <- ggplot(data = my.data,
                   mapping = aes(x = sample,
                                 y = aggregation_degree_percent,
                                 color = sample,
                                 group = sample,
                                 shape = sample)) +
    # geom_violin(trim = F, aes(fill = sample), color = NA, bounds = c(0, 120), width = 0.2) + # violin if needed
    
    geom_jitter(mapping = aes(color = sample, shape = sample),
                position = position_jitterdodge(
                  jitter.width = 0.35, 
                  jitter.height = 0,   
                  dodge.width = 0.5),
                size = 1,
                alpha = 0.1) +
    
    geom_text(data = summary_data, 
              aes(x = sample, label = group, y = anova_point, color = sample),
              vjust = 0, 
              size = 2.75, 
              show.legend = FALSE,
              inherit.aes = FALSE) +
    
    geom_boxplot(aes(fill = sample), color = "black", width = 0.05, outlier.shape = NA, linewidth = 0.5) +
    geom_hline(yintercept = ymin_rounded, linewidth = hline_linewidth, colour = "#333333") +
    labs(x = xlabel, y = "Degree of aggregation (%)") +
    scale_color_manual(values = colors, name = "Sample") +
    scale_shape_manual(values = shape.values, name = "Sample") +
    scale_fill_manual(values = colors, name = "Sample") +
    scale_y_continuous(
      limits = c(ymin_rounded, ymax_rounded),
      breaks = seq(ymin_rounded, 40, by = 10)
    ) +
    bbc_style() +
    guides(shape = guide_legend(ncol = 1, byrow = TRUE)) +
    theme(
      panel.border = element_rect(color = "black", linewidth = 1, fill = NA),
      panel.background = element_blank(),
      plot.background = element_blank(),
      plot.margin = margin(0.2, 0.2, 0.2, 0.2, "cm"),
      axis.title = element_text(family = "TT Arial", size = axis.title.font.size,
                                face = "bold", color = "#222222"),
      axis.text.y = element_text(size = axis.text.font.size),
      axis.text.x = element_text(size = axis.text.font.size - 5.5, angle = 0, face = "bold"),
      legend.position = "none",
      legend.text = element_text(size = legend.font.size),
      legend.key.size = unit(0.2, "cm"),
      legend.title = element_text(size = legend.title.font.size, face = "bold"),
      legend.spacing.y = unit(0.2, "cm"),
      plot.tag = element_text(size = plot.tag.size),
      plot.tag.position = c(0.02, 0.02)
    ) +
    labs(tag = plot.tag)
  
  if (!is.null(sig_comparisons) && nrow(sig_comparisons) > 0) {
    comparisons_list <- sig_comparisons %>%
      select(group1, group2) %>%
      split(seq(nrow(.))) %>%
      lapply(as.character)
    
    y_start <- 20
    y_end   <- 1002.5
    y_positions <- c(45, 48, 51, 54, 57, 60)
    
    result <- result +
      geom_signif(
        comparisons = comparisons_list,
        annotations = sig_comparisons$stars,
        y_position = y_positions,
        step_increase = 0.00001,
        textsize = axis.text.font.size / 5.5,
        tip_length = 0.00005
      )
  }
  
  return(result)
}

# Generate and save plot
a <- get_data_plot(
  my.data = data,
  point.size = 4,
  padding = 3,
  ymin = 0,
  ymax = 64,
  y.scale.gaps = 20,
  anova_text_margin = 1,
  hline_linewidth = 0.5,
  xlabel = "",
  # aspect.ratio.plot = 0.75,
  axis.title.font.size = 18,
  axis.text.font.size = 15,
  legend.font.size = 11,
  legend.title.font.size = 12,
  plot.tag.size = 18,
  shape.values = c(16, 15, 17, 18),
  plot.tag = "a)",
  sig_comparisons = sig_comparisons
)

plot_width <- 15
plot_height <- 17
plot_filename <- "./aggregation_degree_percent_boxplot_jitter.jpeg"
ggsave(g, filename = plot_filename, dpi = 600, type = "cairo",
       width = plot_width, height = plot_height, units = "cm")

rm(list = ls(all.names = TRUE), envir = .GlobalEnv)
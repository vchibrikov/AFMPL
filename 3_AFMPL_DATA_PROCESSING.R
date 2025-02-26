#### read libraries ####
# library("robustbase")
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

pacman::p_load('dplyr', 'tidyr', 'gapminder',
               'ggplot2',  'ggalt',
               'forcats', 'R.utils', 'png',
               'grid', 'ggpubr', 'scales',
               'bbplot')

image_length_nm <- 
image_quality_px <- 
pixel_scale <- image_length_nm/image_quality_px
segment_number <- 

#### MERGE DATAFILES ####
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

folder_path <- "./RESULTS/1_output_path/"

file_paths <- list.files(folder_path, pattern = "\\.xlsx$", full.names = TRUE)

merged_data <- merge_sheets_by_row(file_paths)

write_xlsx(merged_data, "./filepath/to/merged/output/merged_output.xlsx")

#### CALCULATE STATISTICS AND EXTRACT ####
# HEIGHT
file_path <- "./filepath/to/merged/output/merged_output.xlsx"
data <- read_excel(file_path, sheet = "height_nm")

pattern <- "(.*?)_(.*?)_(.*?)_(.*?)_(.*?)_(.*?)_(.*?)_(.*)"
filename_split <- tibble(project = sub(pattern, "\\1", data$image_filename),
                              fraction = sub(pattern, "\\2", data$image_filename),
                              concentration_mg_mL = sub(pattern, "\\3", data$image_filename),
                              ripening_stage = sub(pattern, "\\4", data$image_filename),
                              imaging_mode = sub(pattern, "\\5", data$image_filename),
                              deposition_method = sub(pattern, "\\6", data$image_filename),
                              drops_nr = sub(pattern, "\\7", data$image_filename),
                              afm_fiber_number = sub(pattern, "\\8", data$image_filename)
                              )

filename_split$drops_nr <- gsub("\\.", "_", filename_split$drops_nr)
pattern <- "(.*?)_(.*)"

filename_split_2 <- tibble(drops = sub(pattern, "\\1",filename_split$drops_nr),
                         afm_image_nr = sub(pattern, "\\2", filename_split$drops_nr))

data <- cbind(data, filename_split, filename_split_2)
data <- data %>%
  select(-drops_nr)

colnames(data) <- c("filename", "height_nm", "project", "fraction", "concentration_mg_mL", "ripening_stage",
                    "imaging_mode", "deposition_method", "afm_fiber_number",
                    "drops_nr", "afm_image_nr")

data <- filter(data, height_nm > 0)

data_height <- data %>%
  group_by(fraction, ripening_stage) %>%
  summarize(
    mean_height_nm = mean(height_nm, na.rm = TRUE),
    sd_height_nm = sd(height_nm, na.rm = TRUE),
    median_height_nm = median(height_nm, na.rm = TRUE),
    Q1_height_nm = quantile(height_nm, 0.25, na.rm = TRUE),
    Q3_height_nm = quantile(height_nm, 0.75, na.rm = TRUE),
    n_measurements = n(),
    n_fibers = n_distinct(paste(afm_fiber_number, afm_image_nr, sep = "_"))
  ) %>%
  ungroup()

wb <- createWorkbook()

addWorksheet(wb, "data")
writeData(wb, "data", data)

# Add the second data frame to the second sheet
addWorksheet(wb, "summary")
writeData(wb, "summary", data_height)

# Save the workbook
saveWorkbook(wb, "./output/path/to/height_statistics.xlsx", overwrite = TRUE)

# LENGTH
file_path <- "./filepath/to/merged/output/merged_output.xlsx"
data <- read_excel(file_path, sheet = "contour_length_px")

pattern <- "(.*?)_(.*?)_(.*?)_(.*?)_(.*?)_(.*?)_(.*?)_(.*)"
filename_split <- tibble(project = sub(pattern, "\\1", data$image_filename),
                         fraction = sub(pattern, "\\2", data$image_filename),
                         concentration_mg_mL = sub(pattern, "\\3", data$image_filename),
                         ripening_stage = sub(pattern, "\\4", data$image_filename),
                         imaging_mode = sub(pattern, "\\5", data$image_filename),
                         deposition_method = sub(pattern, "\\6", data$image_filename),
                         drops_nr = sub(pattern, "\\7", data$image_filename),
                         afm_fiber_number = sub(pattern, "\\8", data$image_filename)
)

filename_split$drops_nr <- gsub("\\.", "_", filename_split$drops_nr)
pattern <- "(.*?)_(.*)"

filename_split_2 <- tibble(drops = sub(pattern, "\\1",filename_split$drops_nr),
                           afm_image_nr = sub(pattern, "\\2", filename_split$drops_nr))

data <- cbind(data, filename_split, filename_split_2)
data <- data %>%
  select(-drops_nr)

colnames(data) <- c("filename", "contour_length_px", "project", "fraction", "concentration_mg_mL", "ripening_stage",
                    "imaging_mode", "deposition_method", "afm_fiber_number",
                    "drops_nr", "afm_image_nr")

data_contour_length <- data %>%
  group_by(fraction, ripening_stage) %>%
  summarize(mean_contour_length_nm = mean(contour_length_px * image_length_nm/image_quality_px),
            sd_contour_length_nm = sd(contour_length_px * image_length_nm/image_quality_px),
            median_contour_length_nm = median(contour_length_px * image_length_nm/image_quality_px, na.rm = TRUE),
            Q1_contour_length_nm = quantile(contour_length_px * image_length_nm/image_quality_px, 0.25, na.rm = TRUE),
            Q3_contour_length_nm = quantile(contour_length_px * image_length_nm/image_quality_px, 0.75, na.rm = TRUE),
            n_fibers = n()) %>%
  ungroup()

wb <- createWorkbook()

addWorksheet(wb, "data")
writeData(wb, "data", data)

# Add the second data frame to the second sheet
addWorksheet(wb, "summary")
writeData(wb, "summary", data_contour_length)

# Save the workbook
saveWorkbook(wb, "./output/path/to/length_statistics.xlsx", overwrite = TRUE)

# Shape factor
data_end_to_end_distance_px <- read_excel(file_path, sheet = "end_to_end_distance_px")
data_contour_length_px <- read_excel(file_path, sheet = "contour_length_px")

data_shape_factor <- merge(data_end_to_end_distance_px, data_contour_length_px, by = "image_filename")
data_shape_factor$shape_factor <- data_shape_factor$contour_length_px/data_shape_factor$end_to_end_distance_px

pattern <- "(.*?)_(.*?)_(.*?)_(.*?)_(.*?)_(.*?)_(.*?)_(.*)"
filename_split <- tibble(project = sub(pattern, "\\1", data_shape_factor$image_filename),
                         fraction = sub(pattern, "\\2", data_shape_factor$image_filename),
                         concentration_mg_mL = sub(pattern, "\\3", data_shape_factor$image_filename),
                         ripening_stage = sub(pattern, "\\4", data_shape_factor$image_filename),
                         imaging_mode = sub(pattern, "\\5", data_shape_factor$image_filename),
                         deposition_method = sub(pattern, "\\6", data_shape_factor$image_filename),
                         drops_nr = sub(pattern, "\\7", data_shape_factor$image_filename),
                         afm_fiber_number = sub(pattern, "\\8", data_shape_factor$image_filename)
)

filename_split$drops_nr <- gsub("\\.", "_", filename_split$drops_nr)
pattern <- "(.*?)_(.*)"

filename_split_2 <- tibble(drops = sub(pattern, "\\1",filename_split$drops_nr),
                           afm_image_nr = sub(pattern, "\\2", filename_split$drops_nr))

data_shape_factor <- cbind(data_shape_factor, filename_split, filename_split_2)
data_shape_factor <- data_shape_factor %>%
  select(-drops_nr)

colnames(data_shape_factor) <- c("filename", "end_to_end_distance_px", "contour_length_px", "shape_factor",
                                 "project", "fraction", "concentration_mg_mL", "ripening_stage", "imaging_mode",
                                 "deposition_method", "afm_fiber_number", "drops_nr", "afm_image_nr")

shape_factor <- data_shape_factor %>%
  group_by(fraction, ripening_stage) %>%
  summarize(mean_shape_factor = mean(shape_factor),
            sd_shape_factor = sd(shape_factor),
            median_shape_factor = median(shape_factor, na.rm = TRUE),
            Q1_shape_factor = quantile(shape_factor, 0.25, na.rm = TRUE),
            Q3_shape_factor = quantile(shape_factor, 0.75, na.rm = TRUE),
            mean_contour_length_nm = mean(contour_length_px) * pixel_scale,
            sd_contour_length_nm = sd(contour_length_px) * pixel_scale,
            mean_end_to_end_distance_nm = mean(end_to_end_distance_px) * pixel_scale,
            sd_end_to_end_distance_nm = sd(end_to_end_distance_px) * pixel_scale,
            n_fibers = n()) %>%
  ungroup()

wb <- createWorkbook()

addWorksheet(wb, "data")
writeData(wb, "data", data_shape_factor)

# Add the second data frame to the second sheet
addWorksheet(wb, "summary")
writeData(wb, "summary", shape_factor)

# Save the workbook
saveWorkbook(wb, "./output/path/to/shape_factor_statistics.xlsx", overwrite = TRUE)

#### PERSISTENCE LENGTH - MSED ####
rm(list = ls(all.names = TRUE), envir = .GlobalEnv)

image_length_nm <-
image_quality_px <-
pixel_scale <- image_length_nm/image_quality_px
segment_number <-

file_path <- "./filepath/to/merged/output/merged_output.xlsx"
data.path.coordinates <- read_excel(file_path, sheet = "path_coordinates")

# Loop over segment numbers from 1 to 10
for (segment_number in 1:segment_number) {

  data.path.coordinates.segmented <- data.path.coordinates %>%
    group_by(image_filename) %>%
    mutate(segment_index = rep(1:(n() %/% ((n() - 1)/segment_number) ), each = n()/segment_number)[1:n()]) %>%
    na.omit() %>%
    mutate(image_filename = str_c(image_filename, '_', segment_index)) %>%
    select(image_filename, x, y) %>%
    ungroup()

  persistence.length.msed <- data.path.coordinates.segmented %>%
    group_by(image_filename) %>%
    mutate(contour_length_nm = n() * pixel_scale) %>%
    select(image_filename, contour_length_nm) %>%
    ungroup() %>%
    distinct()

  shortest.distance <- data.path.coordinates.segmented %>%
    group_by(image_filename) %>%
    filter(n() > 1) %>%
    filter(row_number() == 1 | row_number() == n()) %>%
    ungroup()

  # Separate odd and even rows
  odd_rows <- shortest.distance %>%
    filter(row_number() %% 2 == 1)

  even_rows <- shortest.distance %>%
    filter(row_number() %% 2 == 0)

  # Ensure both have the same length
  n_rows <- min(nrow(odd_rows), nrow(even_rows))
  odd_rows <- odd_rows[1:n_rows, ]
  even_rows <- even_rows[1:n_rows, ]

  # Rename columns
  colnames(odd_rows) <- c('image_filename', 'x_start', 'y_start')
  colnames(even_rows) <- c('image_filename', 'x_end', 'y_end')

  persistence.length.msed <- persistence.length.msed %>%
    filter(contour_length_nm != pixel_scale)

  persistence.length.msed$shortest_distance_nm <- sqrt(((even_rows$x_end - odd_rows$x_start)^2) +
                                                         ((even_rows$y_end - odd_rows$y_start)^2)) * pixel_scale

  # Extract filename details
  pattern <- "(.*?)_(.*?)_(.*?)_(.*?)_(.*?)_(.*?)_(.*?)_(.*?)_(.*)"
  filename_split <- tibble(project = sub(pattern, "\\1", persistence.length.msed$image_filename),
                           fraction = sub(pattern, "\\2", persistence.length.msed$image_filename),
                           concentration_mg_mL = sub(pattern, "\\3", persistence.length.msed$image_filename),
                           ripening_stage = sub(pattern, "\\4", persistence.length.msed$image_filename),
                           imaging_mode = sub(pattern, "\\5", persistence.length.msed$image_filename),
                           deposition_method = sub(pattern, "\\6", persistence.length.msed$image_filename),
                           drops_nr = sub(pattern, "\\7", persistence.length.msed$image_filename),
                           afm_fiber_number = sub(pattern, "\\8", persistence.length.msed$image_filename),
                           segment = sub(pattern, "\\9", persistence.length.msed$image_filename))

  filename_split$drops_nr <- gsub("\\.", "_", filename_split$drops_nr)

  pattern <- "(.*?)_(.*)"
  filename_split_2 <- tibble(drops = sub(pattern, "\\1", filename_split$drops_nr),
                             afm_image_nr = sub(pattern, "\\2", filename_split$drops_nr))

  persistence.length.msed <- cbind(persistence.length.msed, filename_split, filename_split_2) %>%
    select(-drops_nr)

  # Function to solve the persistence length equation
  solve_equation <- function(row) {
    shortest_distance_nm <- row$shortest_distance_nm^2
    contour_length_nm <- row$contour_length_nm

    equation <- function(lambda) {
      4 * lambda * (contour_length_nm - 2 * lambda * (1 - exp(-contour_length_nm / (2 * lambda)))) - shortest_distance_nm
    }

    result <- uniroot(equation, interval = c(0, 1000))
    return(data.frame(lambda = result$root))
  }

  # Apply the function to each row
  persistence.length.msed$persistence_length_nm <- persistence.length.msed %>%
    rowwise() %>%
    do(solve_equation(.)) %>%
    as.data.frame() %>%
    unlist()

  persistence.length.msed$segment <- segment_number
  
  # Create summary statistics
  persistence.length.msed.summary <- persistence.length.msed %>%
    group_by(fraction, ripening_stage, segment) %>%
    summarise(mean_msed_pl_nm = mean(persistence_length_nm),
              sd_msed_pl_nm = sd(persistence_length_nm),
              median_msed_pl_nm = median(persistence_length_nm, na.rm = TRUE),
              Q1_msed_pl_nm = quantile(persistence_length_nm, 0.25, na.rm = TRUE),
              Q3_msed_pl_nm = quantile(persistence_length_nm, 0.75, na.rm = TRUE),
              min_msed_pl_nm = min(persistence_length_nm),
              max_msed_pl_nm = max(persistence_length_nm),
              n_segments = segment_number,
              n_fibers = round(n()/segment_number, 0),
              n_measurements = n())

  # Save results to an Excel file
  wb <- createWorkbook()

  addWorksheet(wb, "data")
  writeData(wb, "data", persistence.length.msed)

  addWorksheet(wb, "summary")
  writeData(wb, "summary", persistence.length.msed.summary)

  saveWorkbook(wb, paste0("./path/to/save/results/persistence_length_msed_", segment_number, "_segment_statistics.xlsx"), overwrite = TRUE)

  # Cleanup for next iteration
  rm(persistence.length.msed, persistence.length.msed.summary, odd_rows, even_rows, shortest.distance, filename_split, filename_split_2)
}

#### PERSISTENCE LENGTH - MSMD ####
rm(list = ls(all.names = TRUE), envir = .GlobalEnv)

image_length_nm <-
image_quality_px <-
pixel_scale <- image_length_nm/image_quality_px
segment_number <-

for (segment_number in 1:segment_number) {

  file_path <- "./RESULTS/2_calculations_output/merged_output.xlsx"
  data.path.coordinates <- read_excel(file_path, sheet = "path_coordinates")
  
  data.path.coordinates <- data.path.coordinates %>%
    group_by(image_filename) %>%
    mutate(segment_index = rep(1:(n() %/% ((n() - 1)/segment_number) ), each = n()/segment_number)[1:n()]) %>%
    na.omit() %>%
    mutate(image_filename = str_c(image_filename, '-', segment_index)) %>%
    select(image_filename, x, y) %>%
    ungroup()

  midpoind.shortest.distance <- data.path.coordinates %>%
    group_by(image_filename) %>%
    filter(row_number() == 1 | row_number() == n())

  odd_rows <- midpoind.shortest.distance %>%
    filter(row_number() %% 2 == 1)
  colnames(odd_rows) <- c('image_filename', 'x_start', 'y_start')

  even_rows <- midpoind.shortest.distance %>%
    filter(row_number() %% 2 == 0)
  colnames(even_rows) <- c('image_filename', 'x_end', 'y_end')

  persistence.length.msmd <- merge(odd_rows, even_rows, by = 'image_filename', all = TRUE)
  rm(even_rows, odd_rows, midpoind.shortest.distance)

  persistence.length.msmd$shortest.distance.midpoint.coordinate.x <- (persistence.length.msmd$x_start +  persistence.length.msmd$x_end) / 2
  persistence.length.msmd$shortest.distance.midpoint.coordinate.y <- (persistence.length.msmd$y_start +  persistence.length.msmd$y_end) / 2

  contour.length.midpoint.coordinate <- data.path.coordinates %>%
    group_by(image_filename) %>%
    filter(row_number() == ceiling(n() / 2))
  colnames(contour.length.midpoint.coordinate) <- c('image_filename', 'contour.length.midpoint.coordinate.x', 'contour.length.midpoint.coordinate.y')

  persistence.length.msmd <- merge(persistence.length.msmd, contour.length.midpoint.coordinate, by = 'image_filename', all = TRUE)
  rm(contour.length.midpoint.coordinate)

  persistence.length.msmd$mean.squared.midpoint.displacement.nm <-
    (((persistence.length.msmd$contour.length.midpoint.coordinate.x -
         persistence.length.msmd$shortest.distance.midpoint.coordinate.x)^2 +
        (persistence.length.msmd$contour.length.midpoint.coordinate.y -
           persistence.length.msmd$shortest.distance.midpoint.coordinate.y)^2)^0.5) * pixel_scale

  persistence.length.msmd <- persistence.length.msmd %>%
    select(image_filename, mean.squared.midpoint.displacement.nm)

  contour.length.nm <- data.path.coordinates %>%
    group_by(image_filename) %>%
    mutate(contour.length.nm = n() * pixel_scale) %>%
    select(image_filename, contour.length.nm) %>%
    ungroup()

  contour.length.nm <- contour.length.nm %>%
    group_by(image_filename) %>%
    unique() %>%
    ungroup()

  persistence.length.msmd <- merge(persistence.length.msmd, contour.length.nm, by = 'image_filename', all = TRUE)

  rm(contour.length.nm, data.path.coordinates)

  persistence.length.msmd$persistence.length.msmd.nm <- (persistence.length.msmd$contour.length.nm^3) /
                                                        (48 * (persistence.length.msmd$mean.squared.midpoint.displacement.nm)^2)

  persistence.length.msmd <- persistence.length.msmd %>% filter(!is.infinite(persistence.length.msmd.nm))

  # Extract filename details
  pattern <- "(.*?)_(.*?)_(.*?)_(.*?)_(.*?)_(.*?)_(.*?)_(.*)"
  filename_split <- tibble(project = sub(pattern, "\\1", persistence.length.msmd$image_filename),
                           fraction = sub(pattern, "\\2", persistence.length.msmd$image_filename),
                           concentration_mg_mL = sub(pattern, "\\3", persistence.length.msmd$image_filename),
                           ripening_stage = sub(pattern, "\\4", persistence.length.msmd$image_filename),
                           imaging_mode = sub(pattern, "\\5", persistence.length.msmd$image_filename),
                           deposition_method = sub(pattern, "\\6", persistence.length.msmd$image_filename),
                           drops_nr = sub(pattern, "\\7", persistence.length.msmd$image_filename),
                           afm_fiber_number = sub(pattern, "\\8", persistence.length.msmd$image_filename),
                           segment = sub(pattern, "\\9", persistence.length.msmd$image_filename))

  filename_split$drops_nr <- gsub("\\.", "_", filename_split$drops_nr)

  pattern <- "(.*?)_(.*)"
  filename_split_2 <- tibble(drops = sub(pattern, "\\1", filename_split$drops_nr),
                             afm_image_nr = sub(pattern, "\\2", filename_split$drops_nr))

  pattern <- "(.*?)-(.*)"
  filename_split_3 <- tibble(afm_fiber_nr = sub(pattern, "\\1", filename_split$afm_fiber_number),
                             segment_nr = sub(pattern, "\\2", filename_split$afm_fiber_number))

  persistence.length.msmd <- cbind(persistence.length.msmd, filename_split, filename_split_2, filename_split_3) %>%
    select(-c(drops_nr, afm_fiber_number, segment))

  persistence.length.msmd$segment_nr <- segment_number
  
  persistence.length.msmd.summary <- persistence.length.msmd %>%
    group_by(fraction, ripening_stage) %>%
    summarise(mean_msmd_pl_nm = mean(persistence.length.msmd.nm),
              sd_msmd_pl_nm = sd(persistence.length.msmd.nm),
              median_msmd_pl_nm = median(persistence.length.msmd.nm, na.rm = TRUE),
              Q1_msmd_pl_nm = quantile(persistence.length.msmd.nm, 0.25, na.rm = TRUE),
              Q3_msmd_pl_nm = quantile(persistence.length.msmd.nm, 0.75, na.rm = TRUE),
              min_msmd_pl_nm = min(persistence.length.msmd.nm),
              max_msmd_pl_nm = max(persistence.length.msmd.nm),
              n_segments = segment_number,
              n_fibers = round(n()/segment_number, 0),
              n_measurements = n())

  # Save results to an Excel file
  wb <- createWorkbook()

  addWorksheet(wb, "data")
  writeData(wb, "data", persistence.length.msmd)

  addWorksheet(wb, "summary")
  writeData(wb, "summary", persistence.length.msmd.summary)

  saveWorkbook(wb, paste0("./path/to/save/results/persistence_length_msmd_", segment_number, "_segment_statistics.xlsx"), overwrite = TRUE)
}

#### PERSISTENCE LENGTH - BCF ####
rm(list = ls(all.names = TRUE), envir = .GlobalEnv)

image_length_nm <-
image_quality_px <-
pixel_scale <- image_length_nm/image_quality_px
segment_number <-

for (segment_number in 1:segment_number) {

  file_path <- "./RESULTS/2_calculations_output/merged_output.xlsx"
  data.path.coordinates <- read_excel(file_path, sheet = "path_coordinates")
  
  data.path.coordinates.segmented <- data.path.coordinates %>%
  group_by(image_filename) %>%
  mutate(segment_index = rep(1:(n() %/% ((n() - 1)/segment_number)), each = n()/segment_number)[1:n()]) %>%
  na.omit() %>%
  mutate(image_filename = str_c(image_filename, '_', segment_index)) %>%
  select(image_filename, x, y) %>%
  ungroup()

calculate_angle <- function(df) {
  df %>%
    group_by(image_filename) %>%
    filter(n() >= 6) %>%
    summarise(
      x_first = list(head(x, 3)),
      y_first = list(head(y, 3)),
      x_last = list(tail(x, 3)),
      y_last = list(tail(y, 3))
    ) %>%
    rowwise() %>%
    mutate(
      # Fit lines using lm() (y = m*x + b -> slope m is coefficients[2])
      slope_first = coef(lm(unlist(y_first) ~ unlist(x_first)))[2],
      slope_last = coef(lm(unlist(y_last) ~ unlist(x_last)))[2],
      # Compute the cosine of the angle between the two lines
      cos_theta = (slope_first * slope_last + 1) / 
        sqrt((1 + slope_first^2) * (1 + slope_last^2)),
      # Convert cos_theta to the angle in radians, then to degrees
      angle_degrees = acos(cos_theta) * (180 / pi),
      angle_degrees = 180 - angle_degrees,
      cos_theta = cos(angle_degrees)
    ) %>%
    ungroup()
}

data.path.angles <- calculate_angle(data.path.coordinates.segmented)

data.path.coordinates.segmented <- data.path.coordinates %>%
  group_by(image_filename) %>%
  mutate(segment_index = rep(1:(n() %/% ((n() - 1)/segment_number) ), each = n()/segment_number)[1:n()]) %>%
  na.omit() %>%
  mutate(image_filename = str_c(image_filename, '_', segment_index)) %>%
  select(image_filename, x, y) %>%
  ungroup()

data.path.length <- data.path.coordinates.segmented %>%
  group_by(image_filename) %>%
  mutate(contour_length_nm = n() * pixel_scale) %>%
  select(image_filename, contour_length_nm) %>%
  ungroup() %>%
  distinct()

persistence.length.bcf <- merge(data.path.length, data.path.angles, by = "image_filename")

persistence.length.bcf <- persistence.length.bcf %>%
  select(c(image_filename, contour_length_nm, cos_theta)) %>%
           na.omit()
  
# Function to solve the persistence length equation
solve_equation <- function(row) { 
  contour_length_nm <- row$contour_length_nm
  cos_theta <- row$cos_theta
  
  # Define the equation
  equation <- function(lambda) {
    exp(-contour_length_nm / (2 * lambda)) - cos_theta
  }
  
  # Check function values at interval endpoints
  lower_val <- equation(0.01)  # Avoid division by zero
  upper_val <- equation(1000)
  
  if (lower_val * upper_val > 0) {  # If both values have the same sign, return NA
    return(data.frame(lambda = NA))
  }
  
  # Solve for lambda
  result <- uniroot(equation, interval = c(0.01, 1000))
  return(data.frame(lambda = result$root))
}

# Apply the function to each row
persistence.length.bcf <- persistence.length.bcf %>%
  rowwise() %>%
  mutate(bcf_pl_nm = list(solve_equation(cur_data()))) %>%  # Store as a list
  unnest(cols = c(bcf_pl_nm)) %>%
  na.omit() %>%
  rename(bcf_pl_nm = lambda)

# Extract filename details
pattern <- "(.*?)_(.*?)_(.*?)_(.*?)_(.*?)_(.*?)_(.*?)_(.*)"
filename_split <- tibble(project = sub(pattern, "\\1", persistence.length.bcf$image_filename),
                         fraction = sub(pattern, "\\2", persistence.length.bcf$image_filename),
                         concentration_mg_mL = sub(pattern, "\\3", persistence.length.bcf$image_filename),
                         ripening_stage = sub(pattern, "\\4", persistence.length.bcf$image_filename),
                         imaging_mode = sub(pattern, "\\5", persistence.length.bcf$image_filename),
                         deposition_method = sub(pattern, "\\6", persistence.length.bcf$image_filename),
                         drops_nr = sub(pattern, "\\7", persistence.length.bcf$image_filename),
                         afm_fiber_number = sub(pattern, "\\8", persistence.length.bcf$image_filename),
                         segment = sub(pattern, "\\9", persistence.length.bcf$image_filename))

filename_split$drops_nr <- gsub("\\.", "_", filename_split$drops_nr)

pattern <- "(.*?)_(.*)"
filename_split_2 <- tibble(drops = sub(pattern, "\\1", filename_split$drops_nr),
                           afm_image_nr = sub(pattern, "\\2", filename_split$drops_nr))

pattern <- "(.*?)_(.*)"
filename_split_3 <- tibble(afm_fiber_nr = sub(pattern, "\\1", filename_split$afm_fiber_number),
                           segment_nr = sub(pattern, "\\2", filename_split$afm_fiber_number))

persistence.length.bcf <- cbind(persistence.length.bcf, filename_split, filename_split_2, filename_split_3) %>%
  select(-c(drops_nr, afm_fiber_number, segment))

persistence.length.bcf$segment_nr <- segment_number

persistence.length.bcf.summary <- persistence.length.bcf %>%
  group_by(fraction, ripening_stage) %>%
  summarise(mean_bcf_pl_nm = mean(bcf_pl_nm),
            sd_bcf_pl_nm = sd(bcf_pl_nm),
            median_bcf_pl_nm = median(bcf_pl_nm, na.rm = TRUE),
            Q1_bcf_pl_nm = quantile(bcf_pl_nm, 0.25, na.rm = TRUE),
            Q3_bcf_pl_nm = quantile(bcf_pl_nm, 0.75, na.rm = TRUE),
            min_bcf_pl_nm = min(bcf_pl_nm),
            max_bcf_pl_nm = max(bcf_pl_nm),
            n_segments = segment_number,
            n_fibers = round(n()/segment_number, 0),
            n_measurements = n())

# Save results to an Excel file
wb <- createWorkbook()

addWorksheet(wb, "data")
writeData(wb, "data", persistence.length.bcf)

addWorksheet(wb, "summary")
writeData(wb, "summary", persistence.length.bcf.summary)

saveWorkbook(wb, paste0("./path/to/save/results/persistence_length_bcf_", segment_number, "_segment_statistics.xlsx"), overwrite = TRUE)
}

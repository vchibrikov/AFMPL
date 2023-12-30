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

pacman::p_load('dplyr', 'tidyr', 'gapminder',
               'ggplot2',  'ggalt',
               'forcats', 'R.utils', 'png',
               'grid', 'ggpubr', 'scales',
               'bbplot')

pixel.scale <- ________
segment.number <- ________

#### height data ####

data.height <- read.csv(file = "________", header = TRUE)
data.height %>%
  group_by(image_filename) %>%
  summarise(mean = mean(data_values),
            sd = sd(data_values)) %>%
  ungroup() -> data.height

data.height.mean <- mean(data.height$mean)
data.height.sd <- mean(data.height$sd)
data.height.mean.sd <- as.data.frame(cbind(data.height.mean, data.height.sd))

rm(data.height, data.height.mean, data.height.sd)

#### contour length data ####

data.contour.length <- read.csv(file = "________", header = TRUE)

data.contour.length %>%
  summarise(mean = mean(contour_length) * pixel.scale,
            sd = sd(contour_length) * pixel.scale) %>%
  ungroup() -> data.contour.length.mean.sd

rm(data.contour.length)

#### shortest distance data ####

data.shortest.distance <- read.csv(file = "________", header = TRUE)

data.shortest.distance %>%
  summarise(mean = mean(shortest_distance) * pixel.scale,
            sd = sd(shortest_distance) * pixel.scale) %>%
  ungroup() -> data.shortest.distance.mean.sd

rm(data.shortest.distance)

#### angle data ####

data.angle <- read.csv(file = "________", header = TRUE)
data.angle %>%
  mutate(path_angle_degrees = str_replace(path_angle_degrees, "180", "0")) %>%
  mutate(path_angle_degrees = as.numeric(path_angle_degrees)) %>%
  group_by(image_filename) %>%
  summarise(mean = mean(path_angle_degrees),
            sd = sd(path_angle_degrees)) %>%
  ungroup() -> data.angle

data.angle.mean <- mean(data.angle$mean)
data.angle.sd <- mean(data.angle$sd)
data.angle.mean.sd <- as.data.frame(cbind(data.angle.mean, data.angle.sd))

rm(data.angle, data.angle.mean, data.angle.sd)

#### persistence length - mean square end-to-end distance ####

data.path.coordinates <- read.csv(file = "________________", header = TRUE)

data.path.coordinates <- data.path.coordinates %>%
  group_by(image_filename) %>%
  mutate(segment_index = rep(1:(n() %/% ((n() - 1)/segment.number) ), each = n()/segment.number)[1:n()]) %>%
  na.omit() %>%
  mutate(image_filename = str_c(image_filename, '-', segment_index)) %>%
  select(image_filename, x, y) %>%
  ungroup()

persistence.length.msed <- data.path.coordinates %>%
  group_by(image_filename) %>%
  mutate(contour.length.nm = n() * pixel.scale) %>%
  select(image_filename, contour.length.nm) %>%
  ungroup()

persistence.length.msed <- persistence.length.msed %>%
  group_by(image_filename) %>%
  unique() %>%
  ungroup()

shortest.distance <- data.path.coordinates %>%
  group_by(image_filename) %>%
  filter(row_number() == 1 | row_number() == n())

odd_rows <- shortest.distance %>%
  filter(row_number() %% 2 == 1)
colnames(odd_rows) <- c('image_filename', 'x_start', 'y_start')

even_rows <- shortest.distance %>%
  filter(row_number() %% 2 == 0)
colnames(even_rows) <- c('image_filename', 'x_end', 'y_end')

persistence.length.msed$shortest.distance.nm <- sqrt(((even_rows$x_end - odd_rows$x_start)^2) + ((even_rows$y_end - odd_rows$y_start)^2)) * pixel.scale

pattern <- "(.*?)-(.*)"
persistence.length.msed$image_filename <- tibble(image_filename = sub(pattern, "\\1", persistence.length.msed$image_filename))

rm(even_rows, odd_rows, midpoind.shortest.distance, data.path.coordinates, shortest.distance, pattern)

# Function to solve the equation for a single row
solve_equation <- function(row) {
  shortest.distance <- row$shortest.distance^2
  contour.length.nm <- row$contour.length.nm
  
# Define the equation of persistence length by MSED
equation <- function(lambda) {
  4 * lambda * (contour.length.nm - 2 * lambda * (1 - exp(-contour.length.nm / (2 * lambda)))) - shortest.distance
}
  
# Solve the equation
result <- uniroot(equation, interval = c(0, 1000))

return(data.frame(lambda = result$root))
}

# Apply the function to each row
persistence.length.msed$persistence.length.msed.nm <- persistence.length.msed %>%
  rowwise() %>%
  do(solve_equation(.)) %>%
  as.data.frame()

rm(solve_equation)

persistence.length.msed <- as.data.frame(persistence.length.msed)
persistence.length.msed$persistence.length.msed.nm <- unlist(persistence.length.msed$persistence.length.msed.nm)

persistence.length.msed <- persistence.length.msed %>%
  group_by(image_filename) %>%
  summarise(mean = mean(persistence.length.msed.nm),
            sd = sd(persistence.length.msed.nm))

msed <- persistence.length.msed %>%
  summarise(mean = mean(mean),
            sd = mean(sd))
msed$method <- "MSED"


#### persistence length - bond correlation function ####

data.angle <- read.csv(file = "________", header = TRUE)
data.angle %>%
  mutate(path_angle_degrees = str_replace(path_angle_degrees, "180", "0")) %>%
  mutate(path_angle_degrees = as.numeric(path_angle_degrees)) -> data.angle

data.path.coordinates <- read.csv(file = "________", header = TRUE)
data.path.coordinates <- data.path.coordinates %>%
  group_by(image_filename) %>%
  filter(row_number() != 1 & row_number() != n()) %>%
  as.data.frame()

data.path.angle <- cbind(data.path.coordinates, data.angle)
rm(data.path.coordinates, data.angle)
colnames(data.path.angle) <- c('image_filename', 'x', 'y', 'remove', 'path_angle_degrees')
  
data.path.angle <- data.path.angle %>%
  select(image_filename, x, y, path_angle_degrees)

data.path.angle <- data.path.angle %>%
  group_by(image_filename) %>%
  mutate(segment_index = rep(1:(n() %/% ((n() - 1)/segment.number) ), each = n()/segment.number)[1:n()]) %>%
  na.omit() %>%
  mutate(image_filename = str_c(image_filename, '-', segment_index)) %>%
  select(image_filename, x, y, path_angle_degrees) %>%
  ungroup()

data.path.angle %>%
  group_by(image_filename) %>%
  mutate(mean = mean(path_angle_degrees)) %>%
  mutate(sd = sd(path_angle_degrees)) %>%
  mutate(cos.angle = cos(as.numeric(mean) * pi/180)) %>%
  select(image_filename, x, y, cos.angle) %>%
  ungroup() %>%
  as.data.frame() -> data.path.angle

data.path.angle <- data.path.angle %>%
  group_by(image_filename) %>%
  mutate(contour.length = n() * pixel.scale) %>%
  select(image_filename, cos.angle, contour.length) %>%
  ungroup()

data.path.angle <- data.path.angle %>%
  group_by(image_filename) %>%
  unique() %>%
  ungroup()

pattern <- "(.*?)-(.*)"
data.path.angle$image_filename <- tibble(image_filename = sub(pattern, "\\1", data.path.angle$image_filename))

data.path.angle$persistence.length.bcf <- as.numeric(-(data.path.angle$contour.length / (2 * log(data.path.angle$cos.angle))))
data.path.angle <- data.path.angle %>% filter(!is.infinite(persistence.length.bcf))

persistence.length.bcf <- data.path.angle %>%
  group_by(image_filename) %>%
  summarise(mean = mean(persistence.length.bcf),
            sd = sd(persistence.length.bcf))

bcf <- persistence.length.bcf %>%
  summarise(mean = mean(na.omit(mean)),
            sd = sd(na.omit(sd)))
bcf$method <- "BCF"

rm(data.path.angle, pattern)

#### persistence length - mean-squared midpoint displacement ####

data.path.coordinates <- read.csv(file = "________", header = TRUE)

data.path.coordinates <- data.path.coordinates %>%
  group_by(image_filename) %>%
  mutate(segment_index = rep(1:(n() %/% ((n() - 1)/segment.number) ), each = n()/segment.number)[1:n()]) %>%
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
         persistence.length.msmd$shortest.distance.midpoint.coordinate.y)^2)^0.5) * pixel.scale

persistence.length.msmd <- persistence.length.msmd %>%
  select(image_filename, mean.squared.midpoint.displacement.nm)

contour.length.nm <- data.path.coordinates %>%
  group_by(image_filename) %>%
  mutate(contour.length.nm = n() * pixel.scale) %>%
  select(image_filename, contour.length.nm) %>%
  ungroup()

contour.length.nm <- contour.length.nm %>%
  group_by(image_filename) %>%
  unique() %>%
  ungroup()

persistence.length.msmd <- merge(persistence.length.msmd, contour.length.nm, by = 'image_filename', all = TRUE)

pattern <- "(.*?)-(.*)"
persistence.length.msmd$image_filename <- tibble(image_filename = sub(pattern, "\\1", persistence.length.msmd$image_filename))

rm(contour.length.nm, data.path.coordinates, pattern)

persistence.length.msmd$persistence.length.msmd.nm <- (persistence.length.msmd$contour.length.nm^3) / (48 * (persistence.length.msmd$mean.squared.midpoint.displacement.nm)^2)

persistence.length.msmd <- persistence.length.msmd %>% filter(!is.infinite(persistence.length.msmd.nm))

persistence.length.msmd <- persistence.length.msmd %>%
  group_by(image_filename) %>%
  summarise(mean = mean(persistence.length.msmd.nm),
            sd = sd(persistence.length.msmd.nm))

msmd <- persistence.length.msmd %>%
  summarise(mean = mean(na.omit(mean)),
            sd = sd(na.omit(sd)))
msmd$method <- "MSMD"


#### merge data ####

persistence.length <- rbind(msed, bcf, msmd)
persistence.length$segment.number <- segment.number
rm(pixel.scale, segment.number, msed, bcf, msmd)

















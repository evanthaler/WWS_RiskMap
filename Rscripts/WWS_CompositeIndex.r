rm(list=ls())
library(COINr);library(sf);library(terra);library(dplyr);library(tidyr)

######################
##### USER INPUTS#####
######################
rdsout<-FALSE
ucode_column <- 'COMID'
flowlines <- TRUE
test_sensitivity <-FALSE
test_loo <- TRUE
infile = "~/Documents/Projects/OSU/WWSRiskMapping/datasets/CompositeIndexInput/FlowlinesStreamCatVars_landslides_IDF_WHP_peakFlows.gpkg"
outgpkg <- "~/Documents/Projects/OSU/WWSRiskMapping/CompositeIndexOutput"
weights <- c(1,1,1,1,1) #Watershed, Wildfire Biological, WWFI (self)


rescale_safe <- function(x) {
  max_val <- max(x, na.rm = TRUE)
  if (is.infinite(max_val) || max_val == 0) return(x)
  return(x / max_val * 100)
}
######################
#Part 1 Load and subset datatsets
########
gdf <- st_read(infile)

if(rdsout ==TRUE){
  saveRDS(gdf, sub("\\gpkg$", ".rds", posfile))

}
# Drop geometry for COINr input
df<- st_drop_geometry(gdf)


# Assign uCode if not already present
df$uCode <- as.character(df[[ucode_column]])

###The code wants to know if we're using the flowline-level data or data aggregated to some polygon-level
##indicators
#hydrologic: IDF, Q peak, BFI
#watershed:
#DOM: vegetation, SOM
if (flowlines ==TRUE){
  indicators <- c('Precip_1hr_100yr',
                  "bfiws",
                  "MaximumPeakFlow", 
                  
                  "pct_wetland",
                  "rckdepws",
                  "permws",
                  'LandslideSus',
                  
                  'ConditionalFlameLength',
                  'BurnPotential',
                  'omws') 

} else if (flowlines == FALSE){
  indicators <- c( 'median_IDF_mean',"median_bfiws","median_MaxPeakFlow",
                   "median_pctwetland","median_al_ss","median_runoffws","median_rckdepcat","median_permcat",'median_landslidepotential',
                   'median_conditionalflamelength','median_pctburnmedian','median_pcthighsevmedian',
                   'median_omws')}

longNames <-c("IDF",
              "Baseflow index",
              "Maximum Peak Flow",
              
              "Percent wetland",
              "Soil thickness",
              "Soil permeability",
              "Landslide potential",
              
              'Conditional Flame Length',
              "Potential burned area",
              
              "Soil organic matter"
)


parents <- c("Hydrologic",
             "Hydrologic",
             "Hydrologic",
             
             "Watershed",
             "Watershed",
             "Watershed",
             "Watershed",
             
             "Wildfire",
             "Wildfire",
             
             "DOC")
#For direction: 1 = increase in vulnerability, -1 = decrease in vulnerability
directions <- c(1,
                1,
                1,

                1,
                -1,
                -1,
                1,
                1,

                1,

                1)

#Level 1 weight
lev1_wts = rep(1,length(indicators))
# Clean dataset
df <- df[, c(indicators, "uCode")]

#"Burn area trend","High severity burn trend", "Conditional Flame Length"
# Build iMeta...
iMeta_base <- data.frame(
  iCode = indicators,
  iName = longNames,
  Level = 1,
  Parent = parents,
  Direction = directions,
  Weight = lev1_wts,
  Type = "Indicator"
)
#Parents: Hydrologic, DOC, Catchment character
# Customize temp direction for each
iMeta <- iMeta_base


# Add levels 2 and 3
iMeta_L23 <- data.frame(
  iCode = c("Hydrologic", "Watershed","Wildfire", "DOC","WWVI"),
  iName = c("Hydrologic Index","Catchment charactertics Index","Wildfire Index","DOC Index","Wildfire-Water Vulnerability Index"),
  Direction = c(1,1,1,1,1),
  Level = c(2,2,2,2,3),
  Weight = weights,
  Type = "Aggregate",
  Parent = c("WWVI", "WWVI","WWVI","WWVI", NA)
)
iMeta <- rbind(iMeta, iMeta_L23)




df <- df %>%
  group_by(uCode) %>%
  summarise(across(all_of(indicators), ~mean(.x, na.rm = TRUE)), .groups = "drop")



###########
#Part 2: Build COINs
# COIN for positive-direction areas
coin <- new_coin(df, iMeta)
coin <- qTreat(coin, dset = "Raw", winmax = 5)
coin <- Normalise(coin, dset = "Treated",
                      global_specs = list(f_n = "n_minmax"), f_n_para = list(l_u = c(1, 100)))

# coin <- Normalise(
#   coin,
#   dset = "Treated",
#   global_specs = list(f_n = "n_rank")
# )
#coin_pos <- qNormalise(coin_pos,dset="Treated")
coin <- Aggregate(coin, dset = "Normalised", f_ag = "a_amean") #,f_ag_para = list(p=1)
agg <- get_results(coin, dset = "Aggregated", tab_type = "Aggs")

# Add objectid if not present
agg$objectid <- as.numeric(agg$uCode)


# Drop geometry
geom <- st_geometry(gdf)


# # Make sure join key exists and is character
# Ensure matching types
gdf[[ucode_column]] <- as.character(gdf[[ucode_column]])
agg$uCode <- as.character(agg$uCode)



# Perform join directly on sf object
gdf_final <- left_join(gdf, agg, by = setNames("uCode", ucode_column))




gdf_final$DOC <- rescale_safe(gdf_final$DOC)
gdf_final$Hydrologic <- rescale_safe(gdf_final$Hydrologic)
gdf_final$Wildfire <- rescale_safe(gdf_final$Wildfire)
gdf_final$Watershed <- rescale_safe(gdf_final$Watershed)
gdf_final$WWVI <- rescale_safe(gdf_final$WWVI)
# Export
st_write(gdf_final,
         dsn = outgpkg,
         layer = "WWVI",
         driver = "GPKG", delete_layer = TRUE)

#
# if (test_sensitivity==TRUE){
#   #####################
#   #Sensitivity Analysis
#   #####################
#   # First we'll see how winsorization specifications impacts the index
#   l_winmax <- list(Address = "$Log$Treat$global_specs$f1_para$winmax",
#                    Distribution = 1:5,
#                    Type = "discrete")
#   #check impact of normalization method
#   norm_alts <- list(
#     list(f_n = "n_minmax", f_n_para = list(c(1,100))),
#     list(f_n = "n_zscore", f_n_para = list(c(10,2)))
#   )
#
#   # now put this in a list
#   l_norm <- list(Address = "$Log$Normalise$global_specs",
#                  Distribution = norm_alts,
#                  Type = "discrete")
#
#   #Now we'll play with weights by adding some noise to our inital weight sets
#   w_nom <- coin_pos$Meta$Weights$Original
#   noise_specs = data.frame(Level=c(2),NoiseFactor=c(0.25))
#   noisy_wts <- get_noisy_weights(w = w_nom,noise_specs=noise_specs,Nrep=100)
#
#   l_weights <- list(Address = "$Log$Aggregate$w",
#                     Distribution = noisy_wts,
#                     Type = "discrete")
#
#   ##Finally, we'll look at different aggregation methods
#   l_agg <- list(Address = "$Log$Aggregate$f_ag",
#                 Distribution = c("a_amean", "a_hmean"),
#                 Type = "discrete")
#
#   ##Now we'll combine them all into the SA_spects object for the get_sensitivity() function
#   SA_specs <- list(
#     Winmax = l_winmax,
#     Normalisation = l_norm,
#     Weights = l_weights,
#     Aggregation = l_agg
#   )
#
#   SA_res <- get_sensitivity(coin_pos, SA_specs = SA_specs, N = 10, SA_type = "UA",
#                             dset = "Aggregated", iCode = "Watershed")
#
#   if (test_loo==TRUE){
#   }
#   ####Here can use the leave-one-out protocol to test the influence of individual indicators on the index
#   # Loop through each Level 1 indicator and run remove_elements()
#   l_res_list <- lapply(indicators, function(code) {
#     message("Testing removal of: ", code)
#     remove_elements(coin_pos, Level = 1, dset = "Aggregated", iCode = code)
#   })
#
#   # Name the list entries by indicator code
#   names(l_res_list) <- indicators
# }
#





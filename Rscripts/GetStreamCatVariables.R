rm(list=ls())
# install the most recent approved version from CRAN
#install.packages("StreamCatTools")
# load the most recent approved version from CRAN
library(StreamCatTools)
library(remotes)
# install_github("USEPA/StreamCatTools", build_vignettes=TRUE)
# vignette("Introduction", "StreamCatTools")
# vignette("Applications", "StreamCatTools")
comid_df <- read.csv("~/Documents/Projects/OSU/EPARiskMapping/datasets/IndexVariablesDatasets/WWF_COMIDs.csv")
comid_list <- as.character(comid_df$COMID)

df <- sc_get_data(metric='om',aoi='cat,ws', comid=comid_list) #perm,bfi,iwi,rckdep,runoff,pcthbwet2019,pctwdwet2019,
write.csv(df,"~/Documents/Projects/OSU/EPARiskMapping/datasets/IndexVariablesDatasets/WWF_COMIDs_soilorganicmatter.csv")

#params <-sc_get_params(param='metric_names')

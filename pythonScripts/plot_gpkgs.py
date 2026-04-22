import matplotlib.pyplot as plt
import geopandas as gpd
import matplotlib.patches as mpatches
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib as mpl
import os



def plotgpkg(wtshdfile,wtshd_boundsfile,states_file,outprefix,plotting_crs,col_list,outpath,core_areasfile=None,plot_ssa_area=False):
    plt.rcParams.update({'font.size': 10})
    os.makedirs(outpath,exist_ok=True)
    # Load data
    wtshd = gpd.read_file(wtshdfile)
    wtshd_bounds = gpd.read_file(wtshd_boundsfile)
    states = gpd.read_file(states_file)
    wtshd = wtshd.to_crs(plotting_crs)
    wtshd_bounds = wtshd_bounds.to_crs(plotting_crs)
    if plot_ssa_area:
        core_areas = gpd.read_file(core_areasfile)
        core_areas = core_areas.to_crs(plotting_crs)
    states = states.to_crs(wtshd.crs)


    for c in col_list:
        col_to_plot = c 
        minx, miny, maxx, maxy = wtshd.total_bounds

        fig, ax = plt.subplots(figsize=(5,5))
        #wtshd[col_to_plot] = wtshd[col_to_plot] / wtshd[col_to_plot].max()
        # Get column data and colormap
        cmap = plt.cm.plasma
        #norm = mpl.colors.Normalize(vmin=0, vmax=100)
        norm = mpl.colors.PowerNorm(gamma=1, vmin=0, vmax=100)
        # Plot the polygons manually with colormap
        wtshd_bounds.plot(ax=ax, color='lightblue', edgecolor='none', linewidth=0.5, alpha=0.3, zorder=0,vmin=0,vmax=100)
        wtshd.plot(ax=ax, column=col_to_plot, cmap=cmap, edgecolor=None, linewidth=0.5, zorder=3)
        
        if plot_ssa_area:
            core_areas.plot(ax=ax, color='none', edgecolor='blue', linewidth=0.5, alpha=1, zorder=3)
        # Overlay state boundaries
        states.plot(ax=ax, color='none', edgecolor='black', linewidth=0.5, zorder=4)

        # Match extent with padding
        padding = 0.05
        ax.set_xlim(minx - padding, maxx + padding)
        ax.set_ylim(miny - padding, maxy + padding)

        # Create colorbar axis with same height
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        sm = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm._A = []  # required for older matplotlib versions
        cbar = plt.colorbar(sm, cax=cax)
        cbar.ax.tick_params(labelsize=8)
        cbar.set_label(col_to_plot, rotation=270, labelpad=15)
        
        #plt.title(f'{col_to_plot}')
        plt.savefig(f'{outpath}/{outprefix}_{col_to_plot}.jpg',dpi=800,bbox_inches='tight')
        plt.close()


plotgpkg(
    wtshdfile = '/Users/evanthaler/Documents/Projects/OSU/WWSRiskMapping/CompositeIndexOutput/WWVI_EqualWeighting.gpkg',
    wtshd_boundsfile = '/Users/evanthaler/Documents/Projects/OSU/WWSRiskMapping/CompositeIndexOutput/WWVI_EqualWeighting.gpkg',
    states_file = '/Users/evanthaler/Documents/Projects/OSU/StateShapefiles/tl_2023_us_state/tl_2023_us_state.shp',
    outprefix = 'HUC12s',
    plotting_crs = 'epsg:4326',
    col_list = ['Watershed','Wildfire','WWVI','Hydrologic','DOC'],
    outpath = '/Users/evanthaler/Documents/GitHub/WWS_RiskMap/figs',
    core_areasfile="/Users/evanthaler/Documents/Projects/OSU/WWSRiskMapping/datasets/surface-water-sources/PNW/pnw-dwsa-with-intakes.gpkg",
    plot_ssa_area=False)


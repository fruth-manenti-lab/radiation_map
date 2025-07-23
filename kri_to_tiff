import pandas as pd
import numpy as np
import rasterio
from rasterio.transform import from_origin

src_csv = "1_Krig_activity_Grid_Map.kri"    # path to the .kri file
dst_tif = "1_Krig_activity_Grid_Map.tif"    # output GeoTIFF

# 1. Read the CSV‑style grid
df = pd.read_csv(src_csv,
                 names=["x","y","activity","sd"],   # header already present
                 skiprows=1)                        # skip the header line

# 2. Build sorted coordinate vectors
x_vals = np.sort(df['x'].unique())
y_vals = np.sort(df['y'].unique())

dx = np.diff(x_vals).mean()        # 10 m
dy = np.diff(y_vals).mean()        # 10 m

# 3. Pivot to a 2‑D array (north‑down order expected by raster formats)
grid = (df
        .pivot(index='y', columns='x', values='activity')
        .sort_index(ascending=False)                # make first row = northern edge
        .values.astype(np.float32))

# 4. Define geotransform (upper‑left cell corner)
west  = x_vals.min() - dx/2        # X of left edge
north = y_vals.max() + dy/2        # Y of top edge
transform = from_origin(west, north, dx, dy)        # dx positive, dy positive

# 5. Write GeoTIFF
with rasterio.open(
        dst_tif, "w",
        driver="GTiff",
        height=grid.shape[0],
        width=grid.shape[1],
        count=1,
        dtype=grid.dtype,
        crs="EPSG:3308",
        transform=transform) as dst:
    dst.write(grid, 1)

print("Saved:", dst_tif)

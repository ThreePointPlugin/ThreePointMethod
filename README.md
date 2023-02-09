<b>ThreePointMethod Plugin</b>


<p>The plugin calculates a plane's strike, dip and dip direction using the three-point vector method. 
This plugin was created as a part of the engineering thesis at AGH University of Science and Technology in Krakow.</p>

In the <i>Input File</i>* section, insert a shapefile with three points that belong to one surface but do not lay on a straight line. 
The points must be one after the other. 
The number of threes is not limited.

In the <i> Input DEM</i>* section, insert a Digital Terrain Model covering the area of the indicated triples. 
The file should be a raster in a TIFF format and have a .tif extension. 

In the <i>Output File</i> section, select the location for the point SHP with the output data. 

<img width="396" alt="image" src="https://user-images.githubusercontent.com/79970081/215275989-19c5e781-1fa2-47e2-a34f-184eeb83f0c3.png">



*<i>Both Input File and Input DEM</i> have to use a projected coordinate system, such as UTM.

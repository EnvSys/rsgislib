/*
 *  RSGISLabelPixelsUsingClusters.h
 *  RSGIS_LIB
 *
 *  Created by Pete Bunting on 19/02/2012.
 *  Copyright 2012 RSGISLib.
 * 
 *  RSGISLib is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  RSGISLib is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with RSGISLib.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

#ifndef RSGISLabelPixelsUsingClusters_H
#define RSGISLabelPixelsUsingClusters_H

#include <iostream>
#include <string>
#include <cmath>

#include "common/RSGISImageException.h"

#include "img/RSGISImageCalcException.h"
#include "img/RSGISCalcImageValue.h"
#include "img/RSGISCalcImage.h"

#include "math/RSGISMatrices.h"

#include "gdal_priv.h"
#include "ogrsf_frmts.h"
#include "ogr_api.h"

// mark all exported classes/functions with DllExport to have
// them exported by Visual Studio
#undef DllExport
#ifdef _MSC_VER
    #ifdef rsgis_segmentation_EXPORTS
        #define DllExport   __declspec( dllexport )
    #else
        #define DllExport   __declspec( dllimport )
    #endif
#else
    #define DllExport
#endif

namespace rsgis{namespace segment{
    
    class DllExport RSGISLabelPixelsUsingClusters
    {
    public:
        RSGISLabelPixelsUsingClusters();
        void labelPixelsUsingClusters(GDALDataset **datasets, int numDatasets, std::string output, std::string clusterCentresFile, bool ignoreZeros, std::string imageFormat, bool useImageProj, std::string outProjStr);
        ~RSGISLabelPixelsUsingClusters();
    };
    
    class DllExport RSGISLabelPixelsUsingClustersCalcImg : public rsgis::img::RSGISCalcImageValue
    {
    public: 
        RSGISLabelPixelsUsingClustersCalcImg(int numberOutBands, rsgis::math::Matrix *clusterCentres, bool ignoreZeros);
        void calcImageValue(float *bandValues, int numBands, double *output);
        ~RSGISLabelPixelsUsingClustersCalcImg();
    private:
        rsgis::math::Matrix *clusterCentres;
        bool ignoreZeros;
    };
    
}}

#endif





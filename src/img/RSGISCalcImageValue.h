/*
 *  RSGISCalcImageValue.h
 *  RSGIS_LIB
 *
 *  Created by Pete Bunting on 23/04/2008.
 *  Copyright 2008 RSGISLib.
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

#ifndef RSGISCalcImageValue_H
#define RSGISCalcImageValue_H

#include <iostream>
#include <string>
#include "img/RSGISImageCalcException.h"

#include <geos/geom/Envelope.h>

namespace rsgis 
{
	namespace img
	{
		class RSGISCalcImageValue
			{
			public:
				RSGISCalcImageValue(int numberOutBands);
				virtual void calcImageValue(float *bandValues, int numBands, float *output) throw(RSGISImageCalcException) = 0;
				virtual void calcImageValue(float *bandValues, int numBands) throw(RSGISImageCalcException) = 0;
                virtual void calcImageValue(long *intBandValues, unsigned int numIntVals, float *floatBandValues, unsigned int numfloatVals) throw(RSGISImageCalcException) = 0;
                virtual void calcImageValue(long *intBandValues, unsigned int numIntVals, float *floatBandValues, unsigned int numfloatVals, float *output) throw(RSGISImageCalcException) = 0;
				virtual void calcImageValue(float *bandValues, int numBands, geos::geom::Envelope extent) throw(RSGISImageCalcException) = 0;
				virtual void calcImageValue(float *bandValues, int numBands, float *output, geos::geom::Envelope extent) throw(RSGISImageCalcException) = 0;
				virtual void calcImageValue(float ***dataBlock, int numBands, int winSize, float *output) throw(RSGISImageCalcException) = 0;
                /**
                 * Extent only refers to the central window.
                 */
                virtual void calcImageValue(float ***dataBlock, int numBands, int winSize, float *output, geos::geom::Envelope extent) throw(RSGISImageCalcException) = 0;
				virtual bool calcImageValueCondition(float ***dataBlock, int numBands, int winSize, float *output) throw(RSGISImageCalcException) = 0;
				virtual int getNumOutBands();
				virtual void setNumOutBands(int bands);
				virtual ~RSGISCalcImageValue();
			protected:
				int numOutBands;
			};
	}
}

#endif



/*
 *  RSGISGeometryException.h
 *  RSGIS_LIB
 *
 *  Created by Pete Bunting on 02/06/2008.
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

#ifndef RSGISGeometryException_H
#define RSGISGeometryException_H

#include "common/RSGISException.h"

// mark all exported classes/functions with DllExport to have
// them exported by Visual Studio
#ifdef _MSC_VER
    #ifdef rsgis_geom_EXPORTS
        #define DllExport   __declspec( dllexport )
    #else
        #define DllExport   __declspec( dllimport )
    #endif
#else
    #define DllExport
#endif

namespace rsgis{namespace geom{
		
    class DllExport RSGISGeometryException : public rsgis::RSGISException
        {
        public:
            RSGISGeometryException();
            RSGISGeometryException(const char* message);
            RSGISGeometryException(std::string message);
        };
}}

#endif


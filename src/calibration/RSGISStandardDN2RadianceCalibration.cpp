/*
 *  RSGISStandardDN2RadianceCalibration.cpp
 *  RSGIS_LIB
 *
 *  Created by Pete Bunting on 23/05/2011.
 *  Copyright 2011 RSGISLib. All rights reserved.
 *  This file is part of RSGISLib.
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

#include "RSGISStandardDN2RadianceCalibration.h"

namespace rsgis{namespace calib{
    
    void RSGISLandsatRadianceCalibration::calcImageValue(float *bandValues, int numBands, float *output) throw(rsgis::img::RSGISImageCalcException)
    {
        double gain = 0;
        
        if (int(bandValues[0]) == 0) // If pixels values for first band are 0 - consider image border
        {
            for(unsigned int i = 0; i < this->numOutBands; ++i)
            {
                output[i] = 0;
            }
        }
        else 
        {
            for(unsigned int i = 0; i < this->numOutBands; ++i)
            {
                if(this->radGainOff[i].band > numBands)
                {
                    throw rsgis::img::RSGISImageCalcException("Band is not within input image bands.");
                }
                gain = (this->radGainOff[i].lMax - this->radGainOff[i].lMin)/(this->radGainOff[i].qCalMax - this->radGainOff[i].qCalMin);
                output[i] = gain * (bandValues[i] - this->radGainOff[i].qCalMin) + this->radGainOff[i].lMin;
            }
        }
    }
    
    void RSGISSPOTRadianceCalibration::calcImageValue(float *bandValues, int numBands, float *output) throw(rsgis::img::RSGISImageCalcException)
    {
        for(unsigned int i = 0; i < this->numOutBands; ++i)
        {
            if(this->radGainOff[i].band > numBands)
            {
                throw rsgis::img::RSGISImageCalcException("Band is not within input image bands.");
            }
            output[i] = bandValues[i]/this->radGainOff[i].gain;
        }
    }
    
    void RSGISIkonosRadianceCalibration::calcImageValue(float *bandValues, int numBands, float *output) throw(rsgis::img::RSGISImageCalcException)
    {
        for(unsigned int i = 0; i < this->numOutBands; ++i)
        {
            if(this->radGainOff[i].band > numBands)
            {
                throw rsgis::img::RSGISImageCalcException("Band is not within input image bands.");
            }
            output[i] = (100000*bandValues[i])/(this->radGainOff[i].calCoef * this->radGainOff[i].bandwidth);
        }
    }
    
    void RSGISASTERRadianceCalibration::calcImageValue(float *bandValues, int numBands, float *output) throw(rsgis::img::RSGISImageCalcException)
    {
        for(unsigned int i = 0; i < this->numOutBands; ++i)
        {
            if(this->radGainOff[i].band > numBands)
            {
                throw rsgis::img::RSGISImageCalcException("Band is not within input image bands.");
            }
            output[i] = (bandValues[i]-1)*this->radGainOff[i].unitConCoef;
        }
    }
    
    void RSGISIRSRadianceCalibration::calcImageValue(float *bandValues, int numBands, float *output) throw(rsgis::img::RSGISImageCalcException)
    {
        double gain = 0;
        
        for(unsigned int i = 0; i < this->numOutBands; ++i)
        {
            if(this->radGainOff[i].band > numBands)
            {
                throw rsgis::img::RSGISImageCalcException("Band is not within input image bands.");
            }
            gain = (this->radGainOff[i].lMax - this->radGainOff[i].lMin)/(this->radGainOff[i].qCalMax - this->radGainOff[i].qCalMin);
            output[i] = gain * (bandValues[i] - this->radGainOff[i].qCalMin) + this->radGainOff[i].lMin;
        }
    }
    
    void RSGISQuickbird16bitRadianceCalibration::calcImageValue(float *bandValues, int numBands, float *output) throw(rsgis::img::RSGISImageCalcException)
    {
        for(unsigned int i = 0; i < this->numOutBands; ++i)
        {
            if(this->radGainOff[i].band > numBands)
            {
                throw rsgis::img::RSGISImageCalcException("Band is not within input image bands.");
            }
            output[i] = (bandValues[i] * this->radGainOff[i].calFactor)/this->radGainOff[i].bandIntegrate;
        }
    }
    
    void RSGISQuickbird8bitRadianceCalibration::calcImageValue(float *bandValues, int numBands, float *output) throw(rsgis::img::RSGISImageCalcException)
    {
        for(unsigned int i = 0; i < this->numOutBands; ++i)
        {
            if(this->radGainOff[i].band > numBands)
            {
                throw rsgis::img::RSGISImageCalcException("Band is not within input image bands.");
            }
            output[i] = (bandValues[i] * this->radGainOff[i].calFactor * this->radGainOff[i].k)/this->radGainOff[i].bandIntegrate;
        }
    }
    
    void RSGISWorldView2RadianceCalibration::calcImageValue(float *bandValues, int numBands, float *output) throw(rsgis::img::RSGISImageCalcException)
    {
        for(unsigned int i = 0; i < this->numOutBands; ++i)
        {
            if(this->radGainOff[i].band > numBands)
            {
                throw rsgis::img::RSGISImageCalcException("Band is not within input image bands.");
            }
            output[i] = (this->radGainOff[i].calFactor * bandValues[i])/this->radGainOff[i].bandIntegrate;
        }
    }
    
}}


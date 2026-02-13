caelum_sky_system verniocity.os
{
   
   
    julian_day 305.91  
 

	longitude -40
 	latitude 0 





    sun {
        ambient_multiplier 0.5 0.5 0.5
        diffuse_multiplier 3 3 3
        specular_multiplier 5 5 5
	
        auto_disable_threshold 0.05
        auto_disable true
    }



    

    sky_dome {
        haze_enabled yes
        sky_gradients_image greySky.png
        atmosphere_depth_image AtmosphereDepth.png
    }


global_fog_density_multiplier 0.0055
global_fog_colour_multiplier 1.6 1.46 1.5
	

        
    }
	
}

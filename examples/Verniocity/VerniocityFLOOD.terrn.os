caelum_sky_system VerniocityFLOOD.terrn.os
{
    // J2000
    julian_day 2000.0
    time_scale 1

    point_starfield {
        magnitude_scale 2.51189
        mag0_pixel_size 18
        min_pixel_size 4
        max_pixel_size 6
    }

    manage_ambient_light true
    minimum_ambient_light 0.6 0.6 0.65

    manage_scene_fog yes
    ground_fog_density_multiplier 0.00015

	scene_fog_density_multiplier 0.00015

    sun {
       ambient_multiplier 0.9 0.9 1.0
        diffuse_multiplier 3.8 3.8 3.2
        specular_multiplier 4 4 4

        auto_disable_threshold 0.05
        auto_disable true
    }

    moon {
        ambient_multiplier 0.2 0.2 0.2

        diffuse_multiplier 1 1 1.9
        specular_multiplier 1 1 1

        auto_disable_threshold 0.05
        auto_disable true
    }

    // Off by default
    /*
    depth_composer {
        debug_depth_render off
        haze_enabled yes
        ground_fog_enabled yes
        ground_fog_vertical_decay 1.06
        ground_fog_base_level 5
    }
	*/
    

    sky_dome {
        haze_enabled yes
        sky_gradients_image EarthClearSky2.png
        atmosphere_depth_image AtmosphereDepth.png
    }

    cloud_system
    {
        cloud_layer
        {
            height 2500
            coverage 1
        }
    }
	
}

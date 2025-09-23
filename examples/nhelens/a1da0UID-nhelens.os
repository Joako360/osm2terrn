caelum_sky_system a1da0UID-nhelens.os
{
    // J2000
    julian_day 2451545.0
    time_scale 1

    point_starfield {
        magnitude_scale 2.51189
        mag0_pixel_size 16
        min_pixel_size 4
        max_pixel_size 6
    }

    manage_ambient_light true
    minimum_ambient_light 0.05 0.05 0.1

    manage_scene_fog yes
    ground_fog_density_multiplier 0.001
	scene_fog_density_multiplier 0.00025

    sun {
        ambient_multiplier 0.4 0.5 0.5
        diffuse_multiplier 1.4 1.4 1.6
        specular_multiplier 1 1 1

        auto_disable_threshold 0.05
        auto_disable true
    }

    moon {
        ambient_multiplier 0.2 0.2 0.2
        diffuse_multiplier 1 1 .9
        specular_multiplier 1 1 1

        auto_disable_threshold 0.05
        auto_disable true
    }


    sky_dome {
        haze_enabled yes
        sky_gradients_image EarthClearSky2.png
        atmosphere_depth_image AtmosphereDepth.png
    }
/*
    cloud_system
    {
        cloud_layer low
        {
            height 2000
            coverage 0.1
        }
		cloud_layer high
        {
            height 3000
            coverage 0.6
        }
    }
*/	
}


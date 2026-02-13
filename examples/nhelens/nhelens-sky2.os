caelum_sky_system nhelens-sky2.os
{
	// .75 = 6:00
    julian_day 180.55
    time_scale 30
	longitude 119.5
    latitude -30.6

    manage_ambient_light true
    minimum_ambient_light 0.06 0.08 0.12

    manage_scene_fog yes
    //ground_fog_density_multiplier 0.0
	scene_fog_density_multiplier 10.2
    //global_fog_colour_multiplier 0.97 0.98 0.99

    sun
	{
        ambient_multiplier 0.55 0.65 0.70
        diffuse_multiplier 2.20 2.15 2.00
        specular_multiplier 1 1 1
        auto_disable_threshold 0.05
        auto_disable true
    }
	
	/*
    moon
	{
        ambient_multiplier 0.10 0.13 0.15
        diffuse_multiplier 0.24 0.22 0.20
        specular_multiplier 0.10 0.10 0.10 
        auto_disable_threshold 0.05
        auto_disable true
    }
	*/
	
    point_starfield
	{
        magnitude_scale 2.51189
        mag0_pixel_size 16
        min_pixel_size 4
        max_pixel_size 6
    }
    sky_dome
	{
        haze_enabled no
        sky_gradients_image EarthClearSky2.png
        atmosphere_depth_image AtmosphereDepth.png
    }
    cloud_system
    {
        cloud_layer
        {
            height 3000
            coverage 0.3
        }
}
}
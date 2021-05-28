# osm2terrn.py

CLI based app, you enter the name of a city, it makes a query through osmnx, processes the networks returned by it to write a .tobj, .terrn2, .odef and other terrain files and compresses it into a zip file, ready to install in the Rigs of Rods mods folder.

# Requirements

- Python 3.8 at least, I use the Anaconda suite and recommend using it if you don't have any version of Python.
- osmnx module.

# ToDo

Is preferred to use in-game objects if possible.

- [x] Road edges (~~with orientation and inclination~~)
- [x] Height map (some errors)
- [x] Ground texturer based in altitude, ~~water and green areas~~
- [ ] Road network (including bridges, with orientation and inclination)
- [ ] Railroad network
- [ ] Railway stations/terminals
- [ ] Airstrip/Airports
- [ ] Buildings (making a contour of the OSM area then extruding it to its height)

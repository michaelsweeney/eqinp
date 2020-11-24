# eqparse

Python module for modifying and running DOE-2 / eQUEST input files.

This module is a work in progress and documentation is currently limited as the API is subject to change.


### Getting Started

to get started, git clone this repository and import it into your project.

You'll also need to install the DOE-2 command line program (separately from eQUEST). For more information, visit http://www.doe2.com/ 

This package assumes that the user has installed the DOE-2 command line program has been installed in C:\DOE2.

Usage example:
>from eqinp.inp import Inp
>import eqparse # use eqparse module for loading results (github.com/michaelsweeney/eqparse)
>
>weather_file = 'TMY3/PA_Philadelphia_Internati.bin'
>
>mybldg = Inp('path_to_my_bldg.inp', weather_file)
>
>mybldg_rotated = mybldg.makeparm('rotation_90_deg', [{
>    'kind': 'object',
>    'bdlobjname': 'Building Data',
>    'paramname': 'AZIMUTH',
>    'val': 90
>}]) # makeparm provides functionality for modifying the input file
>
>mybldg_rotated.run() # runs command line prompt
>
>mybldg_rotated_results = eqparse.LoadSim(mybldg_rotated.getsimfile()) # use in tandem with eqparse for results
>print (mybldg_rotated_results.sim.beps())

## Authors

Michael Sweeney (github.com/michaelsweeney)


## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details


## Acknowledgments

Thanks to Santosh Philip and his excellent Eppy project for inspiration!

# cmb2sphere

Converts [Planck](http://sci.esa.int/planck/) temperature data into a height
profile on a sphere. Inspired by ['Cosmic sculpture: a new way to visualise the cosmic microwave background'] [1] by Clements, D. L., S. Sato, and A. Portela Fonseca.

I plan to write about how the process works, how to use the script and how to print the resulting file soon(tm). Feel free to remind me if this notice is still up.

Also forgive some bad stylistic choices, the certainly existing bugs and
anything that is wrong with the script. As often in "research" there wasn't
enough time to do it right... or maybe I was too lazy to improve it further. :p
(We really need a standardized note for this)

## Usage

Download https://irsa.ipac.caltech.edu/data/Planck/release_2/all-sky-maps/maps/component-maps/cmb/COM_CMB_IQU-commander_1024_R2.02_full.fits and place it in the "data" subdirectory.

## License

The script itself is usable under the GPLv3. Please see the *COPYING* file for
details. If there are questions in your jurisdiction, or if the GPLv3 is not
clear enough on the point, please consider the resulting mesh files under a CC0
or whatever you like. Effectively, do what you want with them, but please consider a
citation, or other kind of attribution.


  [1]: http://dx.doi.org/10.1088%2F0143-0807%2F38%2F1%2F015601 "Clements, D. L., S. Sato, and A. Portela Fonseca. 'Cosmic sculpture: a new way to visualise the cosmic microwave background.' European Journal of Physics 38.1 (2016): 015601."

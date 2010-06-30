#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import pyfits
import re
import os.path
import pyfits


if __name__ == '__main__':
  # setup some standard command-line option parsing
  #
  from optparse import OptionParser
  parser = OptionParser(usage="""%prog: [options] input_image newstar_sky_model [output_image]""");
  parser.add_option("-n","--num-sources",dest="nsrc",type="int",action="store",
                    help="Only restore the NSRC brightest sources");
  parser.add_option("-s","--scale",dest="fluxscale",metavar="FLUXSCALE[,N]",action="store",
                    help="rescale model fluxes by given factor. If N is given, rescale N brightest only.");
  parser.add_option("-b","--beamsize",dest="beamsize",type="float",action="store",
                    help="restoring beam size (0 for a delta-function.)");
  parser.add_option("-p","--psf",dest="psf",action="store",
                    help="name of PSF file to be fitted, if beam size is not specified (default psf.fits)");
  parser.add_option("-f",dest="force",action="store_true",
                    help="overwrite output image even if it already exists");
  parser.add_option("-v","--verbose",dest="verbose",type="int",action="store",
                    help="set verbosity level (0 is silent, higher numbers mean more messages)");
  parser.set_defaults(n=0,fluxscale='1',psf='psf.fits',beam=-1);

  (options,rem_args) = parser.parse_args();

  # get filenames
  if len(rem_args) == 2:
    input_image,skymodel = rem_args;
    name,ext = os.path.splitext(input_image)
    output_image = name+".restored"+ext;
  elif len(rem_args) == 3:
    input_image,skymodel,output_image = rem_args;
  else:
    parser.error("Insufficient number of arguments. Use -h for help.");

  # check for overwritten output
  if os.path.exists(output_image) and not options.force:
    print "File %s already exists, use the -f option to overwrite."%output_image;
    sys.exit(1);

  from Timba.Contrib.OMS.SkyPuss.Tools import Imaging
  from Timba.Contrib.OMS.SkyPuss import Import
  
  Imaging._verbosity.set_verbose(options.verbose);

  # read model and sort by apparent brightness
  model = Import.importNEWSTAR(skymodel);
  Imaging.dprintf(1,"Read %d sources from %s\n",len(model.sources),skymodel);
  sources = sorted(model.sources,lambda a,b:cmp(b.brightness(),a.brightness()));

  # apply counts and flux scales
  if options.nsrc:
    sources = sources[:options.nsrc];
    Imaging.dprintf(1,"Using %d brightest sources\n",len(sources));

  if options.fluxscale != '1':
    if "," in options.fluxscale:
      scale,n = options.fluxscale.split(",",1);
      scale = float(scale);
      n = int(n);
      Imaging.dprintf(1,"Flux of %d brightest sources will be scaled by %f\n",n,scale);
    else:
      scale = float(options.fluxscale);
      n = len(sources);
      Imaging.dprintf(1,"Flux of all model sources will be scaled by %f\n",n,scale);
    for src in sources[:n]:
      src.flux.rescale(0.01);

  if options.beamsize >= 0:
    gx = gy = options.beam;
    grot = 0;
  elif options.psf:
    # fit the psf
    gx,gy,grot = Imaging.fitPsf(options.psf);

  # read, restore, write
  input_hdu = pyfits.open(input_image)[0];
  Imaging.restoreSources(input_hdu,sources,gx,gy,grot);

  Imaging.dprintf(1,"Writing output file %s\n",output_image);
  input_hdu.writeto(output_image,clobber=True);


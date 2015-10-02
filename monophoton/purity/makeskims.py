import os
import sys
import subprocess
from ROOT import *
from selections import Regions, Variables, Version
gROOT.SetBatch(True)

varName = 'sieie'
var = Variables[varName]


outDir = os.path.join('/scratch5/ballen/hist/purity/',Version,varName,'Skims/tmp')
if not os.path.exists(outDir):
    os.makedirs(outDir)
    
skims = Regions["Monophoton"]  #["Wgamma"]
lumi = 85.2

for skim in skims:
    print 'Starting skim:', skim[0]
    inputTree = TChain('events')
    
    filesToMerge = []
    for samp in skim[-1]:
        print 'Adding files from:', samp[-1]
        
        for f in os.listdir(samp[-1]):
            print 'Adding file: ', str(f)
            inputTree.Add(samp[-1] + '/' + f)
            # break
    
        outname = os.path.join(outDir,samp[0]+'.root')
        filesToMerge.append(outname)
        print 'Saving skim to:', outname
        generator = TemplateGenerator(skim[1], var[0], outname, True)
        generator.fillSkim(inputTree, var[1], var[2], samp[1], lumi)
        generator.writeSkim()

    mergedFileName = os.path.join(outDir,skim[0]+'.root')
    subprocess.call(['hadd','-f',mergedFileName]+filesToMerge)

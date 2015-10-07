#! /bin/bash

inDir='/afs/cern.ch/work/d/dabercro/public/Winter15/flatTrees_151007'
#inDir='/afs/cern.ch/work/d/dabercro/public/Winter15/flatTreesSkimmed'
#inDir='/Users/dabercro/GradSchool/Winter15/flatTreesSkimmed'

cp $inDir/monojet_GJets_HT-* .

root -q -l -b nloGamma.cc+\(\"monojet_GJets_HT-40To100.root\",23080.0\)
root -q -l -b nloGamma.cc+\(\"monojet_GJets_HT-100To200.root\",9110.0\)
root -q -l -b nloGamma.cc+\(\"monojet_GJets_HT-200To400.root\",2281.0\)
root -q -l -b nloGamma.cc+\(\"monojet_GJets_HT-400To600.root\",273.0\)
root -q -l -b nloGamma.cc+\(\"monojet_GJets_HT-600ToInf.root\",94.5\)

hadd -f $inDir/monojet_GJets.root monojet_GJets_HT-*

#! /usr/bin/python

from StackPlotter import stackPlotter
from array import array

directory = '/afs/cern.ch/work/d/dabercro/public/Winter15/slim_unblind/'

xArray = [200,250,300,350,400,500,600,1000]

stackPlotter.SetTreeName('events')
stackPlotter.SetAllHist('htotal')
stackPlotter.SetLuminosity(2109.0)
stackPlotter.AddDataFile(directory + 'Data_NoNoise.root')
stackPlotter.ReadMCConfig('LoadMCFiles.txt',directory)
stackPlotter.SetDefaultWeight("((jet1isMonoJetId == 1 && minJetMetDPhi > 0.5) && (n_looselep == 0 && n_loosepho == 0 && n_tau == 0 && minJetMetDPhi > 0.4))*mcWeight*npvWeight*ewk_w*kfactor")
stackPlotter.SetDefaultExpr("met")
stackPlotter.SetEventsPer(10.0)
stackPlotter.SetLegendLocation(stackPlotter.kUpper,stackPlotter.kRight,0.25,0.5)

stackPlotter.OnlyPNG()
stackPlotter.MakeCanvas("testMonoJet",len(xArray)-1,array('d',xArray),"MET [GeV]", "Events Per 10 GeV",True)

#! /usr/bin/python

from ROOT import TFile
from HistPlotter import histPlotter as plotter
from array import array
import cuts
import math, os

plotter.SetCanvasSize(600,700)

directory = '/afs/cern.ch/work/d/dabercro/public/Winter15/Correct_w_MJ/'

uncFile_ewk = TFile('/afs/cern.ch/user/z/zdemirag/public/forDan/atoz_ewkunc.root')
uncFile     = TFile('/afs/cern.ch/user/z/zdemirag/public/forDan/atoz_unc.root')

uncertainties = [
    uncFile_ewk.a_ewkcorr_overz_Upcommon,
    uncFile.znlo1_over_anlo1_pdfUp,
    uncFile.znlo1_over_anlo1_renScaleUp,
    uncFile.znlo1_over_anlo1_facScaleUp
]

outDir = '~/www/monoV_160210/'
#outDir = '~/public/dump/'

gammaMCFile = TFile(directory + 'merged/monojet_GJets.root')
print gammaMCFile.GetName()
zeeMCFile   = TFile(directory + 'merged/monojet_DY.root')
print zeeMCFile.GetName()
dataFile    = TFile(directory + 'monojet_Data.root')
print dataFile.GetName()

xArray = [200,250,300,350,400,500,600,1000]

plotter.SetLumiLabel('2.24')
plotter.SetIsCMSPrelim(True)
plotter.SetLegendLocation(plotter.kUpper,plotter.kRight)
plotter.SetDefaultExpr('met')
plotter.SetEventsPer(1.0)

plotter.AddTreeWeight(zeeMCFile.events,'(' + cuts.ZllMJ + ')*mcFactors*XSecWeight')
plotter.AddTreeWeight(dataFile.events,cuts.ZllMJ)
zPlots = plotter.MakeHists(len(xArray)-1,array('d',xArray))

plotter.ResetTree()
plotter.ResetWeight()

plotter.AddTreeWeight(gammaMCFile.events,'(' + cuts.gjetMJ + ')*mcFactors*XSecWeight')
plotter.AddTreeWeight(dataFile.events,cuts.gjetMJ)

gammaPlots = plotter.MakeHists(len(xArray)-1,array('d',xArray))

plotter.AddLegendEntry('MC',2)
plotter.AddLegendEntry('Data',1)

plotter.SetDataIndex(1)
plotter.SetRatioIndex(0)

ratio = plotter.MakeRatio(zPlots,gammaPlots)

for iBin in range(len(xArray)):
    if iBin == 0:
        continue
    sumw2 = math.pow(ratio[0].GetBinError(iBin),2)
    for uncert in uncertainties:
        sumw2 += math.pow(ratio[0].GetBinContent(iBin) * (uncert.GetBinContent(iBin) - 1),2)
    ##
    ratio[0].SetBinError(iBin,math.sqrt(sumw2))
##

plotter.MakeCanvas(outDir + 'Zgamma_ratio_ZllMJ_met',ratio,'|U| [GeV]','Yield Ratio (Zll/#gamma)')

plotter.SetDefaultExpr('photonPt')
gammaPlots = plotter.MakeHists(len(xArray)-1,array('d',xArray))

plotter.ResetTree()
plotter.ResetWeight()

plotter.SetDefaultExpr('dilep_pt')
plotter.AddTreeWeight(zeeMCFile.events,'(' + cuts.ZllMJ + ')*mcFactors*XSecWeight')
plotter.AddTreeWeight(dataFile.events,cuts.ZllMJ)
zPlots = plotter.MakeHists(len(xArray)-1,array('d',xArray))

ratio = plotter.MakeRatio(zPlots,gammaPlots)

for iBin in range(len(xArray)):
    if iBin == 0:
        continue
    sumw2 = math.pow(ratio[0].GetBinError(iBin),2)
    for uncert in uncertainties:
        sumw2 += math.pow(ratio[0].GetBinContent(iBin) * (uncert.GetBinContent(iBin) - 1),2)
    ##
    ratio[0].SetBinError(iBin,math.sqrt(sumw2))
##

plotter.MakeCanvas(outDir + 'Zgamma_ratio_ZllMJ_pt',ratio,'Boson p_{T} [GeV]','Yield Ratio (Zll/#gamma)')

plotter.ResetTree()
plotter.ResetWeight()

## Mono V

xArray = [250,300,350,400,500,600,1000]


plotter.AddTreeWeight(zeeMCFile.events,'(' + cuts.ZllMV + ')*mcFactors*XSecWeight')
plotter.AddTreeWeight(dataFile.events,cuts.ZllMV)
zPlots = plotter.MakeHists(len(xArray)-1,array('d',xArray))

plotter.SetDefaultExpr('met')

plotter.ResetTree()
plotter.ResetWeight()


plotter.AddTreeWeight(gammaMCFile.events,'(' + cuts.gjetMV + ')*mcFactors*XSecWeight')
plotter.AddTreeWeight(dataFile.events,cuts.gjetMV)

gammaPlots = plotter.MakeHists(len(xArray)-1,array('d',xArray))

ratio = plotter.MakeRatio(zPlots,gammaPlots)

for iBin in range(len(xArray)):
    if iBin == 0:
        continue
    sumw2 = math.pow(ratio[0].GetBinError(iBin),2)
    for uncert in uncertainties:
        sumw2 += math.pow(ratio[0].GetBinContent(iBin) * (uncert.GetBinContent(iBin+1) - 1),2)
    ##
    ratio[0].SetBinError(iBin,math.sqrt(sumw2))
##

plotter.MakeCanvas(outDir + 'Zgamma_ratio_ZllMV_met',ratio,'|U| [GeV]','Yield Ratio (Zll/#gamma)')

plotter.SetDefaultExpr('photonPt')
gammaPlots = plotter.MakeHists(len(xArray)-1,array('d',xArray))

plotter.ResetTree()
plotter.ResetWeight()

plotter.SetDefaultExpr('dilep_pt')
plotter.AddTreeWeight(zeeMCFile.events,'(' + cuts.ZllMV + ')*mcFactors*XSecWeight')
plotter.AddTreeWeight(dataFile.events,cuts.ZllMV)
zPlots = plotter.MakeHists(len(xArray)-1,array('d',xArray))

ratio = plotter.MakeRatio(zPlots,gammaPlots)

for iBin in range(len(xArray)):
    if iBin == 0:
        continue
    sumw2 = math.pow(ratio[0].GetBinError(iBin),2)
    for uncert in uncertainties:
        sumw2 += math.pow(ratio[0].GetBinContent(iBin) * (uncert.GetBinContent(iBin+1) - 1),2)
    ##
    ratio[0].SetBinError(iBin,math.sqrt(sumw2))
##

plotter.MakeCanvas(outDir + 'Zgamma_ratio_ZllMV_pt',ratio,'Boson p_{T} [GeV]','Yield Ratio (Zll/#gamma)')
